package br.com.bebidasscan.api.avaliacao;

import br.com.bebidasscan.api.usuario.Usuario;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface AvaliacaoRepository extends JpaRepository<Avaliacao, Integer> {

    List<Avaliacao> findByUsuarioOrderByDataAvaliacaoDesc(Usuario usuario);

    Optional<Avaliacao> findByUsuarioIdUsuarioAndBebidaIdBebida(Integer idUsuario, Integer idBebida);

    List<Avaliacao> findByUsuarioIdUsuario(Integer idUsuario);

    List<Avaliacao> findAllByOrderByIdAvaliacaoDesc(Pageable pageable);

    List<Avaliacao> findAllByOrderByDataAvaliacaoDesc(Pageable pageable);

    @Modifying(clearAutomatically = true, flushAutomatically = true)
    @Query("""
            update Avaliacao avaliacao
               set avaliacao.usuario = null,
                   avaliacao.comentario = null
             where avaliacao.usuario.idUsuario = :idUsuario
            """)
    int anonymizeByUsuarioId(@Param("idUsuario") Integer idUsuario);

    int deleteByUsuarioIdUsuario(Integer idUsuario);

    int deleteByBebidaIdBebida(Integer idBebida);
}
