package br.com.bebidasscan.api.avaliacao.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.LocalDateTime;

public record AvaliacaoResponse(
        @JsonProperty("id_avaliacao") Integer idAvaliacao,
        @JsonProperty("id_bebida") Integer idBebida,
        Integer nota,
        String comentario,
        @JsonProperty("compraria_novamente") Boolean comprariaNovamente,
        @JsonProperty("data_avaliacao") LocalDateTime dataAvaliacao
) {
}
