package br.com.bebidasscan.api.perfil.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotNull;
import java.time.LocalDate;

public record LgpdAcceptRequest(
        @JsonProperty("data_nascimento") @NotNull LocalDate dataNascimento,
        @JsonProperty("aceitou_privacidade") boolean aceitouPrivacidade,
        @JsonProperty("aceitou_termos") boolean aceitouTermos,
        @JsonProperty("marketing_consentimento") boolean marketingConsentimento
) {
}
