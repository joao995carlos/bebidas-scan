package br.com.bebidasscan.api.favorito.dto;

import br.com.bebidasscan.api.bebida.dto.BebidaResponse;
import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.LocalDateTime;

public record FavoritoResponse(
        @JsonProperty("id_favorito") Integer idFavorito,
        BebidaResponse bebida,
        @JsonProperty("data_favorito") LocalDateTime dataFavorito
) {
}
