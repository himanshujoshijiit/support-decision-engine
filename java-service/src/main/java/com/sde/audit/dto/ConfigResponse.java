package com.sde.audit.dto;

public record ConfigResponse(
        boolean authRequired,
        String version
) {
}
