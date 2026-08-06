package br.com.bebidasscan.api.favorito;

import br.com.bebidasscan.api.bebida.Bebida;
import br.com.bebidasscan.api.bebida.BebidaRepository;
import br.com.bebidasscan.api.common.ApiException;
import br.com.bebidasscan.api.common.EntityFields;
import br.com.bebidasscan.api.favorito.dto.FavoritoResponse;
import br.com.bebidasscan.api.usuario.Usuario;
import java.util.List;
import java.util.Map;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class FavoritoService {

    private final FavoritoRepository favoritoRepository;
    private final BebidaRepository bebidaRepository;
    private final FavoritoMapper mapper;

    public FavoritoService(FavoritoRepository favoritoRepository, BebidaRepository bebidaRepository, FavoritoMapper mapper) {
        this.favoritoRepository = favoritoRepository;
        this.bebidaRepository = bebidaRepository;
        this.mapper = mapper;
    }

    public List<FavoritoResponse> listMine(Usuario usuario) {
        return favoritoRepository.findByUsuarioOrderByDataFavoritoDesc(usuario).stream()
                .map(mapper::toResponse)
                .toList();
    }

    @Transactional
    public FavoritoResponse favorite(Integer bebidaId, Usuario usuario) {
        Bebida bebida = bebidaRepository.findById(bebidaId)
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "Bebida nao encontrada"));
        Favorito favorito = favoritoRepository.findByUsuarioAndBebida(usuario, bebida).orElseGet(Favorito::new);
        EntityFields.set(favorito, "usuario", usuario);
        EntityFields.set(favorito, "bebida", bebida);
        return mapper.toResponse(favoritoRepository.save(favorito));
    }

    @Transactional
    public Map<String, String> remove(Integer bebidaId, Usuario usuario) {
        Bebida bebida = bebidaRepository.findById(bebidaId)
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "Favorito nao encontrado"));
        Favorito favorito = favoritoRepository.findByUsuarioAndBebida(usuario, bebida)
                .orElseThrow(() -> new ApiException(HttpStatus.NOT_FOUND, "Favorito nao encontrado"));
        favoritoRepository.delete(favorito);
        return Map.of("detail", "Favorito removido");
    }
}
