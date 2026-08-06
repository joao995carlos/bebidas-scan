package br.com.bebidasscan.api.preco;

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
import java.math.BigDecimal;
import java.time.LocalDateTime;
import org.hibernate.annotations.Check;

@Entity
@Check(constraints = "valor >= 0")
@Table(name = "preco")
public class Preco {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id_preco")
    private Integer idPreco;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "id_usuario")
    private Usuario usuario;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "id_bebida", nullable = false)
    private Bebida bebida;

    @Column(length = 150)
    private String mercado;

    @Column(length = 100)
    private String cidade;

    @Column(length = 2)
    private String estado;

    @Column(nullable = false, precision = 10, scale = 2)
    private BigDecimal valor;

    @Column(name = "data_registro", insertable = false, updatable = false)
    private LocalDateTime dataRegistro;
}
