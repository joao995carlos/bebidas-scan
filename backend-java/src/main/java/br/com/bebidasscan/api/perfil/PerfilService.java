package br.com.bebidasscan.api.perfil;

import br.com.bebidasscan.api.auth.AuthService;
import br.com.bebidasscan.api.auth.PasswordService;
import br.com.bebidasscan.api.avaliacao.Avaliacao;
import br.com.bebidasscan.api.avaliacao.AvaliacaoRepository;
import br.com.bebidasscan.api.bebida.Bebida;
import br.com.bebidasscan.api.bebida.BebidaRepository;
import br.com.bebidasscan.api.common.ApiException;
import br.com.bebidasscan.api.common.EntityFields;
import br.com.bebidasscan.api.favorito.Favorito;
import br.com.bebidasscan.api.favorito.FavoritoRepository;
import br.com.bebidasscan.api.lgpd.LgpdService;
import br.com.bebidasscan.api.perfil.dto.AccountDeletionRequest;
import br.com.bebidasscan.api.perfil.dto.LgpdAcceptRequest;
import br.com.bebidasscan.api.perfil.dto.LgpdStatusResponse;
import br.com.bebidasscan.api.preco.Preco;
import br.com.bebidasscan.api.preco.PrecoRepository;
import br.com.bebidasscan.api.usuario.Usuario;
import br.com.bebidasscan.api.usuario.UsuarioMapper;
import br.com.bebidasscan.api.usuario.UsuarioRepository;
import br.com.bebidasscan.api.usuario.dto.UsuarioResponse;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Arrays;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class PerfilService {

    private static final Set<String> ALLOWED_EXPORT_CATEGORIES = Set.of("perfil", "avaliacoes", "favoritos", "precos", "bebidas");

    private final UsuarioRepository usuarioRepository;
    private final AvaliacaoRepository avaliacaoRepository;
    private final FavoritoRepository favoritoRepository;
    private final PrecoRepository precoRepository;
    private final BebidaRepository bebidaRepository;
    private final UsuarioMapper usuarioMapper;
    private final LgpdService lgpdService;
    private final PasswordService passwordService;
    private final AuthService authService;

    public PerfilService(
            UsuarioRepository usuarioRepository,
            AvaliacaoRepository avaliacaoRepository,
            FavoritoRepository favoritoRepository,
            PrecoRepository precoRepository,
            BebidaRepository bebidaRepository,
            UsuarioMapper usuarioMapper,
            LgpdService lgpdService,
            PasswordService passwordService,
            AuthService authService
    ) {
        this.usuarioRepository = usuarioRepository;
        this.avaliacaoRepository = avaliacaoRepository;
        this.favoritoRepository = favoritoRepository;
        this.precoRepository = precoRepository;
        this.bebidaRepository = bebidaRepository;
        this.usuarioMapper = usuarioMapper;
        this.lgpdService = lgpdService;
        this.passwordService = passwordService;
        this.authService = authService;
    }

    public UsuarioResponse me(Usuario usuario) {
        return usuarioMapper.toResponse(usuario);
    }

    public LgpdStatusResponse lgpdStatus(Usuario usuario) {
        return lgpdService.status(usuario);
    }

    @Transactional
    public LgpdStatusResponse acceptLgpd(LgpdAcceptRequest request, Usuario usuario) {
        if (!request.aceitouPrivacidade() || !request.aceitouTermos()) {
            throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "E necessario aceitar a Politica de Privacidade e os Termos de Uso.");
        }
        if (!lgpdService.isAdult(request.dataNascimento())) {
            throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "O Bebidas Scan e destinado a maiores de 18 anos.");
        }
        lgpdService.applyAcceptance(usuario, request.dataNascimento(), request.marketingConsentimento());
        usuarioRepository.save(usuario);
        return lgpdService.status(usuario);
    }

    public String exportCsv(String categories, Usuario usuario) {
        Set<String> selected = selectExportCategories(categories);
        StringBuilder csv = new StringBuilder();
        csv.append("categoria,campo,valor\n");

        if (selected.contains("perfil")) {
            row(csv, "perfil", "id_usuario", usuario.getIdUsuario());
            row(csv, "perfil", "nome", usuario.getNome());
            row(csv, "perfil", "nome_usuario", usuario.getNomeUsuario());
            row(csv, "perfil", "email", usuario.getEmail());
            row(csv, "perfil", "data_nascimento", EntityFields.get(usuario, "dataNascimento"));
            row(csv, "perfil", "confirmou_maioridade", EntityFields.get(usuario, "confirmouMaioridade"));
            row(csv, "perfil", "privacidade_versao_aceita", EntityFields.get(usuario, "privacidadeVersaoAceita"));
            row(csv, "perfil", "termos_versao_aceita", EntityFields.get(usuario, "termosVersaoAceita"));
            row(csv, "perfil", "lgpd_aceite_em", EntityFields.get(usuario, "lgpdAceiteEm"));
            row(csv, "perfil", "marketing_consentimento", EntityFields.get(usuario, "marketingConsentimento"));
        }
        if (selected.contains("avaliacoes")) {
            row(csv, "avaliacoes", "colunas", "id_avaliacao,id_bebida,nota,comentario,compraria_novamente,data_avaliacao");
            avaliacaoRepository.findByUsuarioOrderByDataAvaliacaoDesc(usuario).forEach(item -> row(
                    csv,
                    "avaliacoes",
                    EntityFields.get(item, "idAvaliacao"),
                    "%s,%s,%s,%s,%s".formatted(
                            id(EntityFields.get(item, "bebida", Bebida.class)),
                            EntityFields.get(item, "nota"),
                            value(EntityFields.get(item, "comentario")),
                            EntityFields.get(item, "comprariaNovamente"),
                            EntityFields.get(item, "dataAvaliacao")
                    )
            ));
        }
        if (selected.contains("favoritos")) {
            row(csv, "favoritos", "colunas", "id_favorito,id_bebida,data_favorito");
            favoritoRepository.findByUsuarioOrderByDataFavoritoDesc(usuario).forEach(item -> row(
                    csv,
                    "favoritos",
                    EntityFields.get(item, "idFavorito"),
                    "%s,%s".formatted(id(EntityFields.get(item, "bebida", Bebida.class)), EntityFields.get(item, "dataFavorito"))
            ));
        }
        if (selected.contains("precos")) {
            row(csv, "precos", "colunas", "id_preco,id_bebida,mercado,cidade,estado,valor,data_registro");
            precoRepository.findAll().stream()
                    .filter(item -> usuario.equals(EntityFields.get(item, "usuario", Usuario.class)))
                    .forEach(item -> row(
                            csv,
                            "precos",
                            EntityFields.get(item, "idPreco"),
                            "%s,%s,%s,%s,%s,%s".formatted(
                                    id(EntityFields.get(item, "bebida", Bebida.class)),
                                    value(EntityFields.get(item, "mercado")),
                                    value(EntityFields.get(item, "cidade")),
                                    value(EntityFields.get(item, "estado")),
                                    EntityFields.get(item, "valor"),
                                    EntityFields.get(item, "dataRegistro")
                            )
                    ));
        }
        if (selected.contains("bebidas")) {
            row(csv, "bebidas", "colunas", "id_bebida,nome,marca,tipo,codigo_barras,criada_em");
            bebidaRepository.findAll().stream()
                    .filter(item -> usuario.equals(EntityFields.get(item, "criadoPor", Usuario.class)))
                    .forEach(item -> row(
                            csv,
                            "bebidas",
                            item.getIdBebida(),
                            "%s,%s,%s,%s,%s".formatted(
                                    item.getNome(),
                                    value(EntityFields.get(item, "marca")),
                                    value(EntityFields.get(item, "tipo")),
                                    value(item.getCodigoBarras()),
                                    EntityFields.get(item, "criadaEm")
                            )
                    ));
        }
        return csv.toString();
    }

    @Transactional
    public Map<String, String> anonymize(AccountDeletionRequest request, Usuario usuario) {
        String email = request.email() == null ? "" : request.email().trim().toLowerCase();
        if (!usuario.getEmail().equals(email) || !passwordService.matches(request.senha(), usuario.getSenhaHash())) {
            throw new ApiException(HttpStatus.FORBIDDEN, "E-mail ou senha nao conferem.");
        }

        authService.revokeAllTokens(usuario);
        favoritoRepository.findByUsuarioOrderByDataFavoritoDesc(usuario).forEach(favoritoRepository::delete);
        avaliacaoRepository.findByUsuarioOrderByDataAvaliacaoDesc(usuario).forEach(item -> {
            EntityFields.set(item, "usuario", null);
            EntityFields.set(item, "comentario", null);
            avaliacaoRepository.save(item);
        });
        precoRepository.findAll().stream()
                .filter(item -> usuario.equals(EntityFields.get(item, "usuario", Usuario.class)))
                .forEach(item -> {
                    EntityFields.set(item, "usuario", null);
                    precoRepository.save(item);
                });
        bebidaRepository.findAll().stream()
                .filter(item -> usuario.equals(EntityFields.get(item, "criadoPor", Usuario.class)))
                .forEach(item -> {
                    EntityFields.set(item, "criadoPor", null);
                    bebidaRepository.save(item);
                });

        String anonymousId = "usuario_excluido_" + usuario.getIdUsuario();
        EntityFields.set(usuario, "nome", "Usuario excluido");
        EntityFields.set(usuario, "nomeUsuario", anonymousId);
        EntityFields.set(usuario, "email", anonymousId + "@anonimo.example.com");
        EntityFields.set(usuario, "senhaHash", "anonimizado");
        EntityFields.set(usuario, "dataNascimento", null);
        EntityFields.set(usuario, "confirmouMaioridade", false);
        EntityFields.set(usuario, "emailVerificado", false);
        EntityFields.set(usuario, "ativo", false);
        EntityFields.set(usuario, "marketingConsentimento", false);
        EntityFields.set(usuario, "marketingConsentimentoEm", null);
        EntityFields.set(usuario, "anonimizadoEm", LocalDateTime.now(ZoneOffset.UTC));
        usuarioRepository.save(usuario);
        return Map.of("detail", "Conta anonimizada e desativada com sucesso.");
    }

    private static Set<String> selectExportCategories(String categories) {
        Set<String> selected = Arrays.stream((categories == null ? "" : categories).split(","))
                .map(String::trim)
                .map(String::toLowerCase)
                .filter(item -> !item.isBlank())
                .filter(ALLOWED_EXPORT_CATEGORIES::contains)
                .collect(Collectors.toCollection(LinkedHashSet::new));
        if (selected.isEmpty()) {
            throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "Selecione pelo menos uma categoria valida.");
        }
        return selected;
    }

    private static Integer id(Bebida bebida) {
        return bebida == null ? null : bebida.getIdBebida();
    }

    private static String value(Object value) {
        return value == null ? "" : value.toString();
    }

    private static void row(StringBuilder csv, String category, Object field, Object value) {
        csv.append(escape(category)).append(',')
                .append(escape(value(field))).append(',')
                .append(escape(value(value))).append('\n');
    }

    private static String escape(String value) {
        if (value.contains(",") || value.contains("\"") || value.contains("\n")) {
            return "\"" + value.replace("\"", "\"\"") + "\"";
        }
        return value;
    }
}
