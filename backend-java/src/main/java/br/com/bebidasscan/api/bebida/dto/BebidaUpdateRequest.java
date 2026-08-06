package br.com.bebidasscan.api.bebida.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.Valid;
import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Size;
import java.math.BigDecimal;

public record BebidaUpdateRequest(
        @Size(max = 200) String nome,
        @Size(max = 150) String marca,
        @Size(max = 80) String tipo,
        @JsonProperty("codigo_barras") @Size(min = 6, max = 80) String codigoBarras,
        @JsonProperty("teor_alcoolico") @DecimalMin("0") @DecimalMax("100") BigDecimal teorAlcoolico,
        String ingredientes,
        @JsonProperty("imagem_url") String imagemUrl,
        @JsonProperty("nutri_score") @Size(max = 10) String nutriScore,
        @JsonProperty("nova_grupo") @Min(1) @Max(4) Integer novaGrupo,
        @JsonProperty("eco_score") @Size(max = 30) String ecoScore,
        String alergenos,
        String categorias,
        @Size(max = 80) String quantidade,
        String embalagem,
        String paises,
        @Valid CachacaRequest cachaca,
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
