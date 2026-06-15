package com.sde.audit.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

/**
 * Runtime security settings. When {@code apiKey} is blank, auth is disabled (local dev).
 * Set {@code SDE_API_KEY} in production so only callers with the header can access the API.
 */
@ConfigurationProperties(prefix = "sde")
public record SdeProperties(String apiKey) {

    public boolean authEnabled() {
        return apiKey != null && !apiKey.isBlank();
    }
}
