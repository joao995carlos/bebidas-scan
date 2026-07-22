# Bebidas Scan - Documentacao completa do projeto

Atualizado em: 2026-07-14

## 1. Visao geral

O Bebidas Scan e um sistema para consultar, cadastrar, avaliar e organizar bebidas a partir de codigo de barras.

O projeto possui:

- API backend em FastAPI.
- Site web servido pelo proprio backend.
- App Android em Flutter.
- Banco de dados PostgreSQL em Docker.
- Integracao com Open Food Facts.
- Leitura de codigo de barras e OCR no Android com Google ML Kit.
- Recursos de LGPD para aceite, transparencia, exportacao CSV e exclusao/anonimizacao de conta.

## 2. Estrutura de pastas

```text
Bebidas Scan/
  backend/
    app/
      main.py
      database.py
      models.py
      schemas.py
      controllers/
        *_controller.py
      services/
        auth_service.py
        bebida_service.py
        perfil_service.py
        avaliacao_service.py
        favorito_service.py
        preco_service.py
        privacidade_service.py
        admin_service.py
        web_service.py
      views/
        admin_views.py
        web_views.py
      security.py
      dependencies.py
      migrations.py
      open_food_facts.py
      lgpd.py
      routes_auth.py
      routes_bebidas.py
      routes_avaliacoes.py
      routes_favoritos.py
      routes_precos.py
      routes_perfil.py
      routes_privacidade.py
      routes_web.py
      routes_admin.py
      tipos_bebida.py
      rate_limit.py
      logging_config.py
    tests/
    requirements.txt
    README.md
  mobile/
    bebidas_scan_app/
      lib/
      android/
      pubspec.yaml
      README.md
  docker-compose.yml
  .env.docker
  .env.docker.example
  README.md
  PROJETO_COMPLETO.md
  ARQUITETURA_MVC.md
```

## 3. Tecnologias usadas

### Backend

- Python.
- FastAPI.
- Arquitetura MVC incremental com controllers e services.
- Uvicorn.
- SQLAlchemy.
- PostgreSQL em producao/local via Docker.
- Psycopg.
- Pydantic.
- PyJWT.
- pwdlib com Argon2 para hash de senha.
- httpx para chamadas externas.
- python-dotenv para variaveis de ambiente.
- pytest para testes.

Padrao atual:

- `models.py` e `schemas.py`: dados, tabelas e contratos.
- `controllers/*_controller.py`: camada publica de roteamento importada pelo `main.py`.
- `routes_*.py`: endpoints HTTP; nos modulos migrados ficam finos e delegam regra de negocio.
- `services/*.py`: regras de negocio, logs de auditoria, validacoes de fluxo e chamadas coordenadas ao banco.
- `views/*.py`: renderizacao HTML do web app e do painel admin.

### Web

- HTML gerado no backend com FastAPI.
- CSS embutido nas paginas do web app/admin.
- JavaScript nativo na tela de scanner web.
- BarcodeDetector API quando disponivel no navegador.
- Fallback manual quando o navegador nao suporta BarcodeDetector.

### Mobile

- Flutter.
- Dart.
- Dio para HTTP.
- flutter_secure_storage para tokens locais.
- camera para camera do app.
- path_provider para salvar arquivo temporario de exportacao.
- share_plus para compartilhar/exportar CSV.
- Google ML Kit no Android:
  - `com.google.mlkit:barcode-scanning:17.3.0`
  - `com.google.mlkit:text-recognition:16.0.1`

### Infraestrutura

- Docker Compose.
- Container `api` com FastAPI/Uvicorn.
- Container `db` com `postgres:16-alpine`.
- Volume Docker para persistir dados do PostgreSQL.
- Preparado para uso com dominio e Cloudflare Tunnel/proxy HTTPS.

## 4. Banco de dados

Modelos principais:

- `Usuario`
- `RefreshToken`
- `Bebida`
- `Cachaca`
- `Avaliacao`
- `Favorito`
- `Preco`

### Usuario

Campos principais:

- nome
- nome de usuario
- email
- senha com hash
- data de nascimento
- confirmacao de maioridade
- tipo de usuario
- status ativo
- versoes aceitas de Politica de Privacidade e Termos
- data/hora de aceite LGPD
- consentimento de marketing
- data de anonimizacao

### Bebida

Campos principais:

- nome
- marca
- tipo
- codigo de barras
- teor alcoolico
- ingredientes
- imagem
- origem dos dados
- usuario criador

Campos enriquecidos por Open Food Facts:

- Nutri-Score
- grupo NOVA
- Eco-Score
- alergenos
- categorias
- quantidade
- embalagem
- paises

### Cachaca

Dados especificos de cachaca foram separados da bebida generica:

- volume
- classificacao
- madeira
- tempo de envelhecimento
- cidade/estado/regiao de origem
- alambique
- produtor
- lote

Esses campos aparecem apenas quando o tipo da bebida e cachaca ou aguardente.

## 5. Backend/API

Base local atual:

```text
http://localhost:8000
```

Healthcheck:

```text
GET /health
```

Documentacao interativa:

```text
http://localhost:8000/docs
```

### Autenticacao

Rotas principais:

- `POST /auth/registrar`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`

Login atual:

- identificador por nome de usuario, email ou campo `identificador`
- senha

### Senhas e credenciais

Usuario comum:

- Nao existe usuario/senha padrao para entrar no app.
- O usuario precisa clicar em `Criar conta`.
- No cadastro, ele define:
  - nome
  - nome de usuario
  - e-mail
  - senha
  - data de nascimento
- A senha de usuario comum precisa ter pelo menos 8 caracteres.
- A senha tambem precisa ter pelo menos uma letra maiuscula, um numero e um caractere especial.
- Depois do cadastro, o login pode ser feito com nome de usuario ou e-mail.
- A senha tambem e exigida para confirmar exclusao/anonimizacao da conta.
- O e-mail e validado no backend e nas telas web/mobile antes do cadastro.
- Entradas que nao sejam e-mail valido, incluindo textos parecidos com SQL, sao recusadas.
- As consultas ao banco usam SQLAlchemy/ORM, evitando concatenacao manual de SQL com dados do usuario.

Administrador:

- A area admin usa credenciais separadas, definidas no `.env.docker`.
- Variaveis:
  - `ADMIN_USERNAME`
  - `ADMIN_PASSWORD`
- Essas credenciais nao aparecem na tela do app e nao devem ser publicadas em documentacao compartilhada.

Banco de dados:

- A senha do PostgreSQL fica em `POSTGRES_PASSWORD` no `.env.docker`.
- Essa senha e somente para conexao do backend com o banco, nao para login no site/app.

O backend usa:

- access token JWT
- refresh token opaco salvo com hash no banco
- revogacao de refresh token no logout
- limpeza de refresh tokens expirados/revogados

### Perfil e LGPD

Rotas:

- `GET /perfil/me`
- `GET /perfil/lgpd/status`
- `POST /perfil/lgpd/aceitar`
- `GET /perfil/exportar.csv`
- `POST /perfil/anonimizar`

Exclusao de conta:

- exige email
- exige senha
- anonimiza nome, email e nome de usuario
- desativa usuario
- revoga tokens
- remove favoritos
- mantem dados de interesse publico/estatistico conforme regra definida

### Bebidas

Rotas:

- `POST /bebidas`
- `PATCH /bebidas/{id_bebida}`
- `GET /bebidas/codigo/{codigo_barras}`
- `GET /bebidas/buscar?q=...`

Ao buscar por codigo:

1. Procura no banco local.
2. Se nao encontrar, consulta Open Food Facts.
3. Se o produto for bebida, cadastra e retorna.
4. Se for alimento comum ou produto nao reconhecido como bebida, retorna `404`.

### Avaliacoes

Rotas:

- `POST /avaliacoes`
- `GET /avaliacoes/minhas`

Regras:

- nota de 1 a 5
- comentario opcional
- flag "compraria novamente"
- um usuario nao deve avaliar a mesma bebida de forma duplicada

### Favoritos

Rotas:

- `GET /favoritos`
- `POST /favoritos/{id_bebida}`
- `DELETE /favoritos/{id_bebida}`

### Precos

Rotas:

- `POST /precos`
- `GET /precos/bebida/{id_bebida}`

Regras:

- valor nao pode ser negativo
- mercado/cidade/estado opcionais

### Privacidade publica

Rotas:

- `GET /privacidade/politica`
- `GET /privacidade/termos`

Retornam a versao atual e o texto legal.

## 6. Site web

O site web roda no proprio backend.

URL local:

```text
http://localhost:8000/
```

### Comportamento atual

- A raiz publica mostra uma pagina de boas-vindas/explicacao.
- O usuario precisa marcar que leu o texto para o botao ficar habilitado.
- O botao leva para o app web/login.
- O app web exige login para uso.
- Sem login, o usuario nao acessa scanner, bebidas, favoritos, avaliacoes e privacidade.

### Telas web principais

- Boas-vindas publica.
- Login.
- Cadastro.
- Aceite LGPD quando pendente.
- Home do app web.
- Scanner web por camera.
- Busca manual por codigo.
- Cadastro/edicao de bebida.
- Detalhe da bebida.
- Favoritos.
- Minhas avaliacoes.
- Minha privacidade.
- Politica de Privacidade.
- Termos de Uso.

### Scanner web

Usa `BarcodeDetector` quando o navegador suporta.

Formatos:

- EAN-13
- EAN-8
- UPC-A
- UPC-E
- CODE-128

Quando o navegador nao suporta, mostra mensagem orientando digitacao manual.

Observacao importante:

- Acesso a camera em navegador geralmente exige HTTPS em dominio publico.
- Em `localhost`, navegadores costumam permitir camera.
- Em IP local ou dominio sem HTTPS, a camera pode ser bloqueada.

## 7. Admin web

Existe uma area admin protegida por HTTP Basic.

Recursos:

- dashboard
- metricas
- usuarios
- ativar/desativar usuarios
- verificar email manualmente
- revogar tokens
- criar/excluir usuarios
- bebidas
- criar/editar/excluir bebidas
- avaliacoes
- favoritos
- precos

Credenciais sao configuradas por variaveis:

- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `ADMIN_CSRF_SECRET`

## 8. App mobile Android

Local:

```text
mobile/bebidas_scan_app
```

### Telas principais

- Login.
- Cadastro.
- Home.
- Scanner de codigo de barras.
- OCR de rotulo/garrafa.
- Detalhe da bebida.
- Cadastro/edicao de bebida.
- Favoritos.
- Minha privacidade.
- Politica de Privacidade.
- Termos de Uso.
- Aceite LGPD.

### API base

O app usa `dart-define`:

```text
API_BASE_URL
```

Padrao atual no codigo:

```text
http://192.168.0.31:8000
```

APK de teste mais recente gerado:

```text
BebidasScan-lan-192.168.10.23.apk
```

Esse APK aponta para:

```text
http://192.168.10.23:8000
```

### Camera e ML Kit

O app Android usa ML Kit nativo via MethodChannel:

```text
bebidas_scan/native_barcode
```

Funcionalidades nativas:

- leitura de codigo de barras por imagem capturada
- leitura OCR de texto em imagem capturada

Formatos de codigo:

- EAN-13
- EAN-8
- UPC-A
- UPC-E
- CODE-128

Ao detectar codigo de barras, o app executa uma vibracao curta usando `HapticFeedback.mediumImpact()`.

### Exportacao LGPD no mobile

O usuario pode exportar dados em CSV pelo app.

Fluxo:

1. Seleciona categorias.
2. App chama `/perfil/exportar.csv`.
3. App salva arquivo temporario.
4. App compartilha o CSV via `share_plus`.

## 9. LGPD

Versao atual dos documentos:

```text
2026-07-14
```

Controlador atual:

```text
Bebidas Scan como projeto provisorio
```

Contato LGPD atual:

```text
canal de privacidade a ser definido
```

### Regras implementadas

- Cadastro exige aceite da Politica de Privacidade.
- Cadastro exige aceite dos Termos de Uso.
- Usuario precisa informar data de nascimento.
- Sistema bloqueia uso quando LGPD estiver pendente.
- Mudanca de versao exige novo aceite.
- Marketing possui consentimento separado.
- Exportacao de dados em CSV.
- Tela "Minha privacidade" no web e no mobile.
- Exclusao/anonimizacao de conta pelo usuario.
- Confirmacao de exclusao com email e senha.
- Revogacao imediata de tokens ao anonimizar.
- Favoritos removidos na exclusao.
- Avaliacoes podem manter nota, apagando comentario e desvinculando usuario.
- Bebidas criadas podem permanecer, removendo vinculo com usuario.
- Tokens expirados/revogados podem ser limpos.

### Textos legais

Textos gerados no backend:

- Politica de Privacidade
- Termos de Uso

Esses textos sao MVP/formais, mas ainda devem ser revisados por profissional juridico antes de uso publico definitivo.

## 10. Open Food Facts

Integracao em:

```text
backend/app/open_food_facts.py
```

Endpoint usado:

```text
https://world.openfoodfacts.org/api/v2/product/{codigo}.json
```

Campos buscados:

- nome
- nome generico
- categorias
- marcas
- ingredientes
- imagem frontal
- Nutri-Score
- NOVA
- Eco-Score
- alergenos
- quantidade
- embalagem
- paises
- nutrimentos

Filtro atual:

- so cadastra automaticamente quando as categorias indicam bebida
- alimentos comuns retornam `404` e nao entram no banco

Tipos reconhecidos:

- cerveja
- vinho
- destilado
- energetico
- refrigerante
- suco
- agua
- cha
- cafe
- bebida generica

## 11. Separacao entre bebidas genericas e cachaca

O projeto evita misturar dados especificos de cachaca em todas as bebidas.

Regras:

- Campos de cachaca ficam no modelo/tabela `Cachaca`.
- O relacionamento e opcional.
- UI web/mobile so mostra campos de cachaca quando o tipo for cachaca ou aguardente.
- Bebidas como refrigerante, agua, energetico e cerveja nao exibem campos de alambique/madeira/envelhecimento.

## 12. Seguranca

Recursos atuais:

- Senha com hash Argon2.
- JWT para access token.
- Refresh token opaco salvo com hash.
- Logout revoga refresh token.
- Rate limit em login/autenticacao.
- Bloqueio temporario por tentativas repetidas.
- Validacao de payload com Pydantic.
- Limite de tamanho de requisicao.
- CSRF em formularios web sensiveis.
- Cookies web com opcao `WEB_COOKIE_SECURE`.
- Suporte a proxy headers atras de Cloudflare/proxy confiavel.
- Escape de HTML em campos exibidos no web.
- Testes cobrindo basicos de seguranca.
- QA automatizado com TestClient para fluxos principais do web app e admin: cadastro, login, LGPD, busca, scanner manual, cadastro de bebida, favorito, avaliacao, exportacao CSV, logout e formularios administrativos.

Pontos que ainda merecem atencao antes de producao:

- Definir dominio final.
- Usar HTTPS obrigatorio.
- Revisar CORS.
- Trocar todos os segredos.
- Definir credenciais admin fortes.
- Revisar politica de backup.
- Configurar firewall.
- Definir monitoramento/logs.
- Revisao juridica LGPD.

## 13. Docker

Servicos:

- `db`: PostgreSQL 16 Alpine
- `api`: FastAPI/Uvicorn

Comando principal:

```powershell
docker compose --env-file .env.docker up -d --build
```

Parar sem apagar dados:

```powershell
docker compose --env-file .env.docker down
```

Parar apagando volume/banco:

```powershell
docker compose --env-file .env.docker down -v
```

Status:

```powershell
docker compose --env-file .env.docker ps
```

Logs:

```powershell
docker compose --env-file .env.docker logs -f api
```

## 14. Variaveis de ambiente importantes

Arquivo Docker:

```text
.env.docker
```

Principais variaveis:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`
- `CORS_ORIGINS`
- `OPEN_FOOD_FACTS_USER_AGENT`
- `AUTH_RATE_LIMIT_MAX_ATTEMPTS`
- `AUTH_RATE_LIMIT_WINDOW_SECONDS`
- `AUTH_RATE_LIMIT_IDENTITY_MAX_ATTEMPTS`
- `AUTH_RATE_LIMIT_IDENTITY_WINDOW_SECONDS`
- `AUTH_LOCKOUT_SECONDS`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `ADMIN_CSRF_SECRET`
- `WEB_CSRF_SECRET`
- `WEB_COOKIE_SECURE`
- `TRUST_PROXY_HEADERS`
- `FORWARDED_ALLOW_IPS`
- `MAX_REQUEST_BODY_BYTES`
- `LOG_LEVEL`
- `API_PORT`

Para Cloudflare/producao:

```env
CORS_ORIGINS=https://seudominio.com.br,https://www.seudominio.com.br,https://api.seudominio.com.br
WEB_COOKIE_SECURE=true
TRUST_PROXY_HEADERS=true
FORWARDED_ALLOW_IPS=*
```

Observacao:

- `FORWARDED_ALLOW_IPS=*` so deve ser usado se o acesso publico passar exclusivamente por proxy confiavel, como Cloudflare Tunnel.

## 15. Como rodar localmente

Na raiz:

```powershell
cd "D:\Arquivos\Documentos\Bebidas Scan"
docker compose --env-file .env.docker up -d --build
```

Abrir:

```text
http://localhost:8000/
```

Healthcheck:

```text
http://localhost:8000/health
```

## 16. Como gerar APK

Entrar na pasta mobile:

```powershell
cd "D:\Arquivos\Documentos\Bebidas Scan\mobile\bebidas_scan_app"
```

Gerar APK para celular fisico usando IP do computador:

```powershell
flutter build apk --release --dart-define=API_BASE_URL=http://SEU_IP:8000
```

Exemplo usado no ultimo APK:

```powershell
flutter build apk --release --dart-define=API_BASE_URL=http://192.168.10.23:8000
```

Arquivo gerado pelo Flutter:

```text
mobile/bebidas_scan_app/build/app/outputs/flutter-apk/app-release.apk
```

Arquivo copiado para a raiz:

```text
BebidasScan-lan-192.168.10.23.apk
```

Observacao atual do build Android:

- Foi adicionada a opcao `kotlin.incremental=false` em `android/gradle.properties`.
- Motivo: evitar falha de cache incremental do Kotlin no Windows quando o projeto esta em `D:` e plugins do Pub estao em `C:`.

## 17. Testes e validacoes recentes

Backend:

```powershell
cd backend
venv\Scripts\python.exe -m pytest tests
```

Estado recente:

```text
7 passed
```

Mobile:

```powershell
cd mobile\bebidas_scan_app
flutter analyze
flutter test
```

Estado recente:

```text
flutter analyze: sem erros
flutter test: passou
```

Docker:

```text
api: healthy
db: healthy
```

Teste Open Food Facts:

- alimento comum testado retornou `404`
- bebida testada retornou dados enriquecidos
- registros de teste foram removidos do banco

## 18. Estado atual do projeto

### Funcionando

- Backend FastAPI.
- Docker com API e PostgreSQL.
- Site web publico com pagina de boas-vindas.
- Login obrigatorio no web app.
- Cadastro com nome de usuario, email, senha e data de nascimento.
- Login com nome de usuario/email/identificador e senha.
- Scanner web com BarcodeDetector quando suportado.
- Cadastro manual de bebidas.
- Busca por codigo de barras.
- Integracao Open Food Facts filtrando apenas bebidas.
- Detalhe de bebida no web e mobile.
- Dados enriquecidos do Open Food Facts no web e mobile.
- Separacao de campos de cachaca.
- Favoritos.
- Avaliacoes.
- Precos.
- Admin web.
- LGPD web.
- LGPD mobile.
- Exportacao CSV no web e mobile.
- Anonimizacao/exclusao de conta com email e senha.
- ML Kit no Android para barcode/OCR.
- Vibracao curta ao escanear codigo no mobile.
- APK de teste para LAN.

### Em atencao

- Camera no navegador em dominio/IP publico precisa HTTPS.
- Textos LGPD precisam revisao juridica antes de producao real.
- Dominio final ainda nao definido.
- Contato LGPD ainda esta como placeholder.
- Credenciais e segredos precisam ser definitivos antes de publicar.
- App Android ainda usa package `com.example.bebidas_scan_app`; antes de Play Store, trocar para um identificador final.
- Release Android usa assinatura debug caso `key.properties` nao exista; para distribuicao oficial, criar keystore de release.

## 19. Proximos passos sugeridos

1. Definir dominio final.
2. Criar email de privacidade, por exemplo `privacidade@seudominio.com.br`.
3. Configurar Cloudflare Tunnel ou proxy HTTPS.
4. Atualizar `.env.docker` com CORS, cookies seguros e segredos fortes.
5. Gerar APK apontando para HTTPS do dominio.
6. Trocar package name Android para identificador final.
7. Criar keystore de release.
8. Revisar LGPD com profissional juridico.
9. Adicionar backup automatizado do PostgreSQL.
10. Adicionar monitoramento/logs de producao.
