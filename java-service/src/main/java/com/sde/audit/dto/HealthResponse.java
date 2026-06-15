package com.sde.audit.dto;

public record HealthResponse(
        String status,
        String database,
        boolean authEnabled
) {
}
