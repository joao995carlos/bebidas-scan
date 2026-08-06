package br.com.bebidasscan.api.favorito;

import br.com.bebidasscan.api.bebida.Bebida;
import br.com.bebidasscan.api.usuario.Usuario;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface FavoritoRepository extends JpaRepository<Favorito, Integer> {

    List<Favorito> findByUsuarioOrderByDataFavoritoDesc(Usuario usuario);

    Optional<Favorito> findByUsuarioAndBebida(Usuario usuario, Bebida bebida);

    Optional<Favorito> findByUsuarioIdUsuarioAndBebidaIdBebida(Integer idUsuario, Integer idBebida);

    List<Favorito> findByUsuarioIdUsuario(Integer idUsuario);

    List<Favorito> findAllByOrderByIdFavoritoDesc(Pageable pageable);

    int deleteByUsuarioIdUsuario(Integer idUsuario);

    int deleteByBebidaIdBebida(Integer idBebida);
}
