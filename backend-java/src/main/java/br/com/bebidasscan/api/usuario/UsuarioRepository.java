package br.com.bebidasscan.api.usuario;

import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UsuarioRepository extends JpaRepository<Usuario, Integer> {

    Optional<Usuario> findByEmail(String email);

    Optional<Usuario> findByNomeUsuario(String nomeUsuario);

    Optional<Usuario> findByEmailAndAtivoTrue(String email);

    Optional<Usuario> findByIdUsuarioAndAtivoTrue(Integer idUsuario);

    Optional<Usuario> findByAtivoTrueAndEmailOrAtivoTrueAndNomeUsuario(
            String email,
            String nomeUsuario
    );

    boolean existsByEmail(String email);

    boolean existsByNomeUsuario(String nomeUsuario);

    boolean existsByEmailOrNomeUsuario(String email, String nomeUsuario);

    long countByAtivoTrue();

    List<Usuario> findAllByOrderByIdUsuarioDesc(Pageable pageable);

    List<Usuario> findAllByOrderByDataCriacaoDesc(Pageable pageable);
}
