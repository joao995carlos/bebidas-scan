package br.com.bebidasscan.api.bebida.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Size;

public record CachacaRequest(
        @JsonProperty("volume_ml") @Min(1) @Max(100000) Integer volumeMl,
        @Size(max = 100) String classificacao,
        @Size(max = 100) String madeira,
        @JsonProperty("tempo_envelhecimento_meses") @Min(0) @Max(1200) Integer tempoEnvelhecimentoMeses,
        @JsonProperty("cidade_origem") @Size(max = 100) String cidadeOrigem,
        @JsonProperty("estado_origem") @Size(min = 2, max = 2) String estadoOrigem,
        @JsonProperty("regiao_origem") @Size(max = 100) String regiaoOrigem,
        @Size(max = 150) String alambique,
        @Size(max = 150) String produtor,
        @Size(max = 80) String lote
) {
}
