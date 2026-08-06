package br.com.bebidasscan.api.avaliacao.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record AvaliacaoCreateRequest(
        @JsonProperty("id_bebida") @NotNull Integer idBebida,
        @NotNull @Min(1) @Max(5) Integer nota,
        @Size(max = 1000) String comentario,
        @JsonProperty("compraria_novamente") Boolean comprariaNovamente
) {
}
