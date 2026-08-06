package br.com.bebidasscan.api.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "bebidas-scan")
public record BebidasScanProperties(
        String jwtSecretKey,
        String jwtAlgorithm,
        long accessTokenExpireMinutes,
        long refreshTokenExpireDays,
        int maxRequestBodyBytes,
        boolean trustProxyHeaders,
        int authRateLimitMaxAttempts,
        int authRateLimitWindowSeconds,
        int authRateLimitIdentityMaxAttempts,
        int authRateLimitIdentityWindowSeconds,
        int authLockoutSeconds,
        String openFoodFactsUserAgent,
        String resendApiKey,
        String emailFrom,
        String passwordResetBaseUrl,
        String appWebUrl,
        String corsOrigins
) {
}
