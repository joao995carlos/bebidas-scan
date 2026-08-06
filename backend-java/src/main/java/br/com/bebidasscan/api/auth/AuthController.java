package br.com.bebidasscan.api.auth;

import br.com.bebidasscan.api.auth.dto.AccessTokenResponse;
import br.com.bebidasscan.api.auth.dto.ChangePasswordRequest;
import br.com.bebidasscan.api.auth.dto.ConfirmPasswordResetRequest;
import br.com.bebidasscan.api.auth.dto.RefreshRequest;
import br.com.bebidasscan.api.auth.dto.RequestPasswordResetRequest;
import br.com.bebidasscan.api.auth.dto.TokenResponse;
import br.com.bebidasscan.api.auth.dto.UsuarioCreateRequest;
import br.com.bebidasscan.api.auth.dto.UsuarioLoginRequest;
import br.com.bebidasscan.api.common.dto.ErrorResponse;
import br.com.bebidasscan.api.common.dto.MessageResponse;
import br.com.bebidasscan.api.observability.MdcKeys;
import br.com.bebidasscan.api.observability.ClientIpResolver;
import br.com.bebidasscan.api.security.AuthenticatedUser;
import br.com.bebidasscan.api.usuario.Usuario;
import br.com.bebidasscan.api.usuario.UsuarioRepository;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import java.time.OffsetDateTime;
import java.util.Map;
import org.slf4j.MDC;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/auth")
public class AuthController {

    private final AuthService authService;
    private final UsuarioRepository usuarioRepository;
    private final ClientIpResolver clientIpResolver;

    public AuthController(
            AuthService authService,
            UsuarioRepository usuarioRepository,
            ClientIpResolver clientIpResolver
    ) {
        this.authService = authService;
        this.usuarioRepository = usuarioRepository;
        this.clientIpResolver = clientIpResolver;
    }

    @PostMapping("/registrar")
    public TokenResponse registrar(@Valid @RequestBody UsuarioCreateRequest request) {
        return authService.register(request);
    }

    @PostMapping("/login")
    public TokenResponse login(
            @Valid @RequestBody UsuarioLoginRequest request,
            HttpServletRequest httpRequest
    ) {
        String clientIp = clientIpResolver.resolve(httpRequest);
        return authService.login(request, clientIp);
    }

    @PostMapping("/refresh")
    public AccessTokenResponse refresh(@Valid @RequestBody RefreshRequest request) {
        return authService.refresh(request);
    }

    @PostMapping("/logout")
    public MessageResponse logout(@Valid @RequestBody RefreshRequest request) {
        return toMessage(authService.logout(request));
    }

    @PostMapping("/alterar-senha")
    public MessageResponse alterarSenha(
            @AuthenticationPrincipal AuthenticatedUser authenticatedUser,
            @Valid @RequestBody ChangePasswordRequest request
    ) {
        Usuario usuario = usuarioRepository.getReferenceById(authenticatedUser.idUsuario());
        return toMessage(authService.changePassword(request, usuario));
    }

    @PostMapping("/solicitar-reset-senha")
    public MessageResponse solicitarResetSenha(@Valid @RequestBody RequestPasswordResetRequest request) {
        return toMessage(authService.requestPasswordReset(request));
    }

    @PostMapping("/confirmar-reset-senha")
    public MessageResponse confirmarResetSenha(@Valid @RequestBody ConfirmPasswordResetRequest request) {
        return toMessage(authService.confirmPasswordReset(request));
    }

    private static MessageResponse toMessage(Map<String, String> response) {
        return new MessageResponse(response.getOrDefault("detail", "ok"));
    }

    @ExceptionHandler(ResponseStatusException.class)
    public ResponseEntity<ErrorResponse> handleResponseStatusException(
            ResponseStatusException exception,
            HttpServletRequest request
    ) {
        String detail = exception.getReason() == null || exception.getReason().isBlank()
                ? "Requisicao invalida"
                : exception.getReason();
        ErrorResponse body = new ErrorResponse(
                detail,
                request.getRequestURI(),
                MDC.get(MdcKeys.REQUEST_ID),
                OffsetDateTime.now()
        );
        return ResponseEntity.status(exception.getStatusCode())
                .headers(exception.getHeaders())
                .body(body);
    }
}
