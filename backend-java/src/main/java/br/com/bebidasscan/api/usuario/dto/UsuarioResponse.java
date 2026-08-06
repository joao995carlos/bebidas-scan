package br.com.bebidasscan.api.usuario.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.time.LocalDate;
import java.time.LocalDateTime;

public record UsuarioResponse(
        @JsonProperty("id_usuario") Integer idUsuario,
        String nome,
        @JsonProperty("nome_usuario") String nomeUsuario,
        String email,
        Boolean ativo,
        @JsonProperty("confirmou_maioridade") Boolean confirmouMaioridade,
        @JsonProperty("tipo_usuario") String tipoUsuario,
        @JsonProperty("data_nascimento") LocalDate dataNascimento,
        @JsonProperty("privacidade_versao_aceita") String privacidadeVersaoAceita,
        @JsonProperty("termos_versao_aceita") String termosVersaoAceita,
        @JsonProperty("lgpd_aceite_em") LocalDateTime lgpdAceiteEm,
        @JsonProperty("marketing_consentimento") Boolean marketingConsentimento
) {
}
