package br.com.bebidasscan.api.bebida;

import br.com.bebidasscan.api.usuario.Usuario;
import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.OneToOne;
import jakarta.persistence.Table;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(
        name = "bebida",
        indexes = @Index(name = "ix_bebida_codigo_barras", columnList = "codigo_barras")
)
public class Bebida {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id_bebida")
    private Integer idBebida;

    @Column(nullable = false, length = 200)
    private String nome;

    @Column(length = 150)
    private String marca;

    @Column(nullable = false, length = 80)
    private String tipo;

    @Column(name = "codigo_barras", unique = true, length = 80)
    private String codigoBarras;

    @Column(name = "teor_alcoolico", precision = 5, scale = 2)
    private BigDecimal teorAlcoolico;

    @Column(name = "volume_ml")
    private Integer volumeMl;

    @Column(columnDefinition = "text")
    private String ingredientes;

    @Column(name = "imagem_url", columnDefinition = "text")
    private String imagemUrl;

    @Column(name = "nutri_score", length = 10)
    private String nutriScore;

    @Column(name = "nova_grupo")
    private Integer novaGrupo;

    @Column(name = "eco_score", length = 30)
    private String ecoScore;

    @Column(columnDefinition = "text")
    private String alergenos;

    @Column(columnDefinition = "text")
    private String categorias;

    @Column(length = 80)
    private String quantidade;

    @Column(columnDefinition = "text")
    private String embalagem;

    @Column(columnDefinition = "text")
    private String paises;

    @Column(length = 100)
    private String classificacao;

    @Column(length = 100)
    private String madeira;

    @Column(name = "tempo_envelhecimento_meses")
    private Integer tempoEnvelhecimentoMeses;

    @Column(name = "cidade_origem", length = 100)
    private String cidadeOrigem;

    @Column(name = "estado_origem", length = 2)
    private String estadoOrigem;

    @Column(name = "regiao_origem", length = 100)
    private String regiaoOrigem;

    @Column(length = 150)
    private String alambique;

    @Column(length = 150)
    private String produtor;

    @Column(length = 80)
    private String lote;

    @Column(name = "origem_dados", length = 80)
    private String origemDados;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "id_criado_por")
    private Usuario criadoPor;

    @Column(name = "criada_em", insertable = false, updatable = false)
    private LocalDateTime criadaEm;

    @OneToOne(mappedBy = "bebida", fetch = FetchType.LAZY, cascade = CascadeType.ALL, orphanRemoval = true)
    private Cachaca cachaca;

    public Integer getIdBebida() {
        return idBebida;
    }

    public String getNome() {
        return nome;
    }

    public String getCodigoBarras() {
        return codigoBarras;
    }
}
