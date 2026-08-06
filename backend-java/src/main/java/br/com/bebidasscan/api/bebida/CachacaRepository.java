package br.com.bebidasscan.api.bebida;

import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CachacaRepository extends JpaRepository<Cachaca, Integer> {

    Optional<Cachaca> findByBebidaIdBebida(Integer idBebida);

    void deleteByBebidaIdBebida(Integer idBebida);
}
