package br.com.bebidasscan.api.security;

import br.com.bebidasscan.api.config.BebidasScanProperties;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import jakarta.annotation.PostConstruct;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;
import java.util.Optional;
import javax.crypto.SecretKey;
import org.springframework.stereotype.Service;

@Service
public class JwtService {

    private final BebidasScanProperties properties;
    private SecretKey secretKey;

    public JwtService(BebidasScanProperties properties) {
        this.properties = properties;
    }

    @PostConstruct
    void validateConfiguration() {
        if (properties.jwtSecretKey() == null || properties.jwtSecretKey().length() < 32) {
            throw new IllegalStateException("JWT_SECRET_KEY precisa ter pelo menos 32 caracteres");
        }
        if (!"HS256".equals(properties.jwtAlgorithm())
                && !"HS384".equals(properties.jwtAlgorithm())
                && !"HS512".equals(properties.jwtAlgorithm())) {
            throw new IllegalStateException("JWT_ALGORITHM invalido");
        }
        if (properties.accessTokenExpireMinutes() <= 0) {
            throw new IllegalStateException("ACCESS_TOKEN_EXPIRE_MINUTES precisa ser maior que zero");
        }
        if (properties.refreshTokenExpireDays() <= 0) {
            throw new IllegalStateException("REFRESH_TOKEN_EXPIRE_DAYS precisa ser maior que zero");
        }
        this.secretKey = Keys.hmacShaKeyFor(properties.jwtSecretKey().getBytes(StandardCharsets.UTF_8));
    }

    public Optional<JwtClaims> verifyAccessToken(String token) {
        try {
            Claims claims = Jwts.parser()
                    .verifyWith(secretKey)
                    .build()
                    .parseSignedClaims(token)
                    .getPayload();

            if (!"access".equals(claims.get("type", String.class))) {
                return Optional.empty();
            }

            String subject = claims.getSubject();
            if (subject == null || subject.isBlank()) {
                return Optional.empty();
            }

            Date expiration = claims.getExpiration();
            if (expiration == null || expiration.toInstant().isBefore(Instant.now())) {
                return Optional.empty();
            }

            return Optional.of(new JwtClaims(
                    Integer.parseInt(subject),
                    claims.get("email", String.class),
                    expiration.toInstant()
            ));
        } catch (JwtException | IllegalArgumentException ex) {
            return Optional.empty();
        }
    }
}
