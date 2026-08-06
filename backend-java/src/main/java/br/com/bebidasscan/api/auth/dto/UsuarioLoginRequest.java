package br.com.bebidasscan.api.auth.dto;

import com.fasterxml.jackson.annotation.JsonAlias;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record UsuarioLoginRequest(
        @JsonAlias({"email", "nome_usuario"})
        @NotBlank @Size(min = 3, max = 150)
        String identificador,
        @NotBlank @Size(max = 100)
        String senha
) {
}
