package br.com.bebidasscan.api.bebida.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record CachacaResponse(
        @JsonProperty("id_cachaca") Integer idCachaca,
        @JsonProperty("id_bebida") Integer idBebida,
        @JsonProperty("volume_ml") Integer volumeMl,
        String classificacao,
        String madeira,
        @JsonProperty("tempo_envelhecimento_meses") Integer tempoEnvelhecimentoMeses,
        @JsonProperty("cidade_origem") String cidadeOrigem,
        @JsonProperty("estado_origem") String estadoOrigem,
        @JsonProperty("regiao_origem") String regiaoOrigem,
        String alambique,
        String produtor,
        String lote
) {
}
