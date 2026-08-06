package br.com.bebidasscan.api.avaliacao;

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
import org.hibernate.annotations.Check;

@Entity
@Check(constraints = "nota >= 1 AND nota <= 5")
@Table(
        name = "avaliacao",
        uniqueConstraints = @UniqueConstraint(
                name = "uq_avaliacao_usuario_bebida",
                columnNames = {"id_usuario", "id_bebida"}
        )
)
public class Avaliacao {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id_avaliacao")
    private Integer idAvaliacao;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "id_usuario")
    private Usuario usuario;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "id_bebida", nullable = false)
    private Bebida bebida;

    @Column(nullable = false)
    private Integer nota;

    @Column(columnDefinition = "text")
    private String comentario;

    @Column(name = "compraria_novamente")
    private Boolean comprariaNovamente;

    @Column(name = "data_avaliacao", insertable = false, updatable = false)
    private LocalDateTime dataAvaliacao;
}
