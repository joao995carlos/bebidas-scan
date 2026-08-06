package br.com.bebidasscan.api.favorito;

import br.com.bebidasscan.api.common.dto.MessageResponse;
import br.com.bebidasscan.api.favorito.dto.FavoritoResponse;
import br.com.bebidasscan.api.security.AuthenticatedUser;
import br.com.bebidasscan.api.usuario.Usuario;
import br.com.bebidasscan.api.usuario.UsuarioRepository;
import java.util.List;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/favoritos")
public class FavoritoController {

    private final FavoritoService favoritoService;
    private final UsuarioRepository usuarioRepository;

    public FavoritoController(FavoritoService favoritoService, UsuarioRepository usuarioRepository) {
        this.favoritoService = favoritoService;
        this.usuarioRepository = usuarioRepository;
    }

    @GetMapping
    public List<FavoritoResponse> listar(@AuthenticationPrincipal AuthenticatedUser authenticatedUser) {
        return favoritoService.listMine(usuario(authenticatedUser));
    }

    @PostMapping("/{id_bebida}")
    public FavoritoResponse favoritar(
            @AuthenticationPrincipal AuthenticatedUser authenticatedUser,
            @PathVariable("id_bebida") Integer idBebida
    ) {
        return favoritoService.favorite(idBebida, usuario(authenticatedUser));
    }

    @DeleteMapping("/{id_bebida}")
    public MessageResponse remover(
            @AuthenticationPrincipal AuthenticatedUser authenticatedUser,
            @PathVariable("id_bebida") Integer idBebida
    ) {
        return new MessageResponse(favoritoService.remove(idBebida, usuario(authenticatedUser)).getOrDefault("detail", "ok"));
    }

    private Usuario usuario(AuthenticatedUser authenticatedUser) {
        return usuarioRepository.getReferenceById(authenticatedUser.idUsuario());
    }
}
