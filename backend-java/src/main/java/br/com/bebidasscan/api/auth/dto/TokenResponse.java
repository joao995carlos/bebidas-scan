package br.com.bebidasscan.api.auth.dto;

import br.com.bebidasscan.api.usuario.dto.UsuarioResponse;
import com.fasterxml.jackson.annotation.JsonProperty;

public record TokenResponse(
        @JsonProperty("access_token") String accessToken,
        @JsonProperty("refresh_token") String refreshToken,
        @JsonProperty("token_type") String tokenType,
        UsuarioResponse usuario
) {
    public TokenResponse(String accessToken, String refreshToken, UsuarioResponse usuario) {
        this(accessToken, refreshToken, "bearer", usuario);
    }
}
