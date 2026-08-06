package br.com.bebidasscan.api.auth;

import static org.assertj.core.api.Assertions.assertThat;

import br.com.bebidasscan.api.common.EntityFields;
import br.com.bebidasscan.api.config.BebidasScanProperties;
import br.com.bebidasscan.api.usuario.Usuario;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import org.junit.jupiter.api.Test;

class TokenServiceTest {

    @Test
    void accessTokenTemClaimsCompativeisComPython() {
        String secret = "12345678901234567890123456789012";
        TokenService service = new TokenService(testProperties(secret));
        service.afterPropertiesSet();

        Usuario usuario = new Usuario();
        EntityFields.set(usuario, "idUsuario", 42);
        EntityFields.set(usuario, "email", "joao@example.com");

        String token = service.createAccessToken(usuario);
        var claims = Jwts.parser()
                .verifyWith(Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8)))
                .build()
                .parseSignedClaims(token)
                .getPayload();

        assertThat(claims.getSubject()).isEqualTo("42");
        assertThat(claims.get("email", String.class)).isEqualTo("joao@example.com");
        assertThat(claims.get("type", String.class)).isEqualTo("access");
        assertThat(claims.getExpiration().toInstant()).isAfter(Instant.now());
    }

    private BebidasScanProperties testProperties(String secret) {
        return new BebidasScanProperties(
                secret,
                "HS256",
                15,
                7,
                1048576,
                false,
                10,
                60,
                5,
                300,
                900,
                "BebidasScanTest/0.1",
                "",
                "Bebidas Scan <nao-responda@bebidasscan.com.br>",
                "https://api.bebidasscan.com.br/resetar-senha",
                "https://bebidasscan.com.br",
                ""
        );
    }
}
