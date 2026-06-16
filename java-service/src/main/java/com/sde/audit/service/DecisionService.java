package com.sde.audit.service;

import com.sde.audit.dto.ActionRequest;
import com.sde.audit.dto.PolicyTuningReport;
import com.sde.audit.dto.StatsResponse;
import com.sde.audit.model.AgentAction;
import com.sde.audit.model.Decision;
import com.sde.audit.model.DecisionStatus;
import com.sde.audit.repo.DecisionRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.time.ZoneOffset;
import java.time.temporal.IsoFields;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
public class DecisionService {

    private final DecisionRepository repository;

    public DecisionService(DecisionRepository repository) {
        this.repository = repository;
    }

    @Transactional
    public Decision record(Decision decision) {
        if (decision.getStatus() == null) {
            decision.setStatus(DecisionStatus.PENDING);
        }
        if (decision.isAutoExecuted() && shouldAutoApprove(decision)) {
            decision.setStatus(DecisionStatus.APPROVED);
            decision.getActions().add(new AgentAction(
                    "AUTO_EXECUTE",
                    decision.getRecommendedAction(),
                    "system",
                    "Policy auto-executed — no human approval required."));
        }
        return repository.save(decision);
    }

    @Transactional(readOnly = true)
    public List<Decision> list(DecisionStatus status) {
        List<Decision> decisions = status == null
                ? repository.findAllByOrderByCreatedAtDesc()
                : repository.findByStatusOrderByCreatedAtDesc(status);
        decisions.forEach(this::enrichLiveContext);
        return decisions;
    }

    @Transactional(readOnly = true)
    public Optional<Decision> get(Long id) {
        return repository.findById(id).map(d -> {
            enrichLiveContext(d);
            return d;
        });
    }

    @Transactional
    public Optional<Decision> applyAction(Long id, ActionRequest request) {
        Optional<Decision> maybe = repository.findById(id);
        if (maybe.isEmpty()) {
            return Optional.empty();
        }
        Decision decision = maybe.get();
        String action = request.actionTaken() == null ? "" : request.actionTaken().trim().toUpperCase();
        String agent = (request.agentId() == null || request.agentId().isBlank()) ? "agent" : request.agentId();

        String finalAction;
        switch (action) {
            case "APPROVE" -> {
                decision.setStatus(DecisionStatus.APPROVED);
                finalAction = decision.getRecommendedAction();
            }
            case "OVERRIDE" -> {
                decision.setStatus(DecisionStatus.OVERRIDDEN);
                finalAction = (request.finalAction() == null || request.finalAction().isBlank())
                        ? "MANUAL" : request.finalAction();
            }
            case "ESCALATE" -> {
                decision.setStatus(DecisionStatus.ESCALATED);
                finalAction = "ESCALATE";
            }
            default -> throw new IllegalArgumentException(
                    "actionTaken must be one of APPROVE, OVERRIDE, ESCALATE (got: " + action + ")");
        }

        decision.getActions().add(new AgentAction(
                action, finalAction, agent, request.overrideReason()));
        Decision saved = repository.save(decision);

        if (DecisionStatus.APPROVED.equals(saved.getStatus()) && isRefundApproval(finalAction)) {
            refreshPendingSiblings(saved);
        }
        return Optional.of(saved);
    }

    @Transactional(readOnly = true)
    public StatsResponse stats() {
        long total = repository.count();
        long pending = repository.countByStatus(DecisionStatus.PENDING);
        long approved = repository.countByStatus(DecisionStatus.APPROVED);
        long overridden = repository.countByStatus(DecisionStatus.OVERRIDDEN);
        long escalated = repository.countByStatus(DecisionStatus.ESCALATED);

        List<Decision> all = repository.findAllByOrderByCreatedAtDesc();
        long autoApproved = all.stream().filter(this::wasAutoApproved).count();

        long actioned = approved + overridden;
        double overrideRate = actioned == 0 ? 0.0 : (double) overridden / actioned;
        double agreementRate = actioned == 0 ? 0.0 : (double) approved / actioned;

        List<StatsResponse.OverrideSample> recentOverrides = all.stream()
                .filter(d -> d.getStatus() == DecisionStatus.OVERRIDDEN)
                .limit(10)
                .map(d -> {
                    AgentAction last = lastAction(d);
                    return new StatsResponse.OverrideSample(
                            d.getId(),
                            d.getTicketId(),
                            d.getRecommendedAction(),
                            last == null ? null : last.getFinalAction(),
                            last == null ? null : last.getOverrideReason());
                })
                .toList();

        return new StatsResponse(total, pending, approved, overridden, escalated,
                autoApproved, round(overrideRate), round(agreementRate), recentOverrides);
    }

    @Transactional(readOnly = true)
    public PolicyTuningReport policyTuningReport() {
        List<Decision> all = repository.findAllByOrderByCreatedAtDesc();
        long total = all.size();
        List<Decision> overridden = all.stream()
                .filter(d -> d.getStatus() == DecisionStatus.OVERRIDDEN)
                .toList();
        long overrideCount = overridden.size();
        double overrideRate = total == 0 ? 0.0 : (double) overrideCount / total;

        Map<String, long[]> byAction = new HashMap<>();
        for (Decision d : all) {
            String action = d.getRecommendedAction() == null ? "UNKNOWN" : d.getRecommendedAction();
            long[] counts = byAction.computeIfAbsent(action, k -> new long[2]);
            counts[0]++;
            if (d.getStatus() == DecisionStatus.OVERRIDDEN) {
                counts[1]++;
            }
        }

        List<PolicyTuningReport.ActionOverrideStat> actionStats = byAction.entrySet().stream()
                .map(e -> {
                    long decisions = e.getValue()[0];
                    long overrides = e.getValue()[1];
                    double rate = decisions == 0 ? 0.0 : (double) overrides / decisions;
                    return new PolicyTuningReport.ActionOverrideStat(
                            e.getKey(), overrides, decisions, round(rate));
                })
                .sorted(Comparator.comparingLong(PolicyTuningReport.ActionOverrideStat::overrideCount).reversed())
                .toList();

        Map<String, long[]> byRule = new HashMap<>();
        for (Decision d : all) {
            List<String> rules = d.getPolicyMatches();
            if (rules == null || rules.isEmpty()) {
                rules = List.of("(no rule matched)");
            }
            for (String rule : rules) {
                long[] counts = byRule.computeIfAbsent(rule, k -> new long[2]);
                counts[0]++;
                if (d.getStatus() == DecisionStatus.OVERRIDDEN) {
                    counts[1]++;
                }
            }
        }

        List<PolicyTuningReport.RuleOverrideStat> ruleStats = byRule.entrySet().stream()
                .map(e -> {
                    long decisions = e.getValue()[0];
                    long overrides = e.getValue()[1];
                    double rate = decisions == 0 ? 0.0 : (double) overrides / decisions;
                    return new PolicyTuningReport.RuleOverrideStat(
                            e.getKey(), overrides, decisions, round(rate));
                })
                .sorted(Comparator.comparingLong(PolicyTuningReport.RuleOverrideStat::overrideCount).reversed())
                .limit(15)
                .toList();

        Map<String, Long> weekly = new LinkedHashMap<>();
        Instant cutoff = Instant.now().minusSeconds(7L * 24 * 3600);
        for (Decision d : overridden) {
            Instant at = d.getCreatedAt();
            if (at == null || at.isBefore(cutoff)) {
                continue;
            }
            var week = at.atZone(ZoneOffset.UTC).get(IsoFields.WEEK_BASED_YEAR)
                    + "-W" + String.format("%02d", at.atZone(ZoneOffset.UTC).get(IsoFields.WEEK_OF_WEEK_BASED_YEAR));
            weekly.merge(week, 1L, Long::sum);
        }

        List<PolicyTuningReport.WeeklyOverrideStat> weeklyStats = weekly.entrySet().stream()
                .sorted(Map.Entry.comparingByKey())
                .map(e -> new PolicyTuningReport.WeeklyOverrideStat(e.getKey(), e.getValue()))
                .collect(Collectors.toCollection(ArrayList::new));

        return new PolicyTuningReport(
                round(overrideRate), total, overrideCount, actionStats, ruleStats, weeklyStats);
    }

    /** Merge approved refund history into pending decisions for the same customer. */
    private void enrichLiveContext(Decision decision) {
        if (decision.getContextSnapshot() == null) {
            decision.setContextSnapshot(new HashMap<>());
        }
        long approvedRefunds = repository.countByCustomerIdAndRecommendedActionAndStatus(
                decision.getCustomerId(), "APPROVE_REFUND", DecisionStatus.APPROVED);
        Map<String, Object> ctx = new HashMap<>(decision.getContextSnapshot());
        int base = toInt(ctx.get("refunds_given_count"));
        int live = base + (int) approvedRefunds;
        ctx.put("refunds_given_count", live);
        if (approvedRefunds > 0) {
            ctx.put("days_since_last_refund", 0);
        }
        decision.setContextSnapshot(ctx);
    }

    private void refreshPendingSiblings(Decision approved) {
        List<Decision> siblings = repository.findByCustomerIdAndStatusOrderByCreatedAtDesc(
                approved.getCustomerId(), DecisionStatus.PENDING);
        for (Decision sibling : siblings) {
            if (sibling.getId().equals(approved.getId())) {
                continue;
            }
            enrichLiveContext(sibling);
            if (!sibling.getFlags().contains("context_refreshed")) {
                sibling.getFlags().add("context_refreshed");
            }
            if (isRefundTicket(sibling) && toInt(sibling.getContextSnapshot().get("refunds_given_count")) > 0) {
                if (!sibling.getFlags().contains("recent_refund")) {
                    sibling.getFlags().add("recent_refund");
                }
            }
            repository.save(sibling);
        }
    }

    private static boolean shouldAutoApprove(Decision decision) {
        return "APPROVE_REFUND".equals(decision.getRecommendedAction());
    }

    private static boolean isRefundApproval(String finalAction) {
        return "APPROVE_REFUND".equals(finalAction);
    }

    private static boolean isRefundTicket(Decision decision) {
        Map<String, Object> ticket = decision.getTicketSnapshot();
        if (ticket != null && Boolean.TRUE.equals(ticket.get("refund_requested"))) {
            return true;
        }
        return "APPROVE_REFUND".equals(decision.getRecommendedAction())
                || "ASK_CLARIFICATION".equals(decision.getRecommendedAction());
    }

    private boolean wasAutoApproved(Decision d) {
        return d.getActions().stream().anyMatch(a -> "AUTO_EXECUTE".equals(a.getActionTaken()));
    }

    private static int toInt(Object value) {
        if (value instanceof Number n) {
            return n.intValue();
        }
        return 0;
    }

    private static AgentAction lastAction(Decision d) {
        List<AgentAction> actions = d.getActions();
        return actions.isEmpty() ? null : actions.get(actions.size() - 1);
    }

    private static double round(double v) {
        return Math.round(v * 100.0) / 100.0;
    }
}
