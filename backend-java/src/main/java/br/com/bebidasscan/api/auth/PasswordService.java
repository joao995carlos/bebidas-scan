package br.com.bebidasscan.api.auth;

import br.com.bebidasscan.api.common.ApiException;
import org.springframework.http.HttpStatus;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

@Service
public class PasswordService {

    public static final String STRONG_PASSWORD_MESSAGE =
            "A senha precisa ter pelo menos 8 caracteres, uma letra maiuscula, um numero e um caractere especial.";

    private final PasswordEncoder passwordEncoder;

    public PasswordService(PasswordEncoder passwordEncoder) {
        this.passwordEncoder = passwordEncoder;
    }

    public String hash(String password) {
        validateStrongPassword(password);
        return passwordEncoder.encode(password);
    }

    public boolean matches(String rawPassword, String hash) {
        return rawPassword != null && hash != null && passwordEncoder.matches(rawPassword, hash);
    }

    public void validateStrongPassword(String password) {
        if (password == null
                || password.length() < 8
                || !password.matches(".*[A-Z].*")
                || !password.matches(".*\\d.*")
                || !password.matches(".*[^A-Za-z0-9].*")) {
            throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, STRONG_PASSWORD_MESSAGE);
        }
    }
}
