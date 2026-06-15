package com.sde.audit.dto;

import java.util.List;

/**
 * Weekly policy-tuning view: which rules and actions agents override most often.
 * Rising override rates on a rule are the signal to tune that policy.
 */
public record PolicyTuningReport(
        double overrideRate,
        long totalDecisions,
        long totalOverrides,
        List<ActionOverrideStat> byRecommendedAction,
        List<RuleOverrideStat> byPolicyRule,
        List<WeeklyOverrideStat> weeklyOverrides
) {
    public record ActionOverrideStat(
            String action,
            long overrideCount,
            long decisionCount,
            double overrideRate
    ) {
    }

    public record RuleOverrideStat(
            String ruleId,
            long overrideCount,
            long decisionCount,
            double overrideRate
    ) {
    }

    public record WeeklyOverrideStat(
            String weekLabel,
            long overrideCount
    ) {
    }
}
