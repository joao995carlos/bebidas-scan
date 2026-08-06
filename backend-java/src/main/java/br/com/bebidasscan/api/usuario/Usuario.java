package br.com.bebidasscan.api.usuario;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.Table;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Entity
@Table(
        name = "usuario",
        indexes = {
                @Index(name = "ix_usuario_email", columnList = "email"),
                @Index(name = "ix_usuario_nome_usuario", columnList = "nome_usuario")
        }
)
public class Usuario {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id_usuario")
    private Integer idUsuario;

    @Column(nullable = false, length = 150)
    private String nome;

    @Column(name = "nome_usuario", unique = true, length = 80)
    private String nomeUsuario;

    @Column(nullable = false, unique = true, length = 150)
    private String email;

    @Column(name = "senha_hash", nullable = false, columnDefinition = "text")
    private String senhaHash;

    @Column(name = "data_nascimento")
    private LocalDate dataNascimento;

    @Column(name = "confirmou_maioridade")
    private Boolean confirmouMaioridade = false;

    @Column(name = "email_verificado")
    private Boolean emailVerificado = false;

    private Boolean ativo = true;

    @Column(name = "tipo_usuario", nullable = false, length = 20)
    private String tipoUsuario = "comum";

    @Column(name = "privacidade_versao_aceita", length = 20)
    private String privacidadeVersaoAceita;

    @Column(name = "termos_versao_aceita", length = 20)
    private String termosVersaoAceita;

    @Column(name = "lgpd_aceite_em")
    private LocalDateTime lgpdAceiteEm;

    @Column(name = "marketing_consentimento")
    private Boolean marketingConsentimento = false;

    @Column(name = "marketing_consentimento_em")
    private LocalDateTime marketingConsentimentoEm;

    @Column(name = "anonimizado_em")
    private LocalDateTime anonimizadoEm;

    @Column(name = "data_criacao", insertable = false, updatable = false)
    private LocalDateTime dataCriacao;

    public Integer getIdUsuario() {
        return idUsuario;
    }

    public String getNome() {
        return nome;
    }

    public String getNomeUsuario() {
        return nomeUsuario;
    }

    public String getEmail() {
        return email;
    }

    public String getSenhaHash() {
        return senhaHash;
    }
}
