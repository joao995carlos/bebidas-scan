# MIGRATION_PLAN - Backend Python Para Java

Documento de planejamento para migrar o backend Python/FastAPI do Bebidas Scan para Java/Spring Boot.

Este arquivo e apenas analitico. Nao contem codigo Java e nao altera a aplicacao atual.

Backend analisado: `backend/`.

Data do plano: 2026-08-06.

## 1. Objetivo Da Migracao

Migrar o backend atual em Python/FastAPI para Java mantendo compatibilidade com:

- app mobile Flutter;
- banco PostgreSQL atual;
- dominio/API publica;
- rotas de autenticacao;
- LGPD;
- busca local e Open Food Facts;
- Resend para e-mails;
- logs estruturados;
- painel admin e web app, se forem mantidos.

## 2. Stack Java Recomendada

- Java 21.
- Spring Boot 3.x.
- Spring Web MVC.
- Spring Security.
- Spring Data JPA.
- Hibernate.
- Bean Validation/Jakarta Validation.
- PostgreSQL JDBC Driver.
- Flyway.
- Actuator.
- Logback com encoder JSON.
- Maven.
- JUnit 5 + Spring Boot Test + MockMvc.

## 3. Endpoints Python Atuais

### Base

| Metodo | Caminho | Origem Python | Objetivo |
|---|---|---|---|
| GET | `/` | `main.py` | Pagina publica de boas-vindas. |
| GET | `/health` | `main.py` | Healthcheck da API. |

### Auth

Prefixo: `/auth`.

| Metodo | Caminho | Schema entrada | Resposta | Regra principal |
|---|---|---|---|---|
| POST | `/auth/registrar` | `UsuarioCreate` | `TokenResposta` | Criar usuario, validar LGPD/maioridade/senha/nome de usuario, emitir tokens e enviar boas-vindas. |
| POST | `/auth/login` | `UsuarioLogin` | `TokenResposta` | Login por e-mail ou nome de usuario, validar senha e emitir tokens. |
| POST | `/auth/refresh` | `RefreshRequest` | `AccessTokenResposta` | Validar refresh token opaco e emitir novo access token. |
| POST | `/auth/logout` | `RefreshRequest` | `dict` | Revogar refresh token. |
| POST | `/auth/alterar-senha` | `AlterarSenhaRequest` | `dict` | Confirmar senha atual, validar nova senha, revogar tokens. |
| POST | `/auth/solicitar-reset-senha` | `SolicitarResetSenhaRequest` | `dict` | Gerar token de reset e enviar e-mail pelo Resend. |
| POST | `/auth/confirmar-reset-senha` | `ConfirmarResetSenhaRequest` | `dict` | Validar token de reset, trocar senha e revogar tokens. |

### Perfil E LGPD

Prefixo: `/perfil`.

| Metodo | Caminho | Schema entrada | Resposta | Regra principal |
|---|---|---|---|---|
| GET | `/perfil/me` | - | `UsuarioResposta` | Retornar usuario autenticado. |
| GET | `/perfil/lgpd/status` | - | `LGPDStatusResposta` | Informar se aceite LGPD esta pendente. |
| POST | `/perfil/lgpd/aceitar` | `LGPDAceiteRequest` | `LGPDStatusResposta` | Registrar aceite de termos/politica, nascimento e marketing. |
| GET | `/perfil/exportar.csv` | query `categorias` | CSV | Exportar dados pessoais por categorias permitidas. |
| POST | `/perfil/anonimizar` | `ExclusaoContaRequest` | `dict` | Confirmar e-mail/senha e anonimizar/desativar conta. |

### Privacidade

Prefixo: `/privacidade`.

| Metodo | Caminho | Resposta | Regra principal |
|---|---|---|---|
| GET | `/privacidade/politica` | `dict` | Retornar texto e versao da Politica de Privacidade. |
| GET | `/privacidade/termos` | `dict` | Retornar texto e versao dos Termos de Uso. |

### Bebidas

Prefixo: `/bebidas`.

| Metodo | Caminho | Schema entrada | Resposta | Regra principal |
|---|---|---|---|---|
| POST | `/bebidas` | `BebidaCreate` | `BebidaResposta` | Criar bebida do usuario e separar dados de cachaca quando aplicavel. |
| PATCH | `/bebidas/{id_bebida}` | `BebidaUpdate` | `BebidaResposta` | Atualizar bebida criada pelo usuario ou por admin. |
| GET | `/bebidas/codigo/{codigo_barras}` | - | `BebidaResposta` | Buscar local; se nao houver, consultar Open Food Facts e salvar. |
| GET | `/bebidas/buscar?q=...` | query `q` | `list[BebidaResposta]` | Buscar por nome local e complementar com Open Food Facts. |

### Avaliacoes

Prefixo: `/avaliacoes`.

| Metodo | Caminho | Schema entrada | Resposta | Regra principal |
|---|---|---|---|---|
| POST | `/avaliacoes` | `AvaliacaoCreate` | `AvaliacaoResposta` | Criar ou atualizar avaliacao do usuario para uma bebida. |
| GET | `/avaliacoes/minhas` | - | `list[AvaliacaoResposta]` | Listar avaliacoes do usuario autenticado. |

### Favoritos

Prefixo: `/favoritos`.

| Metodo | Caminho | Schema entrada | Resposta | Regra principal |
|---|---|---|---|---|
| GET | `/favoritos` | - | `list[FavoritoResposta]` | Listar favoritos do usuario. |
| POST | `/favoritos/{id_bebida}` | - | `FavoritoResposta` | Favoritar bebida; se ja existir, retornar favorito existente. |
| DELETE | `/favoritos/{id_bebida}` | - | `dict` | Remover favorito do usuario. |

### Precos

Prefixo: `/precos`.

| Metodo | Caminho | Schema entrada | Resposta | Regra principal |
|---|---|---|---|---|
| POST | `/precos` | `PrecoCreate` | `PrecoResposta` | Registrar preco de bebida para usuario autenticado. |
| GET | `/precos/bebida/{id_bebida}` | - | `list[PrecoResposta]` | Listar ate 50 precos mais recentes de uma bebida. |

### Reset De Senha HTML

Sem prefixo.

| Metodo | Caminho | Regra principal |
|---|---|---|
| GET | `/resetar-senha` | Exibir formulario publico de redefinicao. |
| POST | `/resetar-senha` | Validar token e nova senha; mostrar retorno em HTML. |
| GET | `/web/resetar-senha` | Rota legada que redireciona para `/resetar-senha`. |

### Web App

Prefixo: `/web`.

| Metodo | Caminho | Regra principal |
|---|---|---|
| GET | `/web` | Redirecionar para `/web/`. |
| GET | `/web/` | Home protegida com busca. |
| GET | `/web/login` | Formulario de login web. |
| POST | `/web/login` | Login web com cookies. |
| GET | `/web/registrar` | Formulario de cadastro web. |
| POST | `/web/registrar` | Cadastro web, aceite LGPD e e-mail boas-vindas. |
| GET | `/web/privacidade` | Politica de Privacidade HTML. |
| GET | `/web/termos` | Termos de Uso HTML. |
| GET | `/web/lgpd/aceitar` | Tela de aceite LGPD pendente. |
| POST | `/web/lgpd/aceitar` | Registrar aceite LGPD via web. |
| GET | `/web/minha-privacidade` | Tela de privacidade do usuario. |
| GET | `/web/minha-privacidade/exportar` | Exportar CSV pela web. |
| POST | `/web/minha-privacidade/anonimizar` | Anonimizar conta via web com e-mail/senha. |
| GET | `/web/logout` | Logout via web. |
| POST | `/web/logout` | Logout via web com CSRF. |
| GET | `/web/scanner` | Scanner web. |
| POST | `/web/buscar-codigo` | Buscar bebida por codigo vindo do scanner/form. |
| GET | `/web/bebidas/nova` | Formulario de bebida. |
| POST | `/web/bebidas/nova` | Criar bebida pela web. |
| GET | `/web/bebidas/{id_bebida}` | Detalhe da bebida. |
| POST | `/web/favoritos/{id_bebida}` | Favoritar pela web. |
| POST | `/web/avaliacoes` | Salvar avaliacao pela web. |
| GET | `/web/favoritos` | Listar favoritos pela web. |
| GET | `/web/minhas-avaliacoes` | Listar avaliacoes pela web. |

### Admin HTML

Prefixo: `/admin`.

| Metodo | Caminho | Regra principal |
|---|---|---|
| GET | `/admin` | Redirecionar para `/admin/`. |
| GET | `/admin/` | Dashboard admin. |
| GET | `/admin/atividade-fragment` | Fragmento HTML de atividade recente. |
| GET | `/admin/usuarios` | Listar usuarios. |
| POST | `/admin/usuarios/{id_usuario}/status` | Ativar/desativar usuario. |
| POST | `/admin/usuarios/{id_usuario}/verificar-email` | Marcar e-mail como verificado. |
| POST | `/admin/usuarios/{id_usuario}/revogar-tokens` | Revogar tokens do usuario. |
| POST | `/admin/usuarios/criar` | Criar usuario pelo admin. |
| POST | `/admin/usuarios/{id_usuario}/excluir` | Excluir usuario e dados vinculados. |
| GET | `/admin/bebidas` | Listar bebidas. |
| GET | `/admin/bebidas/nova` | Formulario de bebida. |
| POST | `/admin/bebidas/nova` | Criar bebida. |
| GET | `/admin/bebidas/{id_bebida}/editar` | Formulario de edicao. |
| POST | `/admin/bebidas/{id_bebida}/editar` | Editar bebida. |
| POST | `/admin/bebidas/{id_bebida}/excluir` | Excluir bebida e vinculos. |
| GET | `/admin/avaliacoes` | Listar avaliacoes. |
| POST | `/admin/avaliacoes/criar` | Criar avaliacao. |
| POST | `/admin/avaliacoes/{id_avaliacao}/excluir` | Excluir avaliacao. |
| GET | `/admin/favoritos` | Listar favoritos. |
| POST | `/admin/favoritos/criar` | Criar favorito. |
| POST | `/admin/favoritos/{id_favorito}/excluir` | Excluir favorito. |
| GET | `/admin/precos` | Listar precos. |
| POST | `/admin/precos/criar` | Criar preco. |
| POST | `/admin/precos/{id_preco}/excluir` | Excluir preco. |

## 4. Modelos De Banco

### `Usuario`

Tabela: `usuario`.

Campos principais:

- `id_usuario`
- `nome`
- `nome_usuario`
- `email`
- `senha_hash`
- `data_nascimento`
- `confirmou_maioridade`
- `email_verificado`
- `ativo`
- `tipo_usuario`
- `privacidade_versao_aceita`
- `termos_versao_aceita`
- `lgpd_aceite_em`
- `marketing_consentimento`
- `marketing_consentimento_em`
- `anonimizado_em`
- `data_criacao`

Equivalente Java:

- Entidade JPA `usuario.Usuario`.
- Repository `UsuarioRepository`.
- DTO de resposta `UsuarioResponse`.

### `RefreshToken`

Tabela: `refresh_token`.

Campos:

- `id_token`
- `id_usuario`
- `token_hash`
- `expiracao`
- `revogado`
- `criado_em`
- `revogado_em`

Equivalente Java:

- Entidade `auth.RefreshToken`.
- Repository `RefreshTokenRepository`.
- Service `RefreshTokenService`.

### `PasswordResetToken`

Tabela: `password_reset_token`.

Campos:

- `id_reset`
- `id_usuario`
- `token_hash`
- `expiracao`
- `usado`
- `usado_em`
- `criado_em`

Equivalente Java:

- Entidade `auth.PasswordResetToken`.
- Repository `PasswordResetTokenRepository`.
- Service `PasswordResetService`.

### `Bebida`

Tabela: `bebida`.

Campos principais:

- `id_bebida`
- `nome`
- `marca`
- `tipo`
- `codigo_barras`
- `teor_alcoolico`
- `volume_ml`
- `ingredientes`
- `imagem_url`
- `nutri_score`
- `nova_grupo`
- `eco_score`
- `alergenos`
- `categorias`
- `quantidade`
- `embalagem`
- `paises`
- campos legados de cachaca na raiz
- `origem_dados`
- `id_criado_por`
- `criada_em`

Equivalente Java:

- Entidade `bebida.Bebida`.
- Repository `BebidaRepository`.
- DTOs `BebidaCreateRequest`, `BebidaUpdateRequest`, `BebidaResponse`.
- Mapper `BebidaMapper`.

### `Cachaca`

Tabela: `cachaca`.

Campos:

- `id_cachaca`
- `id_bebida`
- `volume_ml`
- `classificacao`
- `madeira`
- `tempo_envelhecimento_meses`
- `cidade_origem`
- `estado_origem`
- `regiao_origem`
- `alambique`
- `produtor`
- `lote`
- `criada_em`

Equivalente Java:

- Entidade `bebida.Cachaca`.
- Repository `CachacaRepository`.
- DTOs `CachacaRequest`, `CachacaResponse`.

### `Avaliacao`

Tabela: `avaliacao`.

Campos:

- `id_avaliacao`
- `id_usuario`
- `id_bebida`
- `nota`
- `comentario`
- `compraria_novamente`
- `data_avaliacao`

Constraints:

- nota entre 1 e 5;
- unicidade por usuario + bebida.

Equivalente Java:

- Entidade `avaliacao.Avaliacao`.
- Repository `AvaliacaoRepository`.
- DTOs `AvaliacaoCreateRequest`, `AvaliacaoResponse`.

### `Favorito`

Tabela: `favorito`.

Campos:

- `id_favorito`
- `id_usuario`
- `id_bebida`
- `data_favorito`

Constraint:

- unicidade por usuario + bebida.

Equivalente Java:

- Entidade `favorito.Favorito`.
- Repository `FavoritoRepository`.
- DTO `FavoritoResponse`.

### `Preco`

Tabela: `preco`.

Campos:

- `id_preco`
- `id_usuario`
- `id_bebida`
- `mercado`
- `cidade`
- `estado`
- `valor`
- `data_registro`

Constraint:

- valor maior ou igual a zero.

Equivalente Java:

- Entidade `preco.Preco`.
- Repository `PrecoRepository`.
- DTOs `PrecoCreateRequest`, `PrecoResponse`.

## 5. Schemas Pydantic E DTOs Java

| Schema Python | Uso | Equivalente Java |
|---|---|---|
| `UsuarioCreate` | Cadastro | `auth.dto.UsuarioCreateRequest` |
| `UsuarioLogin` | Login por identificador | `auth.dto.UsuarioLoginRequest` |
| `UsuarioResposta` | Perfil/usuario em tokens | `usuario.dto.UsuarioResponse` |
| `TokenResposta` | Login/cadastro | `auth.dto.TokenResponse` |
| `AccessTokenResposta` | Refresh | `auth.dto.AccessTokenResponse` |
| `RefreshRequest` | Refresh/logout | `auth.dto.RefreshRequest` |
| `AlterarSenhaRequest` | Troca de senha | `auth.dto.ChangePasswordRequest` |
| `SolicitarResetSenhaRequest` | Solicitar reset | `auth.dto.RequestPasswordResetRequest` |
| `ConfirmarResetSenhaRequest` | Confirmar reset | `auth.dto.ConfirmPasswordResetRequest` |
| `LGPDAceiteRequest` | Aceite LGPD | `perfil.dto.LgpdAcceptRequest` |
| `ExclusaoContaRequest` | Anonimizacao | `perfil.dto.AccountDeletionRequest` |
| `LGPDStatusResposta` | Status LGPD | `perfil.dto.LgpdStatusResponse` |
| `CachacaBase/Create/Update` | Dados de cachaca | `bebida.dto.CachacaRequest` |
| `CachacaResposta` | Saida de cachaca | `bebida.dto.CachacaResponse` |
| `BebidaBase/Create/Update` | Criar/editar bebida | `bebida.dto.BebidaCreateRequest`, `BebidaUpdateRequest` |
| `BebidaResposta` | Saida bebida | `bebida.dto.BebidaResponse` |
| `AvaliacaoCreate` | Salvar avaliacao | `avaliacao.dto.AvaliacaoCreateRequest` |
| `AvaliacaoResposta` | Saida avaliacao | `avaliacao.dto.AvaliacaoResponse` |
| `FavoritoResposta` | Saida favorito | `favorito.dto.FavoritoResponse` |
| `PrecoCreate` | Criar preco | `preco.dto.PrecoCreateRequest` |
| `PrecoResposta` | Saida preco | `preco.dto.PrecoResponse` |

Validacoes Java recomendadas:

- `@NotBlank`, `@NotNull`, `@Size`, `@Email`, `@Min`, `@Max`, `@DecimalMin`, `@Past`.
- Validador customizado `@StrongPassword`.
- Normalizadores para e-mail e nome de usuario nos services, nao apenas nos DTOs.

## 6. Regras De Negocio Por Modulo

### `main.py`

Responsabilidades atuais:

- criar app FastAPI;
- criar tabelas SQLAlchemy;
- aplicar migracoes leves;
- configurar logging;
- limpar refresh tokens antigos no startup;
- limitar tamanho de request;
- gerar/propagar `X-Request-ID`;
- logar duracao/status de request;
- configurar CORS;
- registrar routers;
- servir `/` e `/health`.

Migracao Java:

- `BebidasScanApiApplication`;
- `CorsConfig`;
- `RequestSizeFilter`;
- `RequestIdFilter`;
- `StructuredRequestLoggingFilter`;
- `RefreshTokenCleanupRunner`;
- `HealthController`.

### `database.py`

Responsabilidades atuais:

- carregar `.env`;
- exigir `DATABASE_URL`;
- criar engine SQLAlchemy;
- criar sessoes.

Migracao Java:

- `application.yml`;
- Spring `DataSource`;
- Spring Data JPA repositories;
- transacoes com `@Transactional`;
- Flyway para migracoes.

### `dependencies.py`

Responsabilidades atuais:

- validar bearer token;
- decodificar JWT;
- buscar usuario ativo;
- validar admin;
- registrar `userId` no contexto de log.

Migracao Java:

- `JwtAuthenticationFilter`;
- `AuthenticatedUser`;
- `CurrentUserService`;
- `SecurityContext`;
- MDC para `userId`.

### `security.py`

Regras atuais:

- `JWT_SECRET_KEY` obrigatorio com 32+ caracteres;
- algoritmos permitidos: `HS256`, `HS384`, `HS512`;
- access token com `sub`, `email`, `exp`, `type=access`;
- refresh token opaco com `secrets.token_urlsafe(64)`;
- hash SHA-256 para refresh/reset token;
- senha com Argon2 via `pwdlib`.

Migracao Java:

- `JwtService`;
- `PasswordService` com Argon2;
- `OpaqueTokenService`;
- `TokenHashService`.

### `rate_limit.py`

Regras atuais:

- rate limit em memoria por acao, IP e identidade;
- janelas separadas para tentativa geral e por identidade;
- lockout temporario;
- logs de seguranca em falhas.

Migracao Java:

- `RateLimitService` com Caffeine ou Redis;
- `AuthAttemptService`;
- `AuthLockoutService`.

### `validacao.py`

Regras atuais:

- senha deve ter 8+ caracteres, letra maiuscula, numero e caractere especial;
- e-mail e normalizado para lowercase e validado por Pydantic `EmailStr`;
- limite de e-mail em 150 caracteres.

Migracao Java:

- `StrongPasswordValidator`;
- `EmailNormalizer`;
- Bean Validation.

### `usernames.py`

Regras atuais:

- nome de usuario em lowercase;
- remove `@` inicial;
- regex: `^[a-z0-9._-]{3,80}$`;
- slug fallback para nomes.

Migracao Java:

- `UsernameService`;
- `UsernameNormalizer`.

### `tipos_bebida.py`

Regras atuais:

- normaliza acentos e lowercase;
- identifica cachaca/aguardente por regex.

Migracao Java:

- `TipoBebidaService`;
- metodo `isCachacaOrAguardente`.

### `auth_service.py`

Regras atuais:

- cadastro exige aceite da politica e termos;
- cadastro exige maioridade;
- cadastro normaliza nome de usuario;
- bloqueia e-mail/nome de usuario duplicado;
- aplica rate limit no cadastro/login/reset;
- login aceita e-mail ou nome de usuario;
- login exige usuario ativo;
- refresh token precisa existir, nao estar revogado e nao estar expirado;
- logout revoga refresh token;
- troca de senha exige senha atual correta;
- nova senha nao pode ser igual a atual;
- troca/reset revogam tokens;
- reset gera token com validade de 30 minutos;
- reset retorna mensagem generica se e-mail nao existir;
- erros de e-mail viram 503/502;
- eventos de auditoria e seguranca sao logados.

Migracao Java:

- `AuthController`;
- `AuthService`;
- `RegistrationService`;
- `LoginService`;
- `RefreshTokenService`;
- `PasswordResetService`;
- `PasswordChangeService`;
- eventos async para e-mails transacionais.

### `perfil_service.py` E `lgpd.py`

Regras atuais:

- versao LGPD: `2026-07-14`;
- aceite pendente se falta nascimento, maioridade, versao de politica/termos ou data de aceite;
- aceite exige politica e termos;
- aceite exige maioridade;
- marketing e consentimento separado;
- categorias de exportacao permitidas: `perfil`, `avaliacoes`, `favoritos`, `precos`, `bebidas`;
- exportacao CSV por categorias;
- anonimizar exige e-mail e senha;
- anonimizar revoga tokens, apaga favoritos, limpa comentarios de avaliacoes, desvincula precos, desvincula bebidas criadas, desativa usuario e substitui nome/e-mail;
- refresh tokens expirados/revogados sao limpos apos 30 dias;
- textos legais sao gerados no backend.

Migracao Java:

- `LgpdService`;
- `LgpdDocumentService`;
- `UserDataExportService`;
- `AccountAnonymizationService`;
- `RefreshTokenRetentionService`;
- `PerfilController`.

### `bebida_service.py` E `open_food_facts.py`

Regras atuais:

- strings vazias viram `None`;
- dados de cachaca podem vir na raiz por compatibilidade temporaria;
- se tipo nao for cachaca/aguardente, dados de cachaca sao descartados;
- `estado_origem` e convertido para uppercase;
- codigo de barras e unico;
- usuario comum so edita bebida propria;
- admin pode editar qualquer bebida;
- busca por codigo tenta banco local primeiro;
- bebida externa marcada fora do Brasil e ignorada;
- se local for Open Food Facts mas nao Brasil, tenta atualizar via API externa;
- Open Food Facts usa `lc=pt`, `cc=br`, filtro de pais Brasil na busca por nome;
- classifica tipo por categorias externas;
- busca por nome faz busca local com normalizacao sem acentos e complementa com sinonimos externos;
- sinonimos atuais: agua/water, coca/cola, refrigerante/soda, cerveja/beer, suco/juice, energetico/energy drink;
- resultados sao deduplicados por codigo e limitados.

Migracao Java:

- `BebidaController`;
- `BebidaService`;
- `BebidaMapper`;
- `CachacaService`;
- `TipoBebidaService`;
- `OpenFoodFactsClient`;
- `OpenFoodFactsMapper`;
- `OpenFoodFactsProperties`.

### `avaliacao_service.py`

Regras atuais:

- bebida precisa existir;
- usuario tem uma avaliacao por bebida;
- se avaliacao existir, atualiza;
- se nao existir, cria;
- lista minhas avaliacoes por data desc.

Migracao Java:

- `AvaliacaoController`;
- `AvaliacaoService`;
- `AvaliacaoRepository`.

### `favorito_service.py`

Regras atuais:

- bebida precisa existir para favoritar;
- favoritar e idempotente: se ja existe, retorna o existente;
- remover favorito inexistente retorna 404;
- lista favoritos por data desc.

Migracao Java:

- `FavoritoController`;
- `FavoritoService`;
- `FavoritoRepository`.

### `preco_service.py`

Regras atuais:

- bebida precisa existir;
- preco e associado ao usuario autenticado;
- valor validado no schema como >= 0;
- lista ate 50 precos por bebida, mais recentes primeiro.

Migracao Java:

- `PrecoController`;
- `PrecoService`;
- `PrecoRepository`;
- usar `BigDecimal`.

### `privacidade_service.py`

Regras atuais:

- retorna politica e termos com versao atual.

Migracao Java:

- `PrivacidadeController`;
- `LgpdDocumentService`.

### `email_service.py`

Regras atuais:

- provedor Resend;
- `RESEND_API_KEY` vazia gera `EmailNaoConfigurado`;
- remetente vem de `EMAIL_FROM`;
- base de reset vem de `PASSWORD_RESET_BASE_URL`;
- URL app vem de `APP_WEB_URL`;
- e-mails: boas-vindas, reset, senha alterada, senha redefinida;
- logs nao devem vazar token/senha.

Migracao Java:

- `ResendClient`;
- `TransactionalEmailService`;
- `EmailTemplateService`;
- `EmailNotConfiguredException`;
- `RestClient` ou `WebClient`.

### `admin_service.py`

Regras atuais:

- dashboard conta usuarios, ativos, bebidas, avaliacoes, favoritos, precos;
- atividade recente traz ultimos 5 de usuarios/bebidas/avaliacoes/precos;
- admin pode ativar/desativar usuario;
- admin pode marcar e-mail verificado;
- admin pode revogar tokens;
- admin pode criar/excluir usuarios;
- excluir usuario apaga refresh tokens, avaliacoes, favoritos e precos antes do usuario;
- admin lista/cria/edita/exclui bebidas;
- excluir bebida apaga avaliacoes/favoritos/precos vinculados;
- admin cria/exclui avaliacoes/favoritos/precos;
- preco admin aceita virgula ou ponto e rejeita valor negativo.

Migracao Java:

- `AdminController`;
- `AdminService`;
- `AdminDashboardService`;
- `AdminSecurityConfig`;
- templates Thymeleaf se o painel HTML continuar.

### `web_service.py`, `routes_web.py`, `views/web_views.py`

Regras atuais:

- web app usa cookies `web_access_token` e `web_refresh_token`;
- cookies podem ser `secure` via `WEB_COOKIE_SECURE`;
- CSRF baseado em HMAC com refresh token;
- web exige login para uso;
- se LGPD pendente, bloqueia navegacao exceto rotas permitidas;
- reaproveita auth, LGPD, bebidas, favoritos e avaliacoes;
- renderiza HTML manual.

Migracao Java:

- decidir se `/web` sera mantido;
- se sim: `WebController`, `WebAuthService`, Thymeleaf, CSRF Spring Security;
- se nao: manter apenas API e reset de senha.

### `routes_password_reset.py`

Regras atuais:

- pagina publica fora de `/web`;
- token vem por query string;
- senha forte;
- botao para voltar ao login;
- rota legada `/web/resetar-senha`.

Migracao Java:

- `PasswordResetPageController`;
- template Thymeleaf simples;
- `PasswordResetService`.

### `logging_config.py`

Regras atuais:

- logs JSON;
- `requestId` e `userId` via contextvars;
- sanitizacao de chaves sensiveis;
- mascaramento de senha, token, secret, CPF e e-mail;
- loggers separados: app, security, audit.

Migracao Java:

- Logback JSON;
- MDC com `requestId` e `userId`;
- `LogSanitizer`;
- `AuditLogger`;
- `SecurityLogger`;
- filtros para limpar MDC no fim da request.

### `migrations.py`

Regras atuais:

- migracoes leves no startup;
- cria/ajusta colunas;
- migra dados antigos de cachaca para tabela propria.

Migracao Java:

- converter para Flyway;
- criar baseline do schema atual;
- desligar alteracoes automaticas no startup;
- manter `ddl-auto=validate`.

## 7. Dependencias Python E Equivalentes Java

| Python | Uso atual | Equivalente Java |
|---|---|---|
| `fastapi[standard]` | API, rotas, Depends, schemas HTTP | `spring-boot-starter-web`, Spring MVC |
| `uvicorn[standard]` | Servidor ASGI | Tomcat embutido do Spring Boot |
| `sqlalchemy` | ORM e queries | Spring Data JPA + Hibernate |
| `psycopg[binary]` | Driver PostgreSQL | `org.postgresql:postgresql` |
| `pydantic[email]` | DTOs, validacao, EmailStr | Jakarta Bean Validation + DTO records/classes |
| `python-dotenv` | carregar `.env` | Spring `application.yml`, env vars, profiles |
| `PyJWT` | JWT HS256/384/512 | `io.jsonwebtoken:jjwt-*` ou `com.auth0:java-jwt` |
| `pwdlib[argon2]` | hash Argon2 | Spring Security `Argon2PasswordEncoder` |
| `httpx` | chamadas Open Food Facts/Resend | Spring `RestClient` ou `WebClient` |
| `pytest` | testes | JUnit 5, Spring Boot Test, MockMvc |
| `csv` stdlib | exportacao CSV | Apache Commons CSV ou `StringBuilder` controlado |
| `contextvars` stdlib | contexto de log | SLF4J MDC |
| `hmac/hashlib/secrets` stdlib | CSRF/tokens/hash | Java `Mac`, `MessageDigest`, `SecureRandom` |

Dependencias Java adicionais recomendadas:

- `flyway-core`;
- `spring-boot-starter-actuator`;
- `logstash-logback-encoder`;
- `caffeine`, se rate limit ficar em memoria;
- `spring-security-test`;
- `testcontainers-postgresql`, se quiser testes com PostgreSQL real.

## 8. Pacotes Java Sugeridos

```text
br.com.bebidasscan.api
  admin
  auth
  avaliacao
  bebida
  common
  config
  email
  favorito
  lgpd
  observability
  openfoodfacts
  perfil
  preco
  privacidade
  security
  usuario
  web
```

## 9. Ordem De Implementacao Recomendada

1. Configuracao base, health, CORS, exceptions e logs.
2. Entidades JPA e repositories equivalentes aos modelos Python.
3. Flyway baseline do banco atual.
4. DTOs equivalentes aos schemas Pydantic.
5. Security: Argon2, JWT, bearer filter, usuario autenticado.
6. Auth completo.
7. Perfil/LGPD.
8. Bebidas + Open Food Facts.
9. Avaliacoes, favoritos e precos.
10. Resend/e-mails.
11. Reset de senha HTML.
12. Admin.
13. Web app, se for mantido.
14. Docker/Cloudflare e troca controlada.

## 10. Contratos Criticos Para Preservar

- Nomes JSON em snake_case ou equivalentes esperados pelo Flutter.
- Status HTTP e mensagens importantes usadas pelo app.
- Formato de `access_token`, `refresh_token`, `token_type`.
- `Authorization: Bearer <token>`.
- Exportacao CSV em `/perfil/exportar.csv`.
- URL publica `/resetar-senha?token=...`.
- Busca por `/bebidas/codigo/{codigo_barras}` e `/bebidas/buscar?q=...`.
- Separacao de dados de `cachaca`.
- Anonimizacao com confirmacao por e-mail e senha.
- Nao logar senha, token, secret, CPF ou e-mail em claro.

## 11. Testes Minimos Da Migracao

- `GET /health`.
- Cadastro feliz.
- Cadastro sem LGPD.
- Cadastro menor de 18.
- Cadastro com senha fraca.
- Cadastro com e-mail invalido.
- Login por nome de usuario.
- Login por e-mail.
- Login invalido com rate limit.
- Refresh token valido e invalido.
- Logout revogando refresh token.
- Alterar senha e revogar tokens.
- Solicitar reset com e-mail existente e inexistente.
- Confirmar reset com token valido, usado e expirado.
- Status LGPD pendente/aceito.
- Aceite LGPD.
- Exportacao CSV por categoria.
- Anonimizacao com confirmacao correta/incorreta.
- Criar bebida.
- Editar bebida propria e bloquear edicao alheia.
- Buscar bebida por codigo local.
- Buscar bebida por codigo via Open Food Facts.
- Buscar bebida por nome local e externo.
- Favoritar idempotente.
- Remover favorito.
- Criar/atualizar avaliacao.
- Registrar/listar preco.
- Logs sem dados sensiveis.

## 12. Itens Que Devem Ser Decididos Antes Do Corte Final

- Manter ou remover o web app `/web`.
- Manter ou substituir o painel admin HTML.
- Compatibilidade de tokens Python ja emitidos com tokens Java.
- Se rate limit em memoria e suficiente ou se deve usar Redis.
- Se Flyway vai assumir todo o schema desde o inicio ou iniciar com baseline.
- Se `api.bebidasscan.com.br` vai trocar direto para Java ou se sera criado subdominio temporario.

## 13. Criterio De Pronto Para Trocar A API

A API Java so deve substituir a Python quando:

- todos os endpoints criticos do app mobile estiverem implementados;
- testes automatizados passarem;
- banco existente validar com JPA/Flyway;
- CORS/Cloudflare funcionarem;
- Resend enviar e-mails;
- Open Food Facts funcionar com fallback;
- LGPD estiver operacional;
- logs estruturados estiverem ativos;
- houver rollback documentado para voltar ao backend Python.
