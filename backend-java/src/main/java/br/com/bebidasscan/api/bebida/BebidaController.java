package br.com.bebidasscan.api.bebida;

import br.com.bebidasscan.api.bebida.dto.BebidaCreateRequest;
import br.com.bebidasscan.api.bebida.dto.BebidaResponse;
import br.com.bebidasscan.api.bebida.dto.BebidaUpdateRequest;
import br.com.bebidasscan.api.security.AuthenticatedUser;
import br.com.bebidasscan.api.usuario.Usuario;
import br.com.bebidasscan.api.usuario.UsuarioRepository;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Size;
import java.util.List;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@Validated
@RestController
@RequestMapping("/bebidas")
public class BebidaController {

    private final BebidaService bebidaService;
    private final UsuarioRepository usuarioRepository;

    public BebidaController(BebidaService bebidaService, UsuarioRepository usuarioRepository) {
        this.bebidaService = bebidaService;
        this.usuarioRepository = usuarioRepository;
    }

    @PostMapping
    public BebidaResponse criar(
            @AuthenticationPrincipal AuthenticatedUser authenticatedUser,
            @Valid @RequestBody BebidaCreateRequest request
    ) {
        return bebidaService.create(request, usuario(authenticatedUser));
    }

    @PatchMapping("/{id_bebida}")
    public BebidaResponse atualizar(
            @AuthenticationPrincipal AuthenticatedUser authenticatedUser,
            @PathVariable("id_bebida") Integer idBebida,
            @Valid @RequestBody BebidaUpdateRequest request
    ) {
        return bebidaService.update(idBebida, request, usuario(authenticatedUser));
    }

    @GetMapping("/codigo/{codigo_barras}")
    public BebidaResponse buscarPorCodigo(@PathVariable("codigo_barras") String codigoBarras) {
        return bebidaService.findByBarcode(codigoBarras);
    }

    @GetMapping("/buscar")
    public List<BebidaResponse> buscarPorNome(@RequestParam("q") @Size(min = 2, max = 80) String q) {
        return bebidaService.searchByName(q);
    }

    private Usuario usuario(AuthenticatedUser authenticatedUser) {
        return usuarioRepository.getReferenceById(authenticatedUser.idUsuario());
    }
}
