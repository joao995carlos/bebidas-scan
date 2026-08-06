package br.com.bebidasscan.api.preco;

import br.com.bebidasscan.api.preco.dto.PrecoCreateRequest;
import br.com.bebidasscan.api.preco.dto.PrecoResponse;
import br.com.bebidasscan.api.security.AuthenticatedUser;
import br.com.bebidasscan.api.usuario.Usuario;
import br.com.bebidasscan.api.usuario.UsuarioRepository;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/precos")
public class PrecoController {

    private final PrecoService precoService;
    private final UsuarioRepository usuarioRepository;

    public PrecoController(PrecoService precoService, UsuarioRepository usuarioRepository) {
        this.precoService = precoService;
        this.usuarioRepository = usuarioRepository;
    }

    @PostMapping
    public PrecoResponse registrar(
            @AuthenticationPrincipal AuthenticatedUser authenticatedUser,
            @Valid @RequestBody PrecoCreateRequest request
    ) {
        return precoService.create(request, usuario(authenticatedUser));
    }

    @GetMapping("/bebida/{id_bebida}")
    public List<PrecoResponse> listarPorBebida(@PathVariable("id_bebida") Integer idBebida) {
        return precoService.listByBebida(idBebida);
    }

    private Usuario usuario(AuthenticatedUser authenticatedUser) {
        return usuarioRepository.getReferenceById(authenticatedUser.idUsuario());
    }
}
