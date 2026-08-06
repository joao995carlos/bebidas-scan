package br.com.bebidasscan.api.auth.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record RefreshRequest(
        @JsonProperty("refresh_token") @NotBlank @Size(min = 20, max = 300) String refreshToken
) {
}
