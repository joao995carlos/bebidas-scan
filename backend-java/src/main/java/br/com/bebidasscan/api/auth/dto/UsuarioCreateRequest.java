package br.com.bebidasscan.api.auth.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import java.time.LocalDate;

public record UsuarioCreateRequest(
        @NotBlank @Size(min = 2, max = 150) String nome,
        @JsonProperty("nome_usuario") @NotBlank @Size(min = 3, max = 80) String nomeUsuario,
        @Email @NotBlank @Size(max = 150) String email,
        @NotBlank @Size(min = 8, max = 100) String senha,
        @JsonProperty("data_nascimento") @NotNull LocalDate dataNascimento,
        @JsonProperty("aceitou_privacidade") boolean aceitouPrivacidade,
        @JsonProperty("aceitou_termos") boolean aceitouTermos,
        @JsonProperty("marketing_consentimento") boolean marketingConsentimento
) {
}
