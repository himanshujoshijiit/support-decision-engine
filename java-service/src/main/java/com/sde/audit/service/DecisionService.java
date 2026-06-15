package com.sde.audit.service;

import com.sde.audit.dto.ActionRequest;
import com.sde.audit.dto.StatsResponse;
import com.sde.audit.model.AgentAction;
import com.sde.audit.model.Decision;
import com.sde.audit.model.DecisionStatus;
import com.sde.audit.repo.DecisionRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

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
        return repository.save(decision);
    }

    @Transactional(readOnly = true)
    public List<Decision> list(DecisionStatus status) {
        if (status == null) {
            return repository.findAllByOrderByCreatedAtDesc();
        }
        return repository.findByStatusOrderByCreatedAtDesc(status);
    }

    @Transactional(readOnly = true)
    public Optional<Decision> get(Long id) {
        return repository.findById(id);
    }

    /**
     * Apply a human action to a decision and update its status. Records the full action
     * (including the override reason) on the decision's audit trail.
     */
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
        return Optional.of(repository.save(decision));
    }

    @Transactional(readOnly = true)
    public StatsResponse stats() {
        long total = repository.count();
        long pending = repository.countByStatus(DecisionStatus.PENDING);
        long approved = repository.countByStatus(DecisionStatus.APPROVED);
        long overridden = repository.countByStatus(DecisionStatus.OVERRIDDEN);
        long escalated = repository.countByStatus(DecisionStatus.ESCALATED);

        List<Decision> all = repository.findAllByOrderByCreatedAtDesc();
        long autoExecuted = all.stream().filter(Decision::isAutoExecuted).count();

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
                autoExecuted, round(overrideRate), round(agreementRate), recentOverrides);
    }

    private static AgentAction lastAction(Decision d) {
        List<AgentAction> actions = d.getActions();
        return actions.isEmpty() ? null : actions.get(actions.size() - 1);
    }

    private static double round(double v) {
        return Math.round(v * 100.0) / 100.0;
    }
}
