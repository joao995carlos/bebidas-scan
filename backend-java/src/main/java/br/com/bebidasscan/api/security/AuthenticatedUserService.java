package br.com.bebidasscan.api.security;

import java.util.Map;
import java.util.Optional;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class AuthenticatedUserService {

    private final NamedParameterJdbcTemplate jdbcTemplate;

    public AuthenticatedUserService(NamedParameterJdbcTemplate jdbcTemplate) {
        this.jdbcTemplate = jdbcTemplate;
    }

    public Optional<AuthenticatedUser> findActiveUser(Integer userId) {
        String sql = """
                select id_usuario, email, tipo_usuario
                  from usuario
                 where id_usuario = :idUsuario
                   and ativo = true
                """;
        return jdbcTemplate.query(sql, Map.of("idUsuario", userId), (rs, rowNum) -> new AuthenticatedUser(
                rs.getInt("id_usuario"),
                rs.getString("email"),
                rs.getString("tipo_usuario")
        )).stream().findFirst();
    }
}
