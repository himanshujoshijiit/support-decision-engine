# Java Service — Audit & Decision Store

Spring Boot service that is the **durable system of record**. It persists every decision
from the Python engine, serves the agent dashboard, and records what the human did
(approve / override / escalate) and why — the traceability that closes ops/finance buyers
and the feedback loop that tunes the policies.

## Run

```bash
mvn spring-boot:run
```

- Agent dashboard: http://localhost:8080/
- H2 DB console:   http://localhost:8080/h2-console  (JDBC `jdbc:h2:mem:sde`, user `sa`, no password)

Uses an in-memory H2 database, so no setup. For a pilot, point
`spring.datasource.*` in `application.properties` at Postgres.

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/decisions` | Ingest a decision (called by the Python engine) |
| GET  | `/api/decisions` | List decisions, newest first (`?status=PENDING|APPROVED|OVERRIDDEN|ESCALATED`) |
| GET  | `/api/decisions/{id}` | One decision with its full audit trail |
| POST | `/api/decisions/{id}/action` | Record an agent action |
| GET  | `/api/stats` | Dashboard summary + recent overrides (feedback loop) |

### Recording an action

```bash
# Approve the engine's recommendation
curl -X POST http://localhost:8080/api/decisions/1/action \
  -H "Content-Type: application/json" \
  -d '{"action_taken":"APPROVE","agent_id":"dana"}'

# Override it (reason is captured for policy tuning)
curl -X POST http://localhost:8080/api/decisions/1/action \
  -H "Content-Type: application/json" \
  -d '{"action_taken":"OVERRIDE","final_action":"DENY_REFUND","override_reason":"Customer abused refund policy last quarter","agent_id":"dana"}'
```

## Layout

```
src/main/java/com/sde/audit/
  AuditApplication.java          Spring Boot entry point
  model/Decision.java            decision entity (+ embedded audit trail)
  model/AgentAction.java         a human action on a decision
  model/DecisionStatus.java      PENDING / APPROVED / OVERRIDDEN / ESCALATED
  model/JsonMapConverter.java    stores the context snapshot as JSON
  repo/DecisionRepository.java   Spring Data JPA
  service/DecisionService.java   action logic + stats / feedback loop
  controller/DecisionController.java  REST API
  dto/                           request/response records
src/main/resources/
  application.properties
  static/index.html              the agent dashboard (vanilla JS, no build step)
```

Note: JSON is configured to use `snake_case` to match the Python service's payloads.
