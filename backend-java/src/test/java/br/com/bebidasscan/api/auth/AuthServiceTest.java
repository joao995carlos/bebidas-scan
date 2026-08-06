package br.com.bebidasscan.api.auth;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import br.com.bebidasscan.api.auth.dto.TokenResponse;
import br.com.bebidasscan.api.auth.dto.UsuarioLoginRequest;
import br.com.bebidasscan.api.common.ApiException;
import br.com.bebidasscan.api.common.EntityFields;
import br.com.bebidasscan.api.config.BebidasScanProperties;
import br.com.bebidasscan.api.security.RateLimitService;
import br.com.bebidasscan.api.usuario.Usuario;
import br.com.bebidasscan.api.usuario.UsuarioMapper;
import br.com.bebidasscan.api.usuario.UsuarioRepository;
import java.time.LocalDateTime;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.server.ResponseStatusException;

class AuthServiceTest {

    private UsuarioRepository usuarioRepository;
    private RefreshTokenRepository refreshTokenRepository;
    private CountingPasswordService passwordService;
    private FakeTokenService tokenService;
    private UsuarioMapper usuarioMapper;
    private RecordingRateLimitService rateLimitService;
    private AuthService authService;

    @BeforeEach
    void setUp() {
        usuarioRepository = mock(UsuarioRepository.class);
        refreshTokenRepository = mock(RefreshTokenRepository.class);
        passwordService = new CountingPasswordService();
        tokenService = new FakeTokenService();
        usuarioMapper = new UsuarioMapper();
        rateLimitService = new RecordingRateLimitService(testProperties(10));
        authService = new AuthService(
                usuarioRepository,
                refreshTokenRepository,
                mock(PasswordResetTokenRepository.class),
                passwordService,
                tokenService,
                null,
                usuarioMapper,
                null,
                null,
                rateLimitService
        );
    }

    @Test
    void loginComSucessoGeraTokensELimpaTentativas() {
        Usuario usuario = usuarioAtivo();

        when(usuarioRepository.findByEmail("joao@example.com")).thenReturn(Optional.of(usuario));

        TokenResponse response = authService.login(
                new UsuarioLoginRequest("joao@example.com", "Senha@123"),
                "127.0.0.1"
        );

        assertThat(response.accessToken()).isEqualTo("access.jwt");
        assertThat(response.refreshToken()).isEqualTo("refresh-token");
        assertThat(response.tokenType()).isEqualTo("bearer");
        assertThat(rateLimitService.lastCheck).isEqualTo("login|127.0.0.1|joao@example.com");
        assertThat(rateLimitService.lastSuccess).isEqualTo("login|127.0.0.1|joao@example.com");
        verify(refreshTokenRepository).save(any(RefreshToken.class));
    }

    @Test
    void loginComSenhaErradaRetornaNaoAutorizado() {
        Usuario usuario = usuarioAtivo();
        when(usuarioRepository.findByEmail("joao@example.com")).thenReturn(Optional.of(usuario));

        assertThatThrownBy(() -> authService.login(new UsuarioLoginRequest("joao@example.com", "errada"), "127.0.0.1"))
                .isInstanceOf(ApiException.class)
                .extracting("status")
                .isEqualTo(HttpStatus.UNAUTHORIZED);

        assertThat(rateLimitService.lastCheck).isEqualTo("login|127.0.0.1|joao@example.com");
        assertThat(rateLimitService.lastSuccess).isNull();
        verify(refreshTokenRepository, never()).save(any());
    }

    @Test
    void loginComUsuarioInativoRetornaNaoAutorizado() {
        Usuario usuario = usuarioAtivo();
        EntityFields.set(usuario, "ativo", false);
        when(usuarioRepository.findByEmail("joao@example.com")).thenReturn(Optional.of(usuario));

        assertThatThrownBy(() -> authService.login(new UsuarioLoginRequest("joao@example.com", "Senha@123"), "127.0.0.1"))
                .isInstanceOf(ApiException.class)
                .extracting("status")
                .isEqualTo(HttpStatus.UNAUTHORIZED);

        assertThat(passwordService.matchesCalls).isZero();
        verify(refreshTokenRepository, never()).save(any());
    }

    @Test
    void rateLimitBloqueiaAntesDeBuscarUsuario() {
        RateLimitService realRateLimit = new RateLimitService(testProperties(2));
        AuthService service = new AuthService(
                usuarioRepository,
                refreshTokenRepository,
                mock(PasswordResetTokenRepository.class),
                passwordService,
                tokenService,
                null,
                usuarioMapper,
                null,
                null,
                realRateLimit
        );

        UsuarioLoginRequest request = new UsuarioLoginRequest("rate@example.com", "Senha@123");
        when(usuarioRepository.findByEmail("rate@example.com")).thenReturn(Optional.empty());
        when(usuarioRepository.findByNomeUsuario("rate@example.com")).thenReturn(Optional.empty());

        assertThatThrownBy(() -> service.login(request, "10.0.0.5")).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> service.login(request, "10.0.0.5")).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> service.login(request, "10.0.0.5"))
                .isInstanceOf(ResponseStatusException.class)
                .extracting("statusCode")
                .isEqualTo(HttpStatus.TOO_MANY_REQUESTS);

        verify(usuarioRepository, times(2)).findByEmail("rate@example.com");
        verify(usuarioRepository, times(2)).findByNomeUsuario("rate@example.com");
    }

    private Usuario usuarioAtivo() {
        Usuario usuario = new Usuario();
        EntityFields.set(usuario, "idUsuario", 7);
        EntityFields.set(usuario, "nome", "Joao");
        EntityFields.set(usuario, "nomeUsuario", "joao");
        EntityFields.set(usuario, "email", "joao@example.com");
        EntityFields.set(usuario, "senhaHash", "hash");
        EntityFields.set(usuario, "ativo", true);
        EntityFields.set(usuario, "tipoUsuario", "comum");
        return usuario;
    }

    private BebidasScanProperties testProperties(int maxAttempts) {
        return new BebidasScanProperties(
                "12345678901234567890123456789012",
                "HS256",
                15,
                7,
                1048576,
                false,
                maxAttempts,
                60,
                maxAttempts,
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

    private static final class CountingPasswordService extends PasswordService {
        private int matchesCalls;

        private CountingPasswordService() {
            super(new PasswordEncoder() {
                @Override
                public String encode(CharSequence rawPassword) {
                    return "hash";
                }

                @Override
                public boolean matches(CharSequence rawPassword, String encodedPassword) {
                    return "Senha@123".contentEquals(rawPassword) && "hash".equals(encodedPassword);
                }
            });
        }

        @Override
        public boolean matches(String rawPassword, String hash) {
            matchesCalls++;
            return super.matches(rawPassword, hash);
        }
    }

    private static final class FakeTokenService extends TokenService {
        private FakeTokenService() {
            super(new BebidasScanProperties(
                    "12345678901234567890123456789012",
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
            ));
        }

        @Override
        public String createAccessToken(Usuario usuario) {
            return "access.jwt";
        }

        @Override
        public String createOpaqueToken() {
            return "refresh-token";
        }

        @Override
        public String hashToken(String token) {
            return token + "-hash";
        }

        @Override
        public LocalDateTime refreshExpiresAt() {
            return LocalDateTime.now().plusDays(7);
        }
    }

    private static final class RecordingRateLimitService extends RateLimitService {
        private String lastCheck;
        private String lastSuccess;

        private RecordingRateLimitService(BebidasScanProperties properties) {
            super(properties);
        }

        @Override
        public void checkAuthAttempt(String action, String clientHost, String identity) {
            lastCheck = action + "|" + clientHost + "|" + identity;
        }

        @Override
        public void registerAuthSuccess(String action, String clientHost, String identity) {
            lastSuccess = action + "|" + clientHost + "|" + identity;
        }
    }
}
