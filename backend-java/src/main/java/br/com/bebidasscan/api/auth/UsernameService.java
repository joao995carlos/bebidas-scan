package br.com.bebidasscan.api.auth;

import br.com.bebidasscan.api.common.ApiException;
import java.text.Normalizer;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

@Service
public class UsernameService {

    public String normalize(String value) {
        String username = value == null ? "" : value.trim().toLowerCase().replaceFirst("^@", "");
        if (!username.matches("^[a-z0-9._-]{3,80}$")) {
            throw new ApiException(
                    HttpStatus.UNPROCESSABLE_ENTITY,
                    "Nome de usuario deve ter 3 a 80 caracteres e usar apenas letras, numeros, ponto, hifen ou sublinhado."
            );
        }
        return username;
    }

    public String slug(String value) {
        String normalized = Normalizer.normalize(value == null ? "" : value.trim().toLowerCase(), Normalizer.Form.NFD)
                .replaceAll("\\p{M}", "")
                .replaceAll("[^a-z0-9._-]+", ".")
                .replaceAll("[._-]{2,}", ".")
                .replaceAll("^[._-]+|[._-]+$", "");
        if (normalized.length() < 3) {
            normalized = "usuario" + normalized;
        }
        return normalized.length() > 80 ? normalized.substring(0, 80) : normalized;
    }
}
