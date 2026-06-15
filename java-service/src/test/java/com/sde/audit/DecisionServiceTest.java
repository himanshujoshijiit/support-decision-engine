package com.sde.audit;

import com.sde.audit.dto.ActionRequest;
import com.sde.audit.model.Decision;
import com.sde.audit.model.DecisionStatus;
import com.sde.audit.service.DecisionService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

@SpringBootTest
class DecisionServiceTest {

    @Autowired
    private DecisionService service;

    private Decision sample(String action) {
        Decision d = new Decision();
        d.setTicketId("T-test");
        d.setCustomerId("cus_loyal_whale");
        d.setRecommendedAction(action);
        d.setConfidence(0.9);
        d.setReason("test reason");
        d.setPolicyMatches(List.of("auto_approve_high_ltv_billing"));
        d.setFlags(List.of("trusted"));
        d.setSource("heuristic");
        d.setAutoExecuted(true);
        d.setContextSnapshot(Map.of("name", "Acme", "ltv_usd", 2400));
        return d;
    }

    @Test
    void recordsDecisionAsPending() {
        Decision saved = service.record(sample("APPROVE_REFUND"));
        assertEquals(DecisionStatus.PENDING, saved.getStatus());
        assertTrue(saved.getId() != null);
    }

    @Test
    void approveUpdatesStatusAndTrail() {
        Decision saved = service.record(sample("APPROVE_REFUND"));
        Decision after = service.applyAction(saved.getId(),
                new ActionRequest("APPROVE", null, "dana", null)).orElseThrow();
        assertEquals(DecisionStatus.APPROVED, after.getStatus());
        assertEquals(1, after.getActions().size());
        assertEquals("APPROVE_REFUND", after.getActions().get(0).getFinalAction());
    }

    @Test
    void overrideCapturesReasonForFeedbackLoop() {
        Decision saved = service.record(sample("APPROVE_REFUND"));
        service.applyAction(saved.getId(),
                new ActionRequest("OVERRIDE", "DENY_REFUND", "dana", "history of abuse")).orElseThrow();
        var stats = service.stats();
        assertTrue(stats.overridden() >= 1);
        assertTrue(stats.recentOverrides().stream()
                .anyMatch(o -> "history of abuse".equals(o.overrideReason())));
    }

    @Test
    void policyTuningReportAggregatesOverrides() {
        Decision saved = service.record(sample("APPROVE_REFUND"));
        service.applyAction(saved.getId(),
                new ActionRequest("OVERRIDE", "DENY_REFUND", "dana", "too generous")).orElseThrow();
        var report = service.policyTuningReport();
        assertTrue(report.totalOverrides() >= 1);
        assertTrue(report.byRecommendedAction().stream()
                .anyMatch(s -> "APPROVE_REFUND".equals(s.action())));
    }
}
