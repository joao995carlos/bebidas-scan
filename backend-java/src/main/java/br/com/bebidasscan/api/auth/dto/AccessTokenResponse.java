package br.com.bebidasscan.api.auth.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public record AccessTokenResponse(
        @JsonProperty("access_token") String accessToken,
        @JsonProperty("token_type") String tokenType
) {
    public AccessTokenResponse(String accessToken) {
        this(accessToken, "bearer");
    }
}
