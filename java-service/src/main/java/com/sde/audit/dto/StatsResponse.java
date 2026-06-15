package com.sde.audit.dto;

import java.util.List;

/**
 * Dashboard summary + the feedback-loop view: how often agents override the engine and
 * the reasons they give. A rising override rate on a given policy is the signal to tune
 * that rule.
 */
public record StatsResponse(
        long total,
        long pending,
        long approved,
        long overridden,
        long escalated,
        long autoExecuted,
        double overrideRate,
        double agreementRate,
        List<OverrideSample> recentOverrides
) {
    public record OverrideSample(
            Long decisionId,
            String ticketId,
            String recommendedAction,
            String finalAction,
            String overrideReason
    ) {
    }
}
