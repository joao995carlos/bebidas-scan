package br.com.bebidasscan.api.bebida;

import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface BebidaRepository extends JpaRepository<Bebida, Integer> {

    Optional<Bebida> findByCodigoBarras(String codigoBarras);

    boolean existsByCodigoBarras(String codigoBarras);

    List<Bebida> findTop20ByNomeContainingIgnoreCaseOrMarcaContainingIgnoreCase(String nome, String marca);

    List<Bebida> findByNomeContainingIgnoreCaseOrderByNomeAsc(String nome, Pageable pageable);

    List<Bebida> findAllByOrderByNomeAsc(Pageable pageable);

    List<Bebida> findAllByOrderByIdBebidaDesc(Pageable pageable);

    List<Bebida> findAllByOrderByCriadaEmDesc(Pageable pageable);

    List<Bebida> findByNomeContainingIgnoreCaseOrderByIdBebidaDesc(String nome, Pageable pageable);

    List<Bebida> findByCriadoPorIdUsuario(Integer idUsuario);

    @Modifying(clearAutomatically = true, flushAutomatically = true)
    @Query("""
            update Bebida bebida
               set bebida.criadoPor = null
             where bebida.criadoPor.idUsuario = :idUsuario
            """)
    int unlinkCriadoPorUsuarioId(@Param("idUsuario") Integer idUsuario);
}
