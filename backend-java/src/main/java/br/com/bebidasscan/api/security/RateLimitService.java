package br.com.bebidasscan.api.security;

import br.com.bebidasscan.api.config.BebidasScanProperties;
import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Duration;
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HexFormat;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

@Service
public class RateLimitService {

    private static final Logger SECURITY_LOGGER = LoggerFactory.getLogger("bebidas_scan.security");

    private final BebidasScanProperties properties;
    private final Cache<String, Deque<Long>> attempts;
    private final Cache<String, Long> blockedUntil;

    public RateLimitService(BebidasScanProperties properties) {
        this.properties = properties;
        this.attempts = Caffeine.newBuilder()
                .expireAfterAccess(Duration.ofSeconds(Math.max(properties.authLockoutSeconds(), 60) * 2L))
                .build();
        this.blockedUntil = Caffeine.newBuilder()
                .expireAfterWrite(Duration.ofSeconds(Math.max(properties.authLockoutSeconds(), 60) * 2L))
                .build();
    }

    public void checkAuthAttempt(String action, String clientHost, String identity) {
        long now = System.nanoTime();
        String normalizedIdentity = normalize(identity);
        String ipKey = action + ":ip:" + clientHost;
        String identityKey = normalizedIdentity == null ? null : action + ":identity:" + normalizedIdentity;

        for (String key : identityKey == null ? List.of(ipKey) : List.of(ipKey, identityKey)) {
            Long until = blockedUntil.getIfPresent(key);
            if (until != null && until > now) {
                SECURITY_LOGGER.warn("Autenticacao bloqueada por lockout action={} client={} identityHash={} key={}",
                        action, clientHost, identityHash(normalizedIdentity), keyForLog(key));
                throw tooManyAttempts();
            }
            if (until != null) {
                blockedUntil.invalidate(key);
            }
        }

        register(ipKey, properties.authRateLimitWindowSeconds(), properties.authRateLimitMaxAttempts(), now,
                action, clientHost, normalizedIdentity);
        if (identityKey != null) {
            register(identityKey, properties.authRateLimitIdentityWindowSeconds(),
                    properties.authRateLimitIdentityMaxAttempts(), now, action, clientHost, normalizedIdentity);
        }
    }

    public void registerAuthSuccess(String action, String clientHost, String identity) {
        String normalizedIdentity = normalize(identity);
        attempts.invalidate(action + ":ip:" + clientHost);
        blockedUntil.invalidate(action + ":ip:" + clientHost);
        if (normalizedIdentity != null) {
            attempts.invalidate(action + ":identity:" + normalizedIdentity);
            blockedUntil.invalidate(action + ":identity:" + normalizedIdentity);
        }
    }

    private void register(
            String key,
            int windowSeconds,
            int maxAttempts,
            long now,
            String action,
            String clientHost,
            String identity
    ) {
        Deque<Long> entries = attempts.get(key, ignored -> new ArrayDeque<>());
        long windowStart = now - Duration.ofSeconds(windowSeconds).toNanos();
        synchronized (entries) {
            while (!entries.isEmpty() && entries.peekFirst() < windowStart) {
                entries.removeFirst();
            }
            if (entries.size() >= maxAttempts) {
                blockedUntil.put(key, now + Duration.ofSeconds(properties.authLockoutSeconds()).toNanos());
                SECURITY_LOGGER.warn("Rate limit acionado action={} client={} identityHash={} key={} attempts={}",
                        action, clientHost, identityHash(identity), keyForLog(key), entries.size());
                throw tooManyAttempts();
            }
            entries.addLast(now);
        }
    }

    private ResponseStatusException tooManyAttempts() {
        return new ResponseStatusException(
                HttpStatus.TOO_MANY_REQUESTS,
                "Muitas tentativas. Aguarde um pouco e tente novamente."
        );
    }

    private String normalize(String identity) {
        if (identity == null || identity.isBlank()) {
            return null;
        }
        return identity.trim().toLowerCase();
    }

    private String identityHash(String identity) {
        if (identity == null) {
            return "-";
        }
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            return HexFormat.of().formatHex(digest.digest(identity.getBytes(StandardCharsets.UTF_8))).substring(0, 12);
        } catch (NoSuchAlgorithmException ex) {
            return "-";
        }
    }

    private String keyForLog(String key) {
        if (!key.contains(":identity:")) {
            return key;
        }
        int index = key.lastIndexOf(":identity:");
        return key.substring(0, index + 10) + identityHash(key.substring(index + 10));
    }
}
