package br.com.bebidasscan.api.perfil.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.LocalDateTime;

public record LgpdStatusResponse(
        boolean pendente,
        @JsonProperty("versao_atual") String versaoAtual,
        @JsonProperty("privacidade_versao_aceita") String privacidadeVersaoAceita,
        @JsonProperty("termos_versao_aceita") String termosVersaoAceita,
        @JsonProperty("lgpd_aceite_em") LocalDateTime lgpdAceiteEm
) {
}
