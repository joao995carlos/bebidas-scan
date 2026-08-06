package br.com.bebidasscan.api.security;

public record AuthenticatedUser(
        Integer idUsuario,
        String email,
        String tipoUsuario
) {
    public boolean isAdmin() {
        return "admin".equalsIgnoreCase(tipoUsuario);
    }
}
