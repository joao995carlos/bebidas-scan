package br.com.bebidasscan.api.auth;

import br.com.bebidasscan.api.auth.dto.AccessTokenResponse;
import br.com.bebidasscan.api.auth.dto.ChangePasswordRequest;
import br.com.bebidasscan.api.auth.dto.ConfirmPasswordResetRequest;
import br.com.bebidasscan.api.auth.dto.RefreshRequest;
import br.com.bebidasscan.api.auth.dto.RequestPasswordResetRequest;
import br.com.bebidasscan.api.auth.dto.TokenResponse;
import br.com.bebidasscan.api.auth.dto.UsuarioCreateRequest;
import br.com.bebidasscan.api.auth.dto.UsuarioLoginRequest;
import br.com.bebidasscan.api.common.ApiException;
import br.com.bebidasscan.api.common.EntityFields;
import br.com.bebidasscan.api.email.EmailNotConfiguredException;
import br.com.bebidasscan.api.email.TransactionalEmailService;
import br.com.bebidasscan.api.lgpd.LgpdService;
import br.com.bebidasscan.api.security.RateLimitService;
import br.com.bebidasscan.api.usuario.Usuario;
import br.com.bebidasscan.api.usuario.UsuarioMapper;
import br.com.bebidasscan.api.usuario.UsuarioRepository;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Map;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AuthService {

    private final UsuarioRepository usuarioRepository;
    private final RefreshTokenRepository refreshTokenRepository;
    private final PasswordResetTokenRepository passwordResetTokenRepository;
    private final PasswordService passwordService;
    private final TokenService tokenService;
    private final UsernameService usernameService;
    private final UsuarioMapper usuarioMapper;
    private final LgpdService lgpdService;
    private final TransactionalEmailService emailService;
    private final RateLimitService rateLimitService;

    public AuthService(
            UsuarioRepository usuarioRepository,
            RefreshTokenRepository refreshTokenRepository,
            PasswordResetTokenRepository passwordResetTokenRepository,
            PasswordService passwordService,
            TokenService tokenService,
            UsernameService usernameService,
            UsuarioMapper usuarioMapper,
            LgpdService lgpdService,
            TransactionalEmailService emailService,
            RateLimitService rateLimitService
    ) {
        this.usuarioRepository = usuarioRepository;
        this.refreshTokenRepository = refreshTokenRepository;
        this.passwordResetTokenRepository = passwordResetTokenRepository;
        this.passwordService = passwordService;
        this.tokenService = tokenService;
        this.usernameService = usernameService;
        this.usuarioMapper = usuarioMapper;
        this.lgpdService = lgpdService;
        this.emailService = emailService;
        this.rateLimitService = rateLimitService;
    }

    @Transactional
    public TokenResponse register(UsuarioCreateRequest request) {
        if (!request.aceitouPrivacidade() || !request.aceitouTermos()) {
            throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "E necessario aceitar a Politica de Privacidade e os Termos de Uso.");
        }
        if (!lgpdService.isAdult(request.dataNascimento())) {
            throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "O Bebidas Scan e destinado a maiores de 18 anos.");
        }

        String email = normalizeEmail(request.email());
        String username = usernameService.normalize(request.nomeUsuario());
        if (usuarioRepository.existsByEmail(email)) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "E-mail ja cadastrado");
        }
        if (usuarioRepository.existsByNomeUsuario(username)) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "Nome de usuario ja cadastrado");
        }

        Usuario usuario = new Usuario();
        EntityFields.set(usuario, "nome", request.nome().trim());
        EntityFields.set(usuario, "nomeUsuario", username);
        EntityFields.set(usuario, "email", email);
        EntityFields.set(usuario, "senhaHash", passwordService.hash(request.senha()));
        lgpdService.applyAcceptance(usuario, request.dataNascimento(), request.marketingConsentimento());

        try {
            usuario = usuarioRepository.save(usuario);
        } catch (DataIntegrityViolationException exception) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "E-mail ou nome de usuario ja cadastrado");
        }
        TokenResponse response = issueTokens(usuario);
        emailService.sendWelcomeSafely(usuario.getEmail(), usuario.getNome(), usuario.getIdUsuario());
        return response;
    }

    @Transactional
    public TokenResponse login(UsuarioLoginRequest request) {
        return login(request, "unknown");
    }

    @Transactional
    public TokenResponse login(UsuarioLoginRequest request, String clientHost) {
        String identity = request.identificador().trim().toLowerCase().replaceFirst("^@", "");
        rateLimitService.checkAuthAttempt("login", clientHost, identity);
        Usuario usuario = usuarioRepository.findByEmail(identity)
                .or(() -> usuarioRepository.findByNomeUsuario(identity))
                .filter(this::isActive)
                .filter(item -> passwordService.matches(request.senha(), item.getSenhaHash()))
                .orElseThrow(() -> new ApiException(HttpStatus.UNAUTHORIZED, "Nome de usuario ou senha invalidos"));
        rateLimitService.registerAuthSuccess("login", clientHost, identity);
        return issueTokens(usuario);
    }

    @Transactional
    public AccessTokenResponse refresh(RefreshRequest request) {
        RefreshToken refreshToken = refreshTokenRepository.findByTokenHashAndRevogadoFalseAndExpiracaoAfter(
                        tokenService.hashToken(request.refreshToken()),
                        LocalDateTime.now(ZoneOffset.UTC)
                )
                .orElseThrow(() -> new ApiException(HttpStatus.UNAUTHORIZED, "Refresh token invalido ou expirado"));
        Usuario usuario = EntityFields.get(refreshToken, "usuario", Usuario.class);
        if (usuario == null || !isActive(usuario)) {
            throw new ApiException(HttpStatus.UNAUTHORIZED, "Usuario nao encontrado ou inativo");
        }
        return new AccessTokenResponse(tokenService.createAccessToken(usuario));
    }

    @Transactional
    public Map<String, String> logout(RefreshRequest request) {
        refreshTokenRepository.findByTokenHash(tokenService.hashToken(request.refreshToken()))
                .filter(token -> !Boolean.TRUE.equals(EntityFields.get(token, "revogado", Boolean.class)))
                .ifPresent(this::revokeRefreshToken);
        return Map.of("detail", "Logout realizado");
    }

    @Transactional
    public Map<String, String> changePassword(ChangePasswordRequest request, Usuario usuario) {
        if (!passwordService.matches(request.senhaAtual(), usuario.getSenhaHash())) {
            throw new ApiException(HttpStatus.FORBIDDEN, "Senha atual nao confere");
        }
        if (passwordService.matches(request.novaSenha(), usuario.getSenhaHash())) {
            throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "A nova senha precisa ser diferente da atual");
        }
        EntityFields.set(usuario, "senhaHash", passwordService.hash(request.novaSenha()));
        revokeAllTokens(usuario);
        usuarioRepository.save(usuario);
        emailService.sendPasswordChangedSafely(usuario.getEmail(), usuario.getNome(), usuario.getIdUsuario());
        return Map.of("detail", "Senha alterada com sucesso. Entre novamente nos outros dispositivos.");
    }

    @Transactional
    public Map<String, String> requestPasswordReset(RequestPasswordResetRequest request) {
        String email = normalizeEmail(request.email());
        Map<String, String> response = Map.of("detail", "Se o e-mail existir, enviaremos instrucoes para redefinir a senha.");
        Usuario usuario = usuarioRepository.findByEmail(email).filter(this::isActive).orElse(null);
        if (usuario == null) {
            return response;
        }

        String token = tokenService.createOpaqueToken();
        PasswordResetToken resetToken = new PasswordResetToken();
        EntityFields.set(resetToken, "usuario", usuario);
        EntityFields.set(resetToken, "tokenHash", tokenService.hashToken(token));
        EntityFields.set(resetToken, "expiracao", LocalDateTime.now(ZoneOffset.UTC).plusMinutes(30));
        passwordResetTokenRepository.save(resetToken);

        try {
            emailService.sendPasswordReset(email, token);
        } catch (EmailNotConfiguredException exception) {
            throw new ApiException(HttpStatus.SERVICE_UNAVAILABLE, "Envio de e-mail ainda nao configurado");
        } catch (RuntimeException exception) {
            throw new ApiException(HttpStatus.BAD_GATEWAY, "Falha temporaria ao enviar e-mail");
        }
        return response;
    }

    @Transactional
    public Map<String, String> confirmPasswordReset(ConfirmPasswordResetRequest request) {
        PasswordResetToken resetToken = passwordResetTokenRepository.findByTokenHash(tokenService.hashToken(request.token()))
                .filter(this::isPasswordResetTokenUsable)
                .orElseThrow(() -> new ApiException(HttpStatus.BAD_REQUEST, "Token invalido ou expirado"));
        Usuario usuario = EntityFields.get(resetToken, "usuario", Usuario.class);
        if (usuario == null || !isActive(usuario)) {
            throw new ApiException(HttpStatus.BAD_REQUEST, "Usuario nao encontrado ou inativo");
        }
        if (passwordService.matches(request.novaSenha(), usuario.getSenhaHash())) {
            throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "A nova senha precisa ser diferente da atual");
        }
        EntityFields.set(usuario, "senhaHash", passwordService.hash(request.novaSenha()));
        EntityFields.set(resetToken, "usado", true);
        EntityFields.set(resetToken, "usadoEm", LocalDateTime.now(ZoneOffset.UTC));
        revokeAllTokens(usuario);
        usuarioRepository.save(usuario);
        passwordResetTokenRepository.save(resetToken);
        emailService.sendPasswordRedefinedSafely(usuario.getEmail(), usuario.getNome(), usuario.getIdUsuario());
        return Map.of("detail", "Senha redefinida com sucesso.");
    }

    @Transactional
    public TokenResponse issueTokens(Usuario usuario) {
        String accessToken = tokenService.createAccessToken(usuario);
        String refreshToken = tokenService.createOpaqueToken();
        RefreshToken record = new RefreshToken();
        EntityFields.set(record, "usuario", usuario);
        EntityFields.set(record, "tokenHash", tokenService.hashToken(refreshToken));
        EntityFields.set(record, "expiracao", tokenService.refreshExpiresAt());
        refreshTokenRepository.save(record);
        return new TokenResponse(accessToken, refreshToken, usuarioMapper.toResponse(usuario));
    }

    public void revokeAllTokens(Usuario usuario) {
        refreshTokenRepository.revokeAllByUsuarioId(usuario.getIdUsuario(), LocalDateTime.now(ZoneOffset.UTC));
    }

    private void revokeRefreshToken(RefreshToken token) {
        EntityFields.set(token, "revogado", true);
        EntityFields.set(token, "revogadoEm", LocalDateTime.now(ZoneOffset.UTC));
        refreshTokenRepository.save(token);
    }

    private boolean isPasswordResetTokenUsable(PasswordResetToken token) {
        Boolean used = EntityFields.get(token, "usado", Boolean.class);
        LocalDateTime expiration = EntityFields.get(token, "expiracao", LocalDateTime.class);
        return !Boolean.TRUE.equals(used) && expiration != null && expiration.isAfter(LocalDateTime.now(ZoneOffset.UTC));
    }

    private boolean isActive(Usuario usuario) {
        return Boolean.TRUE.equals(EntityFields.get(usuario, "ativo", Boolean.class));
    }

    private static String normalizeEmail(String email) {
        return email == null ? "" : email.trim().toLowerCase();
    }
}
