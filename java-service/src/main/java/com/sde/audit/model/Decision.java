package com.sde.audit.model;

import jakarta.persistence.CollectionTable;
import jakarta.persistence.Column;
import jakarta.persistence.Convert;
import jakarta.persistence.ElementCollection;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.OrderBy;
import jakarta.persistence.Table;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/** A decision recommended by the engine, plus its human-action history. */
@Entity
@Table(name = "decisions")
public class Decision {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String ticketId;
    private String customerId;
    private String recommendedAction;
    private double confidence;

    @Column(length = 2000)
    private String reason;

    /** Dollar amount for an approved refund (null otherwise). */
    private Double amountUsd;

    /** The question to ask when the action is ASK_CLARIFICATION (null otherwise). */
    @Column(length = 1000)
    private String clarifyingQuestion;

    @ElementCollection(fetch = FetchType.EAGER)
    @CollectionTable(name = "decision_policy_matches", joinColumns = @JoinColumn(name = "decision_id"))
    @Column(name = "rule_id")
    private List<String> policyMatches = new ArrayList<>();

    /** The actions policy permitted for this ticket — the trust boundary the engine enforced. */
    @ElementCollection(fetch = FetchType.EAGER)
    @CollectionTable(name = "decision_allowed_actions", joinColumns = @JoinColumn(name = "decision_id"))
    @Column(name = "action")
    private List<String> allowedActions = new ArrayList<>();

    @ElementCollection(fetch = FetchType.EAGER)
    @CollectionTable(name = "decision_flags", joinColumns = @JoinColumn(name = "decision_id"))
    @Column(name = "flag")
    private List<String> flags = new ArrayList<>();

    private String source;
    private boolean autoExecuted;

    /** True when the orchestrator overrode a model recommendation that violated policy. */
    private boolean policyClamped;

    @Convert(converter = JsonMapConverter.class)
    @Column(columnDefinition = "CLOB")
    private Map<String, Object> contextSnapshot;

    @Convert(converter = JsonMapConverter.class)
    @Column(columnDefinition = "CLOB")
    private Map<String, Object> ticketSnapshot;

    private Instant createdAt = Instant.now();

    @Enumerated(EnumType.STRING)
    private DecisionStatus status = DecisionStatus.PENDING;

    @OrderBy("createdAt ASC")
    @ElementCollection(fetch = FetchType.EAGER)
    @CollectionTable(name = "decision_actions", joinColumns = @JoinColumn(name = "decision_id"))
    private List<AgentAction> actions = new ArrayList<>();

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getTicketId() {
        return ticketId;
    }

    public void setTicketId(String ticketId) {
        this.ticketId = ticketId;
    }

    public String getCustomerId() {
        return customerId;
    }

    public void setCustomerId(String customerId) {
        this.customerId = customerId;
    }

    public String getRecommendedAction() {
        return recommendedAction;
    }

    public void setRecommendedAction(String recommendedAction) {
        this.recommendedAction = recommendedAction;
    }

    public double getConfidence() {
        return confidence;
    }

    public void setConfidence(double confidence) {
        this.confidence = confidence;
    }

    public String getReason() {
        return reason;
    }

    public void setReason(String reason) {
        this.reason = reason;
    }

    public Double getAmountUsd() {
        return amountUsd;
    }

    public void setAmountUsd(Double amountUsd) {
        this.amountUsd = amountUsd;
    }

    public String getClarifyingQuestion() {
        return clarifyingQuestion;
    }

    public void setClarifyingQuestion(String clarifyingQuestion) {
        this.clarifyingQuestion = clarifyingQuestion;
    }

    public List<String> getPolicyMatches() {
        return policyMatches;
    }

    public void setPolicyMatches(List<String> policyMatches) {
        this.policyMatches = policyMatches;
    }

    public List<String> getAllowedActions() {
        return allowedActions;
    }

    public void setAllowedActions(List<String> allowedActions) {
        this.allowedActions = allowedActions;
    }

    public List<String> getFlags() {
        return flags;
    }

    public void setFlags(List<String> flags) {
        this.flags = flags;
    }

    public String getSource() {
        return source;
    }

    public void setSource(String source) {
        this.source = source;
    }

    public boolean isAutoExecuted() {
        return autoExecuted;
    }

    public void setAutoExecuted(boolean autoExecuted) {
        this.autoExecuted = autoExecuted;
    }

    public boolean isPolicyClamped() {
        return policyClamped;
    }

    public void setPolicyClamped(boolean policyClamped) {
        this.policyClamped = policyClamped;
    }

    public Map<String, Object> getContextSnapshot() {
        return contextSnapshot;
    }

    public void setContextSnapshot(Map<String, Object> contextSnapshot) {
        this.contextSnapshot = contextSnapshot;
    }

    public Map<String, Object> getTicketSnapshot() {
        return ticketSnapshot;
    }

    public void setTicketSnapshot(Map<String, Object> ticketSnapshot) {
        this.ticketSnapshot = ticketSnapshot;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(Instant createdAt) {
        this.createdAt = createdAt;
    }

    public DecisionStatus getStatus() {
        return status;
    }

    public void setStatus(DecisionStatus status) {
        this.status = status;
    }

    public List<AgentAction> getActions() {
        return actions;
    }

    public void setActions(List<AgentAction> actions) {
        this.actions = actions;
    }
}
