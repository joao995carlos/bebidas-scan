package br.com.bebidasscan.api.favorito;

import br.com.bebidasscan.api.bebida.Bebida;
import br.com.bebidasscan.api.bebida.BebidaMapper;
import br.com.bebidasscan.api.common.EntityFields;
import br.com.bebidasscan.api.favorito.dto.FavoritoResponse;
import java.time.LocalDateTime;
import org.springframework.stereotype.Component;

@Component
public class FavoritoMapper {

    private final BebidaMapper bebidaMapper;

    public FavoritoMapper(BebidaMapper bebidaMapper) {
        this.bebidaMapper = bebidaMapper;
    }

    public FavoritoResponse toResponse(Favorito favorito) {
        Bebida bebida = EntityFields.get(favorito, "bebida", Bebida.class);
        return new FavoritoResponse(
                EntityFields.get(favorito, "idFavorito", Integer.class),
                bebida == null ? null : bebidaMapper.toResponse(bebida),
                EntityFields.get(favorito, "dataFavorito", LocalDateTime.class)
        );
    }
}
