package br.com.bebidasscan.api.bebida.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.math.BigDecimal;

public record BebidaResponse(
        @JsonProperty("id_bebida") Integer idBebida,
        String nome,
        String marca,
        String tipo,
        @JsonProperty("codigo_barras") String codigoBarras,
        @JsonProperty("teor_alcoolico") BigDecimal teorAlcoolico,
        String ingredientes,
        @JsonProperty("imagem_url") String imagemUrl,
        @JsonProperty("nutri_score") String nutriScore,
        @JsonProperty("nova_grupo") Integer novaGrupo,
        @JsonProperty("eco_score") String ecoScore,
        String alergenos,
        String categorias,
        String quantidade,
        String embalagem,
        String paises,
        CachacaResponse cachaca,
        @JsonProperty("origem_dados") String origemDados,
        @JsonProperty("id_criado_por") Integer idCriadoPor
) {
}
