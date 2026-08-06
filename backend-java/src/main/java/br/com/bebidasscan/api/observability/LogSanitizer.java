package br.com.bebidasscan.api.observability;

import java.util.Locale;
import java.util.Set;
import java.util.regex.Pattern;

public class LogSanitizer {

    private static final Set<String> SENSITIVE_KEYS = Set.of(
            "authorization",
            "access_token",
            "refresh_token",
            "token",
            "token_hash",
            "jwt",
            "senha",
            "senha_hash",
            "password",
            "secret",
            "csrf_token",
            "web_access_token",
            "web_refresh_token",
            "cookie",
            "set-cookie",
            "email",
            "identity",
            "cpf",
            "telefone",
            "data_nascimento"
    );

    private static final Pattern SENSITIVE_PATTERN = Pattern.compile(
            "(?i)(bearer\\s+)[a-z0-9._\\-~+/=]+|"
                    + "((access|refresh)?_?token|password|senha|secret|cpf|email)=([^&\\s]+)|"
                    + "(\"(?:access|refresh)?_?token\"|\"password\"|\"senha\"|\"secret\"|\"cpf\"|\"email\")\\s*:\\s*\"[^\"]*\""
    );

    public String sanitizeHeader(String key, String value) {
        if (key == null || value == null) {
            return value;
        }
        String normalizedKey = key.toLowerCase(Locale.ROOT);
        if (SENSITIVE_KEYS.stream().anyMatch(normalizedKey::contains)) {
            return "***MASKED***";
        }
        return sanitizeText(value);
    }

    public String sanitizeText(String value) {
        if (value == null) {
            return null;
        }
        return SENSITIVE_PATTERN.matcher(value).replaceAll(matchResult -> {
            String match = matchResult.group();
            if (match.toLowerCase(Locale.ROOT).startsWith("bearer ")) {
                return "Bearer ***MASKED***";
            }
            int equalsIndex = match.indexOf('=');
            if (equalsIndex > -1) {
                return match.substring(0, equalsIndex + 1) + "***MASKED***";
            }
            int colonIndex = match.indexOf(':');
            if (colonIndex > -1) {
                return match.substring(0, colonIndex + 1) + "\"***MASKED***\"";
            }
            return "***MASKED***";
        });
    }
}
