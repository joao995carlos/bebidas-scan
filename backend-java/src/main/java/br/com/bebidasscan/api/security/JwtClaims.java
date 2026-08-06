package br.com.bebidasscan.api.security;

import java.time.Instant;

public record JwtClaims(
        Integer userId,
        String email,
        Instant expiresAt
) {
}
