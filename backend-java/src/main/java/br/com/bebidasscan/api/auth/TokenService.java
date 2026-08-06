package br.com.bebidasscan.api.auth;

import br.com.bebidasscan.api.config.BebidasScanProperties;
import br.com.bebidasscan.api.usuario.Usuario;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import io.jsonwebtoken.security.MacAlgorithm;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Date;
import java.util.HexFormat;
import javax.crypto.SecretKey;
import org.springframework.beans.factory.InitializingBean;
import org.springframework.stereotype.Service;

@Service
public class TokenService implements InitializingBean {

    private final BebidasScanProperties properties;
    private final SecureRandom secureRandom = new SecureRandom();
    private SecretKey secretKey;
    private MacAlgorithm algorithm;

    public TokenService(BebidasScanProperties properties) {
        this.properties = properties;
    }

    @Override
    public void afterPropertiesSet() {
        if (properties.jwtSecretKey() == null || properties.jwtSecretKey().length() < 32) {
            throw new IllegalStateException("JWT_SECRET_KEY precisa ter pelo menos 32 caracteres");
        }
        algorithm = switch (properties.jwtAlgorithm()) {
            case "HS256" -> Jwts.SIG.HS256;
            case "HS384" -> Jwts.SIG.HS384;
            case "HS512" -> Jwts.SIG.HS512;
            default -> throw new IllegalStateException("JWT_ALGORITHM invalido");
        };
        secretKey = Keys.hmacShaKeyFor(properties.jwtSecretKey().getBytes(StandardCharsets.UTF_8));
    }

    public String createAccessToken(Usuario usuario) {
        Instant expiration = Instant.now().plusSeconds(properties.accessTokenExpireMinutes() * 60);
        return Jwts.builder()
                .subject(String.valueOf(usuario.getIdUsuario()))
                .claim("email", usuario.getEmail())
                .claim("type", "access")
                .expiration(Date.from(expiration))
                .signWith(secretKey, algorithm)
                .compact();
    }

    public String createOpaqueToken() {
        byte[] random = new byte[64];
        secureRandom.nextBytes(random);
        return base64Url(random);
    }

    public String hashToken(String token) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            return HexFormat.of().formatHex(digest.digest(token.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception exception) {
            throw new IllegalStateException("Falha ao gerar hash de token", exception);
        }
    }

    public LocalDateTime refreshExpiresAt() {
        return LocalDateTime.now(ZoneOffset.UTC).plusDays(properties.refreshTokenExpireDays());
    }

    private static String base64Url(byte[] bytes) {
        return java.util.Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
    }
}
