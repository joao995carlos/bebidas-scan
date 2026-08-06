package br.com.bebidasscan.api.usuario;

import br.com.bebidasscan.api.common.EntityFields;
import br.com.bebidasscan.api.usuario.dto.UsuarioResponse;
import java.time.LocalDate;
import java.time.LocalDateTime;
import org.springframework.stereotype.Component;

@Component
public class UsuarioMapper {

    public UsuarioResponse toResponse(Usuario usuario) {
        return new UsuarioResponse(
                usuario.getIdUsuario(),
                usuario.getNome(),
                usuario.getNomeUsuario(),
                usuario.getEmail(),
                EntityFields.get(usuario, "ativo", Boolean.class),
                EntityFields.get(usuario, "confirmouMaioridade", Boolean.class),
                EntityFields.get(usuario, "tipoUsuario", String.class),
                EntityFields.get(usuario, "dataNascimento", LocalDate.class),
                EntityFields.get(usuario, "privacidadeVersaoAceita", String.class),
                EntityFields.get(usuario, "termosVersaoAceita", String.class),
                EntityFields.get(usuario, "lgpdAceiteEm", LocalDateTime.class),
                EntityFields.get(usuario, "marketingConsentimento", Boolean.class)
        );
    }
}
