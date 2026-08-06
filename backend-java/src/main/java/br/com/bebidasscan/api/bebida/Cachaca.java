package br.com.bebidasscan.api.bebida;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.OneToOne;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

@Entity
@Table(name = "cachaca")
public class Cachaca {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id_cachaca")
    private Integer idCachaca;

    @OneToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "id_bebida", nullable = false, unique = true)
    private Bebida bebida;

    @Column(name = "volume_ml")
    private Integer volumeMl;

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

    @Column(name = "criada_em", insertable = false, updatable = false)
    private LocalDateTime criadaEm;
}
