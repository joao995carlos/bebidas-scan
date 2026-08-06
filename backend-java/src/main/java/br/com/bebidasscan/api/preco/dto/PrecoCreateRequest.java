package br.com.bebidasscan.api.preco.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.math.BigDecimal;

public record PrecoCreateRequest(
        @JsonProperty("id_bebida") @NotNull Integer idBebida,
        @Size(max = 150) String mercado,
        @Size(max = 100) String cidade,
        @Size(min = 2, max = 2) String estado,
        @NotNull @DecimalMin("0") BigDecimal valor
) {
}
