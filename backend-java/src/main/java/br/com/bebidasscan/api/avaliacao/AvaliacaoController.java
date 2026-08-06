package br.com.bebidasscan.api.avaliacao;

import br.com.bebidasscan.api.avaliacao.dto.AvaliacaoCreateRequest;
import br.com.bebidasscan.api.avaliacao.dto.AvaliacaoResponse;
import br.com.bebidasscan.api.security.AuthenticatedUser;
import br.com.bebidasscan.api.usuario.Usuario;
import br.com.bebidasscan.api.usuario.UsuarioRepository;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/avaliacoes")
public class AvaliacaoController {

    private final AvaliacaoService avaliacaoService;
    private final UsuarioRepository usuarioRepository;

    public AvaliacaoController(AvaliacaoService avaliacaoService, UsuarioRepository usuarioRepository) {
        this.avaliacaoService = avaliacaoService;
        this.usuarioRepository = usuarioRepository;
    }

    @PostMapping
    public AvaliacaoResponse salvar(
            @AuthenticationPrincipal AuthenticatedUser authenticatedUser,
            @Valid @RequestBody AvaliacaoCreateRequest request
    ) {
        return avaliacaoService.save(request, usuario(authenticatedUser));
    }

    @GetMapping("/minhas")
    public List<AvaliacaoResponse> minhas(@AuthenticationPrincipal AuthenticatedUser authenticatedUser) {
        return avaliacaoService.listMine(usuario(authenticatedUser));
    }

    private Usuario usuario(AuthenticatedUser authenticatedUser) {
        return usuarioRepository.getReferenceById(authenticatedUser.idUsuario());
    }
}
