package br.com.bebidasscan.api.auth.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ConfirmPasswordResetRequest(
        @NotBlank @Size(min = 20, max = 300) String token,
        @JsonProperty("nova_senha") @NotBlank @Size(min = 8, max = 100) String novaSenha
) {
}
