package com.sde.audit.model;

/** Lifecycle of a decision once a human gets involved. */
public enum DecisionStatus {
    /** Recommended by the engine, awaiting an agent. */
    PENDING,
    /** Agent accepted the engine's recommendation. */
    APPROVED,
    /** Agent chose a different action than recommended (feeds the feedback loop). */
    OVERRIDDEN,
    /** Agent escalated to another team/person. */
    ESCALATED
}
