package br.com.bebidasscan.api.perfil.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record AccountDeletionRequest(
        @Email @NotBlank String email,
        @NotBlank @Size(max = 100) String senha
) {
}
