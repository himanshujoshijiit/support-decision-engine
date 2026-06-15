package com.sde.audit.dto;

/**
 * An agent action on a decision.
 *
 * @param actionTaken    APPROVE | OVERRIDE | ESCALATE
 * @param finalAction    when overriding, the action the agent chose instead
 * @param agentId        who took the action (optional; defaults to "agent")
 * @param overrideReason why they overrode (required for OVERRIDE — powers the feedback loop)
 */
public record ActionRequest(
        String actionTaken,
        String finalAction,
        String agentId,
        String overrideReason
) {
}
