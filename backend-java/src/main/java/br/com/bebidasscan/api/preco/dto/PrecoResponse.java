package br.com.bebidasscan.api.preco.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.math.BigDecimal;
import java.time.LocalDateTime;

public record PrecoResponse(
        @JsonProperty("id_preco") Integer idPreco,
        @JsonProperty("id_bebida") Integer idBebida,
        String mercado,
        String cidade,
        String estado,
        BigDecimal valor,
        @JsonProperty("data_registro") LocalDateTime dataRegistro
) {
}
