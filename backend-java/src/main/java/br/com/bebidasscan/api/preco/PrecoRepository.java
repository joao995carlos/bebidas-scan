package br.com.bebidasscan.api.preco;

import br.com.bebidasscan.api.bebida.Bebida;
import java.util.List;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface PrecoRepository extends JpaRepository<Preco, Integer> {

    List<Preco> findByBebidaOrderByDataRegistroDesc(Bebida bebida);

    List<Preco> findByBebidaOrderByDataRegistroDesc(Bebida bebida, Pageable pageable);

    List<Preco> findByUsuarioIdUsuario(Integer idUsuario);

    List<Preco> findAllByOrderByIdPrecoDesc(Pageable pageable);

    List<Preco> findAllByOrderByDataRegistroDesc(Pageable pageable);

    @Modifying(clearAutomatically = true, flushAutomatically = true)
    @Query("""
            update Preco preco
               set preco.usuario = null
             where preco.usuario.idUsuario = :idUsuario
            """)
    int unlinkUsuarioId(@Param("idUsuario") Integer idUsuario);

    int deleteByUsuarioIdUsuario(Integer idUsuario);

    int deleteByBebidaIdBebida(Integer idBebida);
}
