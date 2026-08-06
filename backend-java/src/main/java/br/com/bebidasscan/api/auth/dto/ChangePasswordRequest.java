package br.com.bebidasscan.api.auth.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record ChangePasswordRequest(
        @JsonProperty("senha_atual") @NotBlank @Size(max = 100) String senhaAtual,
        @JsonProperty("nova_senha") @NotBlank @Size(min = 8, max = 100) String novaSenha
) {
}
