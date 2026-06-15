package com.sde.audit;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Support Decision Engine — Audit & Decision Store.
 *
 * <p>The durable system of record. It persists every decision produced by the Python
 * judgment layer, serves the agent dashboard, and captures what the human ultimately did
 * (approve / override / escalate) plus the reason — the feedback loop that makes the
 * system fit each customer's policies over time.
 */
@SpringBootApplication
public class AuditApplication {

    public static void main(String[] args) {
        SpringApplication.run(AuditApplication.class, args);
    }
}
