package br.com.bebidasscan.api.auth;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface RefreshTokenRepository extends JpaRepository<RefreshToken, Integer> {

    Optional<RefreshToken> findByTokenHash(String tokenHash);

    Optional<RefreshToken> findByTokenHashAndRevogadoFalseAndExpiracaoAfter(
            String tokenHash,
            LocalDateTime agora
    );

    List<RefreshToken> findByUsuarioIdUsuarioAndRevogadoFalse(Integer idUsuario);

    @Modifying(clearAutomatically = true, flushAutomatically = true)
    @Query("""
            update RefreshToken token
               set token.revogado = true,
                   token.revogadoEm = :revogadoEm
             where token.usuario.idUsuario = :idUsuario
               and token.revogado = false
            """)
    int revokeActiveByUsuarioId(
            @Param("idUsuario") Integer idUsuario,
            @Param("revogadoEm") LocalDateTime revogadoEm
    );

    @Modifying(clearAutomatically = true, flushAutomatically = true)
    @Query("""
            update RefreshToken token
               set token.revogado = true,
                   token.revogadoEm = :revogadoEm
             where token.usuario.idUsuario = :idUsuario
            """)
    int revokeAllByUsuarioId(
            @Param("idUsuario") Integer idUsuario,
            @Param("revogadoEm") LocalDateTime revogadoEm
    );

    @Modifying(clearAutomatically = true, flushAutomatically = true)
    @Query("""
            delete from RefreshToken token
             where token.usuario.idUsuario = :idUsuario
            """)
    int deleteByUsuarioId(@Param("idUsuario") Integer idUsuario);

    @Modifying(clearAutomatically = true, flushAutomatically = true)
    @Query("""
            delete from RefreshToken token
             where (token.revogado = true and token.revogadoEm < :limite)
                or token.expiracao < :limite
            """)
    int deleteExpiredOrRevokedBefore(@Param("limite") LocalDateTime limite);
}
