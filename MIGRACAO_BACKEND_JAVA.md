# Migracao Completa Do Backend Para Java

Este documento descreve o que deve ser feito para refatorar/migrar o backend atual em Python/FastAPI para Java/Spring Boot, preservando os contratos usados pelo app mobile e evitando quebrar o sistema em producao/testes.

Backend atual de referencia: `backend/`.

Backend Java iniciado: `backend-java/`.

Stack recomendada:

- Java 21
- Spring Boot 3
- Spring Web
- Spring Security
- Spring Data JPA
- Bean Validation
- PostgreSQL
- Flyway
- Actuator
- Maven

## Objetivo

Migrar a API Python para Java mantendo:

- Mesmos endpoints publicos usados pelo app mobile.
- Mesmo banco de dados PostgreSQL, tabelas e nomes de colunas.
- Mesmo comportamento de autenticacao, LGPD, busca, favoritos, avaliacoes, precos e e-mails.
- Compatibilidade com Cloudflare Tunnel, Resend e Open Food Facts.
- Logs estruturados com mascaramento de dados sensiveis.

## Estrategia Segura De Migracao

1. Manter o backend Python funcionando como referencia.
2. Evoluir `backend-java/` em paralelo.
3. Migrar endpoint por endpoint.
4. Criar testes de contrato comparando respostas Python vs Java.
5. Apontar o app mobile para Java apenas quando os endpoints principais estiverem equivalentes.
6. Fazer troca definitiva somente depois de validar auth, LGPD, busca e reset de senha.

## Ordem Recomendada

1. Base Java: config, properties, CORS, logs, exceptions e health.
2. Banco: entidades JPA, repositories e Flyway.
3. Seguranca: senha, JWT, refresh token, usuario logado.
4. Auth: cadastro, login, refresh, logout, alterar senha e reset.
5. Perfil/LGPD: status, aceite, exportacao CSV e anonimizar conta.
6. Bebidas: criar, editar, buscar por codigo e buscar por nome.
7. Favoritos, avaliacoes e precos.
8. Integracoes externas: Open Food Facts e Resend.
9. Admin.
10. Web app HTML, ou decisao formal de remover/manter separado.
11. QA, Docker, documentacao e corte final.

## Estrutura Java Recomendada

```text
backend-java/
  src/main/java/br/com/bebidasscan/api/
    BebidasScanApiApplication.java
    admin/
    auth/
    avaliacao/
    bebida/
    common/
    config/
    email/
    favorito/
    lgpd/
    observability/
    openfoodfacts/
    perfil/
    preco/
    privacidade/
    security/
    usuario/
    web/
  src/main/resources/
    application.yml
    db/migration/
  src/test/java/br/com/bebidasscan/api/
```

Pacotes novos sugeridos:

- `common`: erros padronizados, DTOs comuns, utilitarios de data, sanitizacao e CSV.
- `security`: JWT, hash de senha, filtro de autenticacao e usuario logado.
- `observability`: logs JSON, requestId, filtros HTTP e mascaramento.
- `email`: cliente Resend e templates de e-mail.
- `openfoodfacts`: cliente externo e mapeamento dos produtos.
- `lgpd`: regras de aceite, exportacao, retencao e anonimizacao.
- `web`: apenas se o HTML servido pelo backend continuar existindo.

## Mapeamento Arquivo Por Arquivo

### `backend/app/main.py`

O que faz hoje:

- Cria a aplicacao FastAPI.
- Inicializa tabelas/migracoes leves.
- Configura logging.
- Limpa refresh tokens antigos na inicializacao.
- Configura middleware de tamanho maximo de request.
- Configura middleware de observabilidade com `requestId`.
- Configura CORS.
- Registra routers.
- Serve pagina inicial publica e `/health`.

O que fazer em Java:

- Mover bootstrap para `BebidasScanApiApplication.java`.
- Criar `config/CorsConfig.java` lendo `cors-origins`.
- Criar `observability/RequestLoggingFilter.java` para `requestId`, duracao, status e logs.
- Criar `config/RequestSizeConfig.java` ou filtro equivalente para `MAX_REQUEST_BODY_BYTES`.
- Criar `health/HealthController.java` ou usar Actuator mantendo `/health`.
- Migrar limpeza de refresh tokens para `auth/RefreshTokenCleanupJob.java`, executado no startup com `ApplicationRunner`.
- Nao usar `ddl-auto=update` em producao; preferir Flyway.

Classes Java alvo:

- `BebidasScanApiApplication`
- `config/CorsConfig`
- `observability/RequestContextFilter`
- `observability/RequestLoggingFilter`
- `common/RequestSizeFilter`
- `auth/RefreshTokenCleanupJob`
- `health/HealthController`

### `backend/app/database.py`

O que faz hoje:

- Le `DATABASE_URL`.
- Cria engine SQLAlchemy.
- Cria `SessionLocal`.
- Expoe `get_db()`.

O que fazer em Java:

- Configurar datasource em `application.yml`.
- Usar Spring Data JPA e injecao de repositories.
- Remover conceito manual de sessao por request; deixar transacoes com `@Transactional`.
- Padronizar `spring.jpa.hibernate.ddl-auto=validate`.

Classes/arquivos Java alvo:

- `src/main/resources/application.yml`
- repositories em cada pacote de dominio
- services com `@Transactional`

### `backend/app/models.py`

O que faz hoje:

- Define tabelas `usuario`, `refresh_token`, `password_reset_token`, `bebida`, `cachaca`, `avaliacao`, `favorito`, `preco`.

O que fazer em Java:

- Conferir se as entidades ja criadas em `backend-java` batem 1:1 com nomes de tabelas, colunas, nullable, unique, indices e relacionamentos.
- Corrigir tipos:
  - `Numeric` -> `BigDecimal`
  - `DateTime` -> `LocalDateTime`
  - `Date` -> `LocalDate`
  - `Text` -> `String` com `@Column(columnDefinition = "text")` quando necessario.
- Mapear relacionamentos `@ManyToOne`, `@OneToOne`, `@JoinColumn`.
- Manter nomes de colunas iguais aos atuais para reaproveitar o banco.

Classes Java alvo ja iniciadas:

- `usuario/Usuario.java`
- `auth/RefreshToken.java`
- `auth/PasswordResetToken.java`
- `bebida/Bebida.java`
- `bebida/Cachaca.java`
- `avaliacao/Avaliacao.java`
- `favorito/Favorito.java`
- `preco/Preco.java`

### `backend/app/schemas.py`

O que faz hoje:

- Define DTOs Pydantic de entrada e saida.
- Valida email, senha forte, limites de tamanho, nota, preco e campos de cachaca.

O que fazer em Java:

- Criar DTOs Java `record` por fluxo, separados das entidades JPA.
- Usar Bean Validation:
  - `@NotBlank`
  - `@Size`
  - `@Email`
  - `@Min`
  - `@Max`
  - `@DecimalMin`
  - `@Past`
- Criar validacao customizada para senha forte.
- Criar mappers manuais ou MapStruct. Para manter o projeto simples, comecar com mappers manuais.

Classes Java alvo:

- `auth/dto/UsuarioCreateRequest`
- `auth/dto/UsuarioLoginRequest`
- `auth/dto/TokenResponse`
- `auth/dto/AccessTokenResponse`
- `auth/dto/RefreshRequest`
- `auth/dto/AlterarSenhaRequest`
- `auth/dto/SolicitarResetSenhaRequest`
- `auth/dto/ConfirmarResetSenhaRequest`
- `usuario/dto/UsuarioResponse`
- `perfil/dto/LgpdAceiteRequest`
- `perfil/dto/ExclusaoContaRequest`
- `perfil/dto/LgpdStatusResponse`
- `bebida/dto/BebidaCreateRequest`
- `bebida/dto/BebidaUpdateRequest`
- `bebida/dto/BebidaResponse`
- `bebida/dto/CachacaRequest`
- `bebida/dto/CachacaResponse`
- `avaliacao/dto/AvaliacaoCreateRequest`
- `avaliacao/dto/AvaliacaoResponse`
- `favorito/dto/FavoritoResponse`
- `preco/dto/PrecoCreateRequest`
- `preco/dto/PrecoResponse`

### `backend/app/security.py`

O que faz hoje:

- Valida variaveis JWT.
- Gera/verifica hash de senha com Argon2.
- Cria e verifica access token JWT.
- Gera refresh token seguro.
- Cria hash SHA-256 de refresh/reset tokens.
- Calcula expiracao.

O que fazer em Java:

- Adicionar dependencia para JWT, por exemplo `com.auth0:java-jwt` ou `io.jsonwebtoken`.
- Adicionar suporte a Argon2 via Spring Security `Argon2PasswordEncoder`.
- Criar servico de JWT.
- Criar servico de tokens opacos.
- Validar configuracao no startup.

Classes Java alvo:

- `security/PasswordService`
- `security/JwtService`
- `security/TokenHashService`
- `security/SecurityPropertiesValidator`

### `backend/app/dependencies.py`

O que faz hoje:

- Extrai bearer token.
- Valida access token.
- Busca usuario ativo.
- Preenche `userId` no contexto de log.

O que fazer em Java:

- Criar filtro `OncePerRequestFilter` para autenticar JWT.
- Criar `CurrentUser`/principal autenticado.
- Criar anotacao/helper para recuperar usuario logado nos controllers.
- Garantir que `userId` entre no MDC dos logs e seja removido no fim da request.

Classes Java alvo:

- `security/JwtAuthenticationFilter`
- `security/AuthenticatedUser`
- `security/CurrentUserService`
- `observability/MdcCleanupFilter`

### `backend/app/logging_config.py`

O que faz hoje:

- Configura logs JSON.
- Mascara campos sensiveis.
- Usa `requestId` e `userId`.
- Separa logger app/security.

O que fazer em Java:

- Usar Logback com encoder JSON.
- Criar filtro para popular MDC com `requestId` e `userId`.
- Criar utilitario de sanitizacao para logs de dominio.
- Padronizar niveis `info`, `warn`, `error`, `fatal`.
- Garantir que senha, tokens, CPF, e-mail e secrets nunca sejam logados em claro.

Arquivos/classes Java alvo:

- `src/main/resources/logback-spring.xml`
- `observability/LogSanitizer`
- `observability/StructuredLogger`
- `observability/RequestContextFilter`

### `backend/app/rate_limit.py`

O que faz hoje:

- Aplica rate limit em memoria para autenticacao.
- Bloqueia tentativas excessivas por janela.

O que fazer em Java:

- Implementar equivalente inicialmente em memoria com Caffeine Cache.
- Separar chaves por IP, acao e identidade.
- No futuro, trocar para Redis se houver multiplas instancias.

Classes Java alvo:

- `security/RateLimitService`
- `security/AuthLockoutService`

### `backend/app/validacao.py`

O que faz hoje:

- Normaliza e valida e-mail.
- Valida senha forte com maiuscula, minuscula, numero e caractere especial.

O que fazer em Java:

- Criar validadores Bean Validation customizados.
- Garantir as mesmas mensagens de erro para nao quebrar app mobile.

Classes Java alvo:

- `common/validation/StrongPassword`
- `common/validation/StrongPasswordValidator`
- `common/validation/EmailNormalizer`

### `backend/app/usernames.py`

O que faz hoje:

- Normaliza/valida nome de usuario.

O que fazer em Java:

- Criar utilitario de normalizacao.
- Aplicar em cadastro web/mobile e admin.
- Garantir unicidade por repository.

Classe Java alvo:

- `usuario/UsernameService`

### `backend/app/tipos_bebida.py`

O que faz hoje:

- Decide se uma bebida tambem deve ter dados de cachaca/aguardente.

O que fazer em Java:

- Criar enum/servico de classificacao de tipo.
- Usar em cadastro, edicao e mapeamento de Open Food Facts.

Classe Java alvo:

- `bebida/TipoBebidaService`

### `backend/app/lgpd.py`

O que faz hoje:

- Versao dos documentos LGPD.
- Calcula maioridade.
- Verifica aceite pendente.
- Registra aceite.
- Anonimiza usuario.
- Limpa refresh tokens antigos.
- Exporta dados em CSV.
- Gera texto de Politica de Privacidade e Termos.

O que fazer em Java:

- Separar regra, exportacao e textos legais.
- Usar `@Transactional` na anonimizacao.
- Garantir ordem de anonimizacao:
  - revogar tokens
  - apagar favoritos
  - desvincular/limpar avaliacoes
  - desvincular precos
  - desvincular bebidas criadas
  - anonimizar usuario
- Criar exportacao CSV com escaping correto.
- Manter versao `2026-07-14` ate decisao contraria.

Classes Java alvo:

- `lgpd/LgpdService`
- `lgpd/LgpdDocumentService`
- `lgpd/UserDataExportService`
- `lgpd/AccountAnonymizationService`
- `lgpd/RefreshTokenRetentionService`

### `backend/app/email_service.py`

O que faz hoje:

- Envia e-mails via Resend.
- Gera templates HTML:
  - boas-vindas
  - reset de senha
  - senha alterada
  - senha redefinida
- Falha sem quebrar o fluxo quando Resend nao esta configurado.

O que fazer em Java:

- Criar cliente Resend com `WebClient` ou `RestClient`.
- Criar templates simples em classes Java ou usar Thymeleaf apenas se o volume crescer.
- Manter comportamento seguro: erro de e-mail nao pode vazar token nem senha em log.
- Manter logs de falha com `action=email.tipo`.

Classes Java alvo:

- `email/ResendClient`
- `email/TransactionalEmailService`
- `email/EmailTemplateService`
- `email/EmailNotConfiguredException`

### `backend/app/open_food_facts.py`

O que faz hoje:

- Consulta Open Food Facts.
- Mapeia retorno externo para bebida.
- Lida com dados incompletos e dados em portugues/brasil quando possivel.

O que fazer em Java:

- Criar cliente HTTP com timeout.
- Configurar `User-Agent`.
- Priorizar endpoints/parametros de lingua/pais quando aplicavel.
- Mapear somente campos usados pelo app.
- Tratar erro externo sem derrubar a busca local.

Classes Java alvo:

- `openfoodfacts/OpenFoodFactsClient`
- `openfoodfacts/OpenFoodFactsMapper`
- `openfoodfacts/OpenFoodFactsProperties`

### `backend/app/migrations.py`

O que faz hoje:

- Aplica migracoes leves em runtime.
- Cria/ajusta colunas e tabelas conforme evolucao do projeto.
- Migra dados antigos de cachaca para tabela `cachaca`.

O que fazer em Java:

- Parar de migrar schema no startup da aplicacao.
- Converter cada alteracao para Flyway SQL.
- Criar baseline a partir do schema atual.
- Validar em banco limpo e banco existente.

Arquivos Java alvo:

- `src/main/resources/db/migration/V1__baseline_schema.sql`
- `src/main/resources/db/migration/V2__lgpd_fields.sql`
- `src/main/resources/db/migration/V3__password_reset_token.sql`
- `src/main/resources/db/migration/V4__cachaca_table.sql`

### `backend/app/routes_auth.py`

O que faz hoje:

- `POST /auth/registrar`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `POST /auth/alterar-senha`
- `POST /auth/solicitar-reset-senha`
- `POST /auth/confirmar-reset-senha`
- Agenda e-mails transacionais.

O que fazer em Java:

- Criar `AuthController`.
- Delegar regra para `AuthService`.
- Manter DTOs e respostas compativeis.
- Adicionar testes de contrato para todos os fluxos.

Classes Java alvo:

- `auth/AuthController`
- `auth/AuthService`
- `auth/RefreshTokenService`
- `auth/PasswordResetService`

### `backend/app/services/auth_service.py`

O que faz hoje:

- Cadastro.
- Login com e-mail ou nome de usuario.
- Emissao/renovacao/revogacao de tokens.
- Logout.
- Alteracao de senha.
- Solicitar e confirmar reset de senha.
- Rate limit.
- LGPD no cadastro.

O que fazer em Java:

- Migrar regra para `AuthService`.
- Separar responsabilidades:
  - `RegistrationService`
  - `LoginService`
  - `RefreshTokenService`
  - `PasswordResetService`
  - `PasswordChangeService`
- Manter transacoes atomicas.
- Nao enviar e-mail dentro da transacao principal se isso puder atrasar resposta; usar evento async depois do commit quando possivel.

### `backend/app/routes_perfil.py`

O que faz hoje:

- `GET /perfil/me`
- `GET /perfil/lgpd/status`
- `POST /perfil/lgpd/aceitar`
- `GET /perfil/exportar.csv`
- `POST /perfil/anonimizar`

O que fazer em Java:

- Criar `PerfilController`.
- Usar usuario autenticado.
- Retornar CSV com headers corretos.
- Confirmar email/senha antes da anonimizacao.

Classes Java alvo:

- `perfil/PerfilController`
- `perfil/PerfilService`
- `lgpd/LgpdService`
- `lgpd/UserDataExportService`
- `lgpd/AccountAnonymizationService`

### `backend/app/services/perfil_service.py`

O que faz hoje:

- Implementa status LGPD, aceite, exportacao e anonimizacao para app mobile/API.

O que fazer em Java:

- Migrar para `PerfilService`, chamando servicos LGPD especializados.
- Garantir `@Transactional` no aceite e anonimizacao.
- Preservar mensagens de erro usadas pelo mobile.

### `backend/app/routes_privacidade.py`

O que faz hoje:

- `GET /privacidade/politica`
- `GET /privacidade/termos`

O que fazer em Java:

- Criar `PrivacidadeController`.
- Retornar texto puro ou JSON conforme contrato atual.
- Usar `LgpdDocumentService`.

Classes Java alvo:

- `privacidade/PrivacidadeController`
- `lgpd/LgpdDocumentService`

### `backend/app/services/privacidade_service.py`

O que faz hoje:

- Entrega texto da politica e dos termos.

O que fazer em Java:

- Migrar para `LgpdDocumentService`.
- Considerar mover textos longos para arquivos `.md` ou `.txt` em `resources/legal/`.

### `backend/app/routes_bebidas.py`

O que faz hoje:

- `POST /bebidas`
- `PATCH /bebidas/{id_bebida}`
- `GET /bebidas/codigo/{codigo_barras}`
- `GET /bebidas/buscar?q=...`

O que fazer em Java:

- Criar `BebidaController`.
- Manter mesmas rotas.
- Preservar busca local + externa.
- Preservar criador da bebida via usuario autenticado.
- Preservar regras de cachaca separada.

Classes Java alvo:

- `bebida/BebidaController`
- `bebida/BebidaService`
- `bebida/BebidaMapper`
- `bebida/TipoBebidaService`
- `openfoodfacts/OpenFoodFactsClient`

### `backend/app/services/bebida_service.py`

O que faz hoje:

- Cria bebida.
- Atualiza bebida.
- Busca por codigo local e Open Food Facts.
- Busca por nome local e externo.
- Normaliza resposta externa.
- Garante relacao `Bebida`/`Cachaca`.

O que fazer em Java:

- Migrar regra para `BebidaService`.
- Criar queries especificas nos repositories.
- Usar `Pageable`/`Limit` para evitar buscas gigantes.
- Fazer deduplicacao por codigo de barras e nome.
- Garantir que falha da API externa nao quebre busca local.

### `backend/app/routes_avaliacoes.py`

O que faz hoje:

- `POST /avaliacoes`
- `GET /avaliacoes/minhas`

O que fazer em Java:

- Criar `AvaliacaoController`.
- Usar `AvaliacaoService`.
- Manter restricao de uma avaliacao por usuario/bebida.

Classes Java alvo:

- `avaliacao/AvaliacaoController`
- `avaliacao/AvaliacaoService`
- `avaliacao/AvaliacaoRepository`

### `backend/app/services/avaliacao_service.py`

O que faz hoje:

- Cria/atualiza avaliacao do usuario.
- Lista avaliacoes do usuario.

O que fazer em Java:

- Migrar para `AvaliacaoService`.
- Implementar upsert seguro ou atualizar se ja existir.
- Tratar violacao de constraint com mensagem amigavel.

### `backend/app/routes_favoritos.py`

O que faz hoje:

- `GET /favoritos`
- `POST /favoritos/{id_bebida}`
- `DELETE /favoritos/{id_bebida}`

O que fazer em Java:

- Criar `FavoritoController`.
- Usar `FavoritoService`.
- Manter idempotencia onde fizer sentido.

Classes Java alvo:

- `favorito/FavoritoController`
- `favorito/FavoritoService`

### `backend/app/services/favorito_service.py`

O que faz hoje:

- Lista favoritos.
- Adiciona favorito.
- Remove favorito.

O que fazer em Java:

- Migrar para `FavoritoService`.
- Evitar duplicidade por `id_usuario` + `id_bebida`.
- Decidir se favoritar item ja favorito retorna existente ou erro.

### `backend/app/routes_precos.py`

O que faz hoje:

- `POST /precos`
- `GET /precos/bebida/{id_bebida}`

O que fazer em Java:

- Criar `PrecoController`.
- Usar `PrecoService`.
- Validar preco >= 0.

Classes Java alvo:

- `preco/PrecoController`
- `preco/PrecoService`

### `backend/app/services/preco_service.py`

O que faz hoje:

- Registra preco.
- Lista precos de uma bebida.

O que fazer em Java:

- Migrar para `PrecoService`.
- Usar `BigDecimal` para valor.
- Manter usuario nullable para dados anonimizados.

### `backend/app/routes_admin.py`

O que faz hoje:

- Painel admin HTML com Basic Auth.
- Dashboard.
- Usuarios.
- Bebidas.
- Avaliacoes.
- Favoritos.
- Precos.
- Acoes administrativas de status, email verificado, revogar tokens e exclusoes.

O que fazer em Java:

- Decidir se o admin HTML continua no backend Java ou vira ferramenta separada.
- Se continuar:
  - Criar `AdminController`.
  - Usar Thymeleaf ou HTML manual.
  - Implementar Basic Auth separado de JWT.
  - Manter CSRF em formularios.
- Se nao continuar:
  - Criar apenas endpoints JSON administrativos.

Classes Java alvo:

- `admin/AdminController`
- `admin/AdminService`
- `admin/AdminSecurityConfig`
- `admin/AdminViewService` ou templates Thymeleaf

### `backend/app/services/admin_service.py`

O que faz hoje:

- Regras administrativas para usuarios, bebidas, avaliacoes, favoritos e precos.
- Metricas do dashboard.
- Atividade recente.
- Revogacao de tokens.

O que fazer em Java:

- Migrar para `AdminService`.
- Separar consultas de dashboard em `AdminDashboardService`.
- Criar projections/DTOs para evitar carregar dados demais.

### `backend/app/routes_web.py`

O que faz hoje:

- Web app HTML em `/web`.
- Login/cadastro web.
- LGPD web.
- Scanner web.
- CRUD parcial de bebidas.
- Favoritos e avaliacoes web.
- Logout e cookies.

O que fazer em Java:

- Decidir formalmente entre tres opcoes:
  1. Migrar para Thymeleaf no Spring Boot.
  2. Transformar em frontend separado.
  3. Remover/pausar web app e manter apenas API + pagina reset.
- Se migrar:
  - Criar `web/WebController`.
  - Criar templates Thymeleaf.
  - Implementar cookie auth ou reutilizar JWT.
  - Manter CSRF.
- Como o site esta em segundo plano, deixar para a ultima fase.

Classes Java alvo:

- `web/WebController`
- `web/WebAuthService`
- `web/WebViewService` ou templates

### `backend/app/services/web_service.py`

O que faz hoje:

- Reaproveita regras de auth, LGPD, bebida, favorito e avaliacao para o web app.

O que fazer em Java:

- Migrar somente se `/web` continuar existindo.
- Evitar duplicar regra: web deve chamar os mesmos services usados pela API mobile.

### `backend/app/routes_password_reset.py`

O que faz hoje:

- Pagina publica separada em `/resetar-senha`.
- Recebe token por query string.
- Valida nova senha.
- Confirma reset.
- Mostra botao para voltar ao login.
- Mantem redirect legado de `/web/resetar-senha`.

O que fazer em Java:

- Criar controller publico de reset.
- Manter `/resetar-senha`.
- Manter compatibilidade com `/web/resetar-senha` se links antigos existirem.
- Usar template HTML simples ou Thymeleaf.

Classes Java alvo:

- `auth/PasswordResetPageController`
- `auth/PasswordResetService`

### `backend/app/views/web_views.py`

O que faz hoje:

- Gera HTML do web app.

O que fazer em Java:

- Se migrar web app para Java, transformar em templates Thymeleaf.
- Se web app for removido, arquivar como referencia e remover rotas `/web`.

Arquivos Java alvo:

- `src/main/resources/templates/web/*.html`
- `src/main/resources/static/web/*`

### `backend/app/views/admin_views.py`

O que faz hoje:

- Gera HTML do painel admin.

O que fazer em Java:

- Se manter admin HTML, migrar para Thymeleaf.
- Separar layout, tabelas e formularios.
- Manter escaping automatico do template engine.

Arquivos Java alvo:

- `src/main/resources/templates/admin/*.html`
- `src/main/resources/static/admin/*`

### `backend/app/controllers/*.py`

O que faz hoje:

- Reexporta routers Python para compor a camada MVC.

O que fazer em Java:

- Substituir por controllers reais anotados com `@RestController` ou `@Controller`.
- Cada controller deve ter responsabilidade clara:
  - receber request
  - validar DTO
  - chamar service
  - retornar response
- Nao colocar regra de negocio nos controllers.

Classes Java alvo:

- `auth/AuthController`
- `bebida/BebidaController`
- `avaliacao/AvaliacaoController`
- `favorito/FavoritoController`
- `preco/PrecoController`
- `perfil/PerfilController`
- `privacidade/PrivacidadeController`
- `admin/AdminController`
- `web/WebController`, se mantido

### `backend/app/__init__.py`, `services/__init__.py`, `views/__init__.py`

O que faz hoje:

- Marca pacotes Python.

O que fazer em Java:

- Nao migrar. Java usa packages por diretorio e declaracao `package`.

### `backend/requirements.txt`

O que faz hoje:

- Lista dependencias Python.

O que fazer em Java:

- Migrar dependencias para `backend-java/pom.xml`.
- Depois da troca definitiva, manter apenas se o backend Python continuar como legado.

Dependencias Maven provaveis:

- `spring-boot-starter-web`
- `spring-boot-starter-security`
- `spring-boot-starter-data-jpa`
- `spring-boot-starter-validation`
- `spring-boot-starter-actuator`
- `postgresql`
- `flyway-core`
- biblioteca JWT
- `caffeine`, se rate limit em memoria
- `logstash-logback-encoder`, se logs JSON via Logback
- `spring-boot-starter-webflux`, se usar `WebClient`

### `backend/Dockerfile`

O que faz hoje:

- Builda container Python/FastAPI.

O que fazer em Java:

- Usar `backend-java/Dockerfile`.
- Ajustar `docker-compose.yml` para buildar `backend-java`.
- Expor porta Java ou manter porta externa `8000` apontando para porta interna Java.

### `backend/.env.example`

O que faz hoje:

- Documenta variaveis do backend Python.

O que fazer em Java:

- Espelhar variaveis em `backend-java/.env.example`.
- Manter nomes atuais para reduzir impacto operacional.

### `backend/tests/*.py`

O que faz hoje:

- Testa seguranca basica e Open Food Facts.

O que fazer em Java:

- Recriar testes em JUnit/MockMvc.
- Criar testes de contrato para endpoints principais.
- Adicionar testes de servico para auth, LGPD e bebidas.

Arquivos Java alvo:

- `src/test/java/.../auth/AuthControllerTest.java`
- `src/test/java/.../auth/AuthServiceTest.java`
- `src/test/java/.../bebida/BebidaControllerTest.java`
- `src/test/java/.../openfoodfacts/OpenFoodFactsClientTest.java`
- `src/test/java/.../perfil/PerfilControllerTest.java`
- `src/test/java/.../security/SecurityBasicsTest.java`

## O Que Ja Existe Em `backend-java/`

Arquivos ja iniciados:

- `pom.xml`
- `Dockerfile`
- `src/main/resources/application.yml`
- `BebidasScanApiApplication.java`
- `config/BebidasScanProperties.java`
- `config/SecurityConfig.java`
- `health/HealthController.java`
- Entidades JPA:
  - `Usuario`
  - `RefreshToken`
  - `PasswordResetToken`
  - `Bebida`
  - `Cachaca`
  - `Avaliacao`
  - `Favorito`
  - `Preco`
- Repositories para as entidades principais.
- Teste inicial de healthcheck.

Proximos passos nesse backend iniciado:

1. Conferir entidades JPA contra `models.py`.
2. Adicionar DTOs de `schemas.py`.
3. Implementar `SecurityConfig` real com JWT.
4. Implementar `AuthController` e `AuthService`.
5. Implementar `PerfilController` e LGPD.
6. Implementar `BebidaController` e busca por codigo/nome.
7. Migrar demais endpoints.

## Contratos Que Nao Podem Quebrar

Endpoints usados pelo app mobile:

- `POST /auth/registrar`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `POST /auth/alterar-senha`
- `POST /auth/solicitar-reset-senha`
- `POST /auth/confirmar-reset-senha`
- `GET /perfil/me`
- `GET /perfil/lgpd/status`
- `POST /perfil/lgpd/aceitar`
- `GET /perfil/exportar.csv`
- `POST /perfil/anonimizar`
- `GET /privacidade/politica`
- `GET /privacidade/termos`
- `GET /bebidas/codigo/{codigo_barras}`
- `GET /bebidas/buscar?q=...`
- `POST /bebidas`
- `PATCH /bebidas/{id_bebida}`
- `POST /avaliacoes`
- `GET /avaliacoes/minhas`
- `GET /favoritos`
- `POST /favoritos/{id_bebida}`
- `DELETE /favoritos/{id_bebida}`
- `POST /precos`
- `GET /precos/bebida/{id_bebida}`
- `GET /health`

Campos de resposta importantes:

- `access_token`
- `refresh_token`
- `token_type`
- `usuario`
- `id_usuario`
- `nome_usuario`
- `email`
- `pendente`
- `versao_atual`
- `id_bebida`
- `codigo_barras`
- `cachaca`

## Checklist De Implementacao Java

### Fase 1 - Base

- [ ] Validar `pom.xml`.
- [ ] Definir Java 21.
- [ ] Configurar `application.yml`.
- [ ] Configurar profiles `dev`, `test`, `prod`.
- [ ] Configurar CORS.
- [ ] Configurar Actuator.
- [ ] Configurar erro padronizado.
- [ ] Configurar logs JSON.
- [ ] Configurar filtros de requestId/userId.

### Fase 2 - Banco

- [ ] Revisar entidades JPA.
- [ ] Criar migrations Flyway.
- [ ] Criar repositories faltantes.
- [ ] Criar testes de schema.
- [ ] Garantir `ddl-auto=validate`.

### Fase 3 - Seguranca/Auth

- [ ] Hash Argon2.
- [ ] JWT access token.
- [ ] Refresh token opaco.
- [ ] Rate limit.
- [ ] Usuario autenticado.
- [ ] Cadastro.
- [ ] Login.
- [ ] Refresh.
- [ ] Logout.
- [ ] Alterar senha.
- [ ] Solicitar reset.
- [ ] Confirmar reset.

### Fase 4 - LGPD/Perfil

- [ ] Perfil `/perfil/me`.
- [ ] Status LGPD.
- [ ] Aceite LGPD.
- [ ] Exportacao CSV.
- [ ] Anonimizacao com email/senha.
- [ ] Retencao de refresh tokens.
- [ ] Politica e termos.

### Fase 5 - Bebidas

- [ ] Criar bebida.
- [ ] Atualizar bebida.
- [ ] Separar dados de cachaca.
- [ ] Buscar por codigo local.
- [ ] Consultar Open Food Facts por codigo.
- [ ] Buscar por nome local.
- [ ] Consultar Open Food Facts por nome.
- [ ] Deduplicar resultados.

### Fase 6 - Funcionalidades Sociais

- [ ] Avaliacoes.
- [ ] Favoritos.
- [ ] Precos.
- [ ] Regras de duplicidade.
- [ ] Regras de usuario anonimizado.

### Fase 7 - Admin/Web

- [ ] Decidir futuro do `/web`.
- [ ] Migrar pagina `/resetar-senha`.
- [ ] Migrar admin HTML ou criar API admin JSON.
- [ ] Implementar Basic Auth/admin.
- [ ] Implementar CSRF se houver HTML com formularios.

### Fase 8 - Infra E Corte

- [ ] Atualizar `docker-compose.yml`.
- [ ] Atualizar Cloudflare para apontar para Java.
- [ ] Atualizar README.
- [ ] Gerar APK apontando para API Java.
- [ ] Rodar QA completo.
- [ ] Manter rollback para FastAPI ate estabilizar.

## Plano De Testes

Testes minimos antes de trocar o app para Java:

- Cadastro com senha forte.
- Cadastro recusando senha fraca.
- Cadastro recusando e-mail invalido.
- Login com nome de usuario.
- Login com e-mail.
- Refresh token.
- Logout.
- Alteracao de senha.
- Recuperacao de senha com Resend desligado.
- Recuperacao de senha com token valido.
- LGPD pendente.
- Aceite LGPD.
- Exportacao CSV.
- Anonimizacao.
- Busca por codigo local.
- Busca por codigo via Open Food Facts.
- Busca por nome local.
- Busca por nome externa.
- Favoritar/desfavoritar.
- Avaliar bebida.
- Registrar preco.
- Healthcheck.
- Logs sem senha/token/e-mail em claro.

## Criterios Para Considerar A Migracao Completa

- App mobile funciona sem alteracao de fluxo, apenas mudando `API_BASE_URL`.
- Todos os endpoints listados retornam status e JSON compativeis.
- Banco existente sobe com `ddl-auto=validate`.
- Testes Java passam.
- Logs estruturados estao ativos.
- Resend envia e-mails.
- Open Food Facts funciona com timeout e fallback.
- LGPD esta funcional no app.
- Docker/Cloudflare funcionam com a API Java.
- Existe plano de rollback para voltar ao backend Python.

## Riscos Principais

- Divergencia de nomes de campos JSON entre Pydantic e Jackson.
- Diferenca de formato de datas.
- Diferenca no hash de senha Argon2.
- JWT incompativel com tokens emitidos pelo backend Python.
- Migração Flyway alterando banco existente indevidamente.
- CORS/Cloudflare quebrando app mobile.
- E-mail de reset usando URL errada.
- Open Food Facts retornando dados diferentes por pais/lingua.
- Admin/web demorando mais que a API mobile.

## Recomendacao Final

Nao fazer a troca em um unico passo. A migracao deve ser incremental:

1. Java sobe em porta separada.
2. Endpoints sao migrados e testados por grupos.
3. Mobile de teste aponta para Java.
4. Cloudflare pode expor um subdominio temporario, por exemplo `java-api.bebidasscan.com.br`.
5. Depois de aprovado, `api.bebidasscan.com.br` passa para o backend Java.
6. FastAPI fica disponivel como rollback por alguns dias.
