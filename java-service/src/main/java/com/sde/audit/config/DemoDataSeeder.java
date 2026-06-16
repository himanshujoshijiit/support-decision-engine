package com.sde.audit.config;

import com.sde.audit.model.AgentAction;
import com.sde.audit.model.Decision;
import com.sde.audit.model.DecisionStatus;
import com.sde.audit.repo.DecisionRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Seeds demo decisions including auto-approved, overridden, and escalated examples
 * so the feedback loop and filter tabs are visible without manual agent actions.
 */
@Configuration
@org.springframework.boot.autoconfigure.condition.ConditionalOnProperty(
        name = "sde.demo-seed", havingValue = "true", matchIfMissing = true)
public class DemoDataSeeder {

    private static final Logger log = LoggerFactory.getLogger(DemoDataSeeder.class);

    @Bean
    CommandLineRunner seedDemoDecisions(DecisionRepository repository) {
        return args -> {
            if (repository.count() > 0) {
                return;
            }
            log.info("Seeding demo decisions for dashboard (overrides + auto-approved)...");
            List<Decision> seeded = buildDemoDecisions();
            repository.saveAll(seeded);
            log.info("Seeded {} demo decisions", seeded.size());
        };
    }

    private static List<Decision> buildDemoDecisions() {
        List<Decision> out = new ArrayList<>();

        out.add(pendingRefund(
                "T-1001", "cus_loyal_whale", "APPROVE_REFUND", 49.0, 0.9,
                "Acme Corp (Dana Reed)", 2400.0, 0, false,
                "Double charged — clean history, agent approval recommended ($49).",
                List.of("auto_approve_high_ltv_billing"), List.of("trusted"), false));

        out.add(pendingRefund(
                "T-1005", "cus_loyal_whale", "ASK_CLARIFICATION", null, 0.8,
                "Acme Corp (Dana Reed)", 2400.0, 0, false,
                "Refund requested but amount missing — ask clarifying question.",
                List.of("ask_clarification_missing_amount"), List.of("missing_info"), false));

        out.add(pending(
                "T-1003", "cus_churn_risk", "ESCALATE", 0.88,
                "Sam Rivera", 950.0, 1, 1, "past_due",
                "Open dispute + past-due — escalate immediately.",
                List.of("escalate_open_dispute"), List.of("open_dispute", "churn_risk")));

        Decision overridden = pendingRefund(
                "T-2001", "cus_repeat_refunder", "APPROVE_REFUND", 29.0, 0.72,
                "Jordan Blake", 180.0, 2, false,
                "Engine suggested approve — agent disagreed due to abuse pattern.",
                List.of("auto_approve_high_ltv_billing"), List.of("trusted"), false);
        overridden.setStatus(DecisionStatus.OVERRIDDEN);
        overridden.getActions().add(new AgentAction(
                "OVERRIDE", "DENY_REFUND", "dana",
                "Customer has a history of refund abuse — deny per ops playbook."));
        out.add(overridden);

        Decision overridden2 = pending(
                "T-2002", "cus_churn_risk", "ESCALATE", 0.91,
                "Sam Rivera", 950.0, 1, 1, "past_due",
                "Escalation recommended for dispute case.",
                List.of("escalate_open_dispute"), List.of("open_dispute"));
        overridden2.setStatus(DecisionStatus.OVERRIDDEN);
        overridden2.getActions().add(new AgentAction(
                "OVERRIDE", "PRIORITY_ROUTE", "mike",
                "Route to senior agent with save offer — dispute is recoverable."));
        out.add(overridden2);

        Decision autoApproved = pendingRefund(
                "T-3001", "cus_loyal_whale", "APPROVE_REFUND", 49.0, 0.92,
                "Acme Corp (Dana Reed)", 2400.0, 0, false,
                "Policy auto-executed — refund processed without agent queue time.",
                List.of("auto_approve_high_ltv_billing"), List.of("trusted", "auto_approved"), true);
        autoApproved.setStatus(DecisionStatus.APPROVED);
        autoApproved.getActions().add(new AgentAction(
                "AUTO_EXECUTE", "APPROVE_REFUND", "system",
                "Policy auto-executed — no human approval required."));
        out.add(autoApproved);

        Decision escalated = pending(
                "T-1004", "cus_new_trial", "ESCALATE", 0.88,
                "Priya Nair", 0.0, 0, 0, "trialing",
                "SLA breach — immediate escalation.",
                List.of("escalate_sla_breach"), List.of("sla_breach"));
        escalated.setStatus(DecisionStatus.ESCALATED);
        escalated.getActions().add(new AgentAction("ESCALATE", "ESCALATE", "agent", null));
        out.add(escalated);

        return out;
    }

    private static Decision pendingRefund(
            String ticketId, String customerId, String action, Double amount, double confidence,
            String name, double ltv, int refunds, boolean autoExecuted,
            String reason, List<String> policies, List<String> flags, boolean autoFlag) {
        Decision d = base(ticketId, customerId, action, confidence, name, ltv, refunds, 0, "active", reason, policies, flags);
        d.setAmountUsd(amount);
        d.setAutoExecuted(autoExecuted || autoFlag);
        d.setTicketSnapshot(refundTicket(ticketId, customerId, amount != null ? amount : 0));
        return d;
    }

    private static Decision pending(
            String ticketId, String customerId, String action, double confidence,
            String name, double ltv, int refunds, int disputes, String subStatus,
            String reason, List<String> policies, List<String> flags) {
        Decision d = base(ticketId, customerId, action, confidence, name, ltv, refunds, disputes, subStatus, reason, policies, flags);
        d.setTicketSnapshot(Map.of("ticket_id", ticketId, "customer_id", customerId, "refund_requested", false));
        return d;
    }

    private static Decision base(
            String ticketId, String customerId, String action, double confidence,
            String name, double ltv, int refunds, int disputes, String subStatus,
            String reason, List<String> policies, List<String> flags) {
        Decision d = new Decision();
        d.setTicketId(ticketId);
        d.setCustomerId(customerId);
        d.setRecommendedAction(action);
        d.setConfidence(confidence);
        d.setReason(reason);
        d.setPolicyMatches(new ArrayList<>(policies));
        d.setFlags(new ArrayList<>(flags));
        d.setSource("demo-seed");
        d.setStatus(DecisionStatus.PENDING);
        d.setContextSnapshot(context(name, customerId, ltv, refunds, disputes, subStatus));
        d.setAllowedActions(List.of(action, "ESCALATE", "RESPOND"));
        return d;
    }

    private static Map<String, Object> context(
            String name, String customerId, double ltv, int refunds, int disputes, String subStatus) {
        Map<String, Object> ctx = new LinkedHashMap<>();
        ctx.put("name", name);
        ctx.put("customer_id", customerId);
        ctx.put("ltv_usd", ltv);
        ctx.put("tenure_months", 8);
        ctx.put("subscription_status", subStatus);
        ctx.put("mrr_usd", 99.0);
        ctx.put("refunds_given_count", refunds);
        ctx.put("days_since_last_refund", refunds > 0 ? 21 : null);
        ctx.put("open_disputes", disputes);
        ctx.put("fraud_risk", "low");
        return ctx;
    }

    private static Map<String, Object> refundTicket(String ticketId, String customerId, double amount) {
        Map<String, Object> t = new LinkedHashMap<>();
        t.put("ticket_id", ticketId);
        t.put("customer_id", customerId);
        t.put("refund_requested", true);
        t.put("requested_refund_usd", amount);
        t.put("category", "billing");
        return t;
    }
}
