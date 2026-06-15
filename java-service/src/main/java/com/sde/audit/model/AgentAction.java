package com.sde.audit.model;

import jakarta.persistence.Column;
import jakarta.persistence.Embeddable;

import java.time.Instant;

/**
 * A human action taken on a decision. Embedded in {@link Decision} so the full audit
 * trail travels with the decision it belongs to.
 *
 * <p>{@code actionTaken} is APPROVE / OVERRIDE / ESCALATE. When an agent OVERRIDEs the
 * engine, {@code finalAction} captures what they did instead and {@code overrideReason}
 * captures why — this is the raw material for the feedback loop / policy tuning.
 */
@Embeddable
public class AgentAction {

    private String actionTaken;
    private String finalAction;
    private String agentId;

    @Column(length = 2000)
    private String overrideReason;

    private Instant createdAt = Instant.now();

    public AgentAction() {
    }

    public AgentAction(String actionTaken, String finalAction, String agentId, String overrideReason) {
        this.actionTaken = actionTaken;
        this.finalAction = finalAction;
        this.agentId = agentId;
        this.overrideReason = overrideReason;
        this.createdAt = Instant.now();
    }

    public String getActionTaken() {
        return actionTaken;
    }

    public void setActionTaken(String actionTaken) {
        this.actionTaken = actionTaken;
    }

    public String getFinalAction() {
        return finalAction;
    }

    public void setFinalAction(String finalAction) {
        this.finalAction = finalAction;
    }

    public String getAgentId() {
        return agentId;
    }

    public void setAgentId(String agentId) {
        this.agentId = agentId;
    }

    public String getOverrideReason() {
        return overrideReason;
    }

    public void setOverrideReason(String overrideReason) {
        this.overrideReason = overrideReason;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(Instant createdAt) {
        this.createdAt = createdAt;
    }
}
