# Pilot Agreement — Skeleton (1 page)

> Not legal advice. A lightweight letter-of-intent to start a pilot fast. Have counsel
> review before signing anything binding.

---

**Between:** [Your Company] ("Provider") and [Customer] ("Customer")
**Effective date:** [date]   **Term:** 30 days from kickoff (the "Pilot")

### 1. Scope
Provider will deploy the Support Decision Engine against Customer's **[sandbox / single
tagged queue]** on **Zendesk + Stripe (read-only)**, encode Customer's refund/escalation
policies, and produce recommendations + an audit trail for support tickets.

### 2. What Provider does
- Encode Customer's policies into the engine in week 1 (the onboarding work).
- Connect read-only Zendesk + Stripe access.
- Provide the agent console and audit export.
- Support during the Pilot.

### 3. What Customer does
- Provide read-only API access and a test/sandbox queue.
- Nominate an **ops owner** for policy decisions.
- Give honest feedback; review recommendations.
- Provide a short testimonial **if** success criteria are met.

### 4. Data & security
- Read-only scopes only; no automatic refund execution during the Pilot.
- No model training on Customer data without written opt-in.
- Retention: 90 days default, deleted on request at Pilot end.
- See the [Security one-pager](SECURITY.md).

### 5. Success criteria (measured, see below)
The Pilot is "successful" if the criteria in the table below are met by day 30.

### 6. Fees
- **Pilot:** free for 30 days.
- **On success → conversion:** Starter at **$499/month** + a one-time onboarding fee
  (policy encoding). Pricing per the proposal.

### 7. Confidentiality & IP
- Mutual confidentiality for shared data and methods.
- Provider retains all IP in the engine; Customer owns its policy content and its data.

### 8. Termination
Either party may end the Pilot with 5 days' notice. On termination, Provider deletes
Customer data within 30 days on request.

---

**Signed:**

Provider: ___________________  Date: ________
Customer: ___________________  Date: ________

---

## Pilot success criteria (put these numbers in the agreement)

| Metric | Target |
|--------|--------|
| Recommendations in the "acceptable" set per ops lead | **≥ 80%** |
| Reduction in time-to-first-action on judgment tickets | **≥ 30%** |
| Audit coverage of decisions | **100%** |
| Override reasons captured on overrides | **≥ 90%** |

These map directly to what the engine measures: agreement rate and override rate on
`GET /api/stats`, and the audit trail per decision.
