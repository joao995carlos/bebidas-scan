package br.com.bebidasscan.api.perfil;

import br.com.bebidasscan.api.common.dto.MessageResponse;
import br.com.bebidasscan.api.perfil.dto.AccountDeletionRequest;
import br.com.bebidasscan.api.perfil.dto.LgpdAcceptRequest;
import br.com.bebidasscan.api.perfil.dto.LgpdStatusResponse;
import br.com.bebidasscan.api.security.AuthenticatedUser;
import br.com.bebidasscan.api.usuario.Usuario;
import br.com.bebidasscan.api.usuario.UsuarioRepository;
import br.com.bebidasscan.api.usuario.dto.UsuarioResponse;
import jakarta.validation.Valid;
import org.springframework.http.ContentDisposition;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/perfil")
public class PerfilController {

    private final PerfilService perfilService;
    private final UsuarioRepository usuarioRepository;

    public PerfilController(PerfilService perfilService, UsuarioRepository usuarioRepository) {
        this.perfilService = perfilService;
        this.usuarioRepository = usuarioRepository;
    }

    @GetMapping("/me")
    public UsuarioResponse me(@AuthenticationPrincipal AuthenticatedUser authenticatedUser) {
        return perfilService.me(usuario(authenticatedUser));
    }

    @GetMapping("/lgpd/status")
    public LgpdStatusResponse lgpdStatus(@AuthenticationPrincipal AuthenticatedUser authenticatedUser) {
        return perfilService.lgpdStatus(usuario(authenticatedUser));
    }

    @PostMapping("/lgpd/aceitar")
    public LgpdStatusResponse aceitarLgpd(
            @AuthenticationPrincipal AuthenticatedUser authenticatedUser,
            @Valid @RequestBody LgpdAcceptRequest request
    ) {
        return perfilService.acceptLgpd(request, usuario(authenticatedUser));
    }

    @GetMapping("/exportar.csv")
    public ResponseEntity<String> exportarCsv(
            @AuthenticationPrincipal AuthenticatedUser authenticatedUser,
            @RequestParam(name = "categorias", defaultValue = "perfil") String categorias
    ) {
        String csv = perfilService.exportCsv(categorias, usuario(authenticatedUser));
        return ResponseEntity.ok()
                .contentType(new MediaType("text", "csv"))
                .header(HttpHeaders.CONTENT_DISPOSITION,
                        ContentDisposition.attachment().filename("bebidas_scan_dados.csv").build().toString())
                .body(csv);
    }

    @PostMapping("/anonimizar")
    public MessageResponse anonimizar(
            @AuthenticationPrincipal AuthenticatedUser authenticatedUser,
            @Valid @RequestBody AccountDeletionRequest request
    ) {
        return new MessageResponse(perfilService.anonymize(request, usuario(authenticatedUser)).getOrDefault("detail", "ok"));
    }

    private Usuario usuario(AuthenticatedUser authenticatedUser) {
        return usuarioRepository.getReferenceById(authenticatedUser.idUsuario());
    }
}
