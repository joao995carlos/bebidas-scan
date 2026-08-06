package br.com.bebidasscan.api.favorito;

import br.com.bebidasscan.api.bebida.Bebida;
import br.com.bebidasscan.api.usuario.Usuario;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;
import java.time.LocalDateTime;

@Entity
@Table(
        name = "favorito",
        uniqueConstraints = @UniqueConstraint(
                name = "uq_favorito_usuario_bebida",
                columnNames = {"id_usuario", "id_bebida"}
        )
)
public class Favorito {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id_favorito")
    private Integer idFavorito;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "id_usuario", nullable = false)
    private Usuario usuario;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "id_bebida", nullable = false)
    private Bebida bebida;

    @Column(name = "data_favorito", insertable = false, updatable = false)
    private LocalDateTime dataFavorito;
}
