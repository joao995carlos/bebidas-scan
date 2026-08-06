package br.com.bebidasscan.api.auth;

import br.com.bebidasscan.api.usuario.Usuario;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

@Entity
@Table(
        name = "refresh_token",
        indexes = @Index(name = "ix_refresh_token_token_hash", columnList = "token_hash")
)
public class RefreshToken {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "id_token")
    private Integer idToken;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "id_usuario")
    private Usuario usuario;

    @Column(name = "token_hash", nullable = false, columnDefinition = "text")
    private String tokenHash;

    @Column(nullable = false)
    private LocalDateTime expiracao;

    private Boolean revogado = false;

    @Column(name = "criado_em", insertable = false, updatable = false)
    private LocalDateTime criadoEm;

    @Column(name = "revogado_em")
    private LocalDateTime revogadoEm;
}
