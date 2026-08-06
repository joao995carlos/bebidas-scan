# Bebidas Scan

Sistema para consultar, cadastrar, avaliar e organizar bebidas a partir de codigo de barras.

O projeto possui backend/API em FastAPI, app Android em Flutter, web app servido pelo proprio backend, painel admin, recursos de LGPD, e-mail transacional com Resend e preparacao para publicar via Cloudflare Tunnel.

## Estado Atual

- Backend funcional com FastAPI, SQLAlchemy, JWT, refresh tokens, rate limit, logs estruturados e mascaramento de dados sensiveis.
- Banco PostgreSQL via Docker Compose.
- App Android Flutter com login obrigatorio, onboarding, scanner, busca, favoritos, avaliacoes, perfil, privacidade, exportacao CSV e aviso persistente quando a API esta offline.
- Scanner Android com camera, Google ML Kit para codigo de barras/OCR, vibracao curta ao detectar codigo e configuracoes de scanner/acessibilidade.
- Web app em `/web`, atualmente deixado em segundo plano, mas protegido por login.
- Pagina publica separada para redefinicao de senha em `/resetar-senha`.
- Integracao com Open Food Facts para enriquecer busca por codigo/nome.
- Integracao com Resend para boas-vindas, recuperacao de senha e avisos de senha alterada/redefinida.
- Dominio usado no projeto: `bebidasscan.com.br`.
- Rota publica de API usada nos testes com dominio: `https://api.bebidasscan.com.br`.

## Estrutura

```text
Bebidas Scan/
  backend/
    app/
      controllers/       # camada publica MVC importada pelo main.py
      services/          # regras de negocio
      views/             # HTML do web app/admin
      main.py            # FastAPI app, middlewares e routers
      database.py        # engine/session SQLAlchemy
      models.py          # modelos/tabelas
      schemas.py         # contratos Pydantic
      lgpd.py            # regras LGPD
      email_service.py   # Resend/e-mails transacionais
      open_food_facts.py # integracao externa
      logging_config.py  # logs JSON e data masking
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
  .env.docker.example
  README.md
  PROJETO_COMPLETO.md
  ARQUITETURA_MVC.md
  OBSERVABILIDADE.md
```

## Tecnologias

### Backend

- Python
- FastAPI
- Uvicorn
- SQLAlchemy
- PostgreSQL
- Pydantic
- PyJWT
- Argon2 via `pwdlib`
- httpx
- python-dotenv
- pytest

### Mobile

- Flutter/Dart
- Dio
- flutter_secure_storage
- camera
- permission_handler
- path_provider
- share_plus
- Google ML Kit no Android:
  - `com.google.mlkit:barcode-scanning:17.3.0`
  - `com.google.mlkit:text-recognition:16.0.1`

### Infraestrutura

- Docker Compose
- PostgreSQL `postgres:16-alpine`
- Cloudflare DNS/Tunnel
- Resend para e-mails transacionais

## Arquitetura

O backend segue uma arquitetura MVC incremental:

- `models.py`: entidades de banco.
- `schemas.py`: contratos de entrada/saida da API.
- `controllers/*_controller.py`: camada de controller importada pelo `main.py`.
- `routes_*.py`: endpoints HTTP.
- `services/*.py`: regras de negocio e coordenacao com banco/servicos externos.
- `views/*.py`: renderizacao HTML do web app e painel admin.

Arquivos complementares:

- `lgpd.py`: aceite, exportacao CSV, retencao e anonimizacao.
- `logging_config.py`: logs estruturados em JSON com `requestId`, `userId`, niveis e mascaramento de dados sensiveis.
- `migrations.py`: migracoes leves executadas na inicializacao.

## Funcionalidades Principais

- Cadastro e login com nome de usuario/e-mail e senha.
- Validacao de e-mail e senha forte.
- Refresh token, logout e troca de senha.
- Recuperacao de senha por e-mail.
- Busca de bebidas por codigo de barras.
- Busca de bebidas por nome no banco e na API externa.
- Cadastro e edicao de bebidas.
- Separacao de dados gerais de bebida e dados especificos de cachaca.
- Favoritos.
- Avaliacoes.
- Registro de precos.
- Perfil do usuario.
- Configuracoes do app mobile.
- Onboarding no mobile.
- Aviso persistente quando o backend esta offline.
- Exportacao de dados pessoais em CSV.
- Exclusao/anonimizacao de conta com confirmacao por e-mail e senha.
- Painel admin com usuarios, bebidas, avaliacoes, favoritos e precos.

## LGPD

Recursos implementados:

- Aceite obrigatorio de Politica de Privacidade e Termos.
- Versao atual dos documentos: `2026-07-14`.
- Confirmacao de maioridade por data de nascimento.
- Consentimento separado para marketing.
- Tela/API de status LGPD.
- Politica de Privacidade e Termos expostos pela API.
- Exportacao CSV por categorias.
- Exclusao/anonimizacao de conta.
- Revogacao de tokens ao excluir conta.
- Retencao prevista para logs e refresh tokens.

## E-mails

Provedor: Resend.

E-mails transacionais atuais:

- Boas-vindas apos cadastro.
- Link de recuperacao de senha.
- Aviso de senha alterada.
- Aviso de senha redefinida.

Variaveis necessarias:

```env
RESEND_API_KEY=re_sua_chave
EMAIL_FROM=Bebidas Scan <nao-responda@bebidasscan.com.br>
PASSWORD_RESET_BASE_URL=https://api.bebidasscan.com.br/resetar-senha
APP_WEB_URL=https://bebidasscan.com.br
```

Importante: nunca grave `RESEND_API_KEY` no Git.

## Rodar Com Docker

Na raiz do projeto:

```powershell
Copy-Item .env.docker.example .env.docker
docker compose --env-file .env.docker up -d --build
```

Servicos:

- API: `http://localhost:8000`
- Healthcheck: `http://localhost:8000/health`
- Docs: `http://localhost:8000/docs`
- Web app: `http://localhost:8000/web/`
- Admin: `http://localhost:8000/admin/`
- Redefinicao de senha: `http://localhost:8000/resetar-senha`

Para parar sem apagar dados:

```powershell
docker compose --env-file .env.docker down
```

Para parar e apagar o banco/volume:

```powershell
docker compose --env-file .env.docker down -v
```

## Rodar Backend Sem Docker

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Configure `DATABASE_URL` no `backend/.env`. Em desenvolvimento, as tabelas/migracoes leves rodam na inicializacao.

## Configurar Dominio Com Cloudflare Tunnel

1. No Cloudflare Zero Trust, crie um tunnel.
2. Instale/rode o `cloudflared` no computador onde a API esta rodando.
3. No tunnel, adicione uma rota do tipo `Aplicativo publicado`.
4. Configure o hostname:

```text
api.bebidasscan.com.br
```

5. Configure a URL do servico com protocolo:

```text
http://localhost:8000
```

6. Confirme que a Cloudflare criou um CNAME apontando para:

```text
<id-do-tunnel>.cfargotunnel.com
```

7. No `.env.docker`, use:

```env
CORS_ORIGINS=https://bebidasscan.com.br,https://www.bebidasscan.com.br,https://api.bebidasscan.com.br
WEB_COOKIE_SECURE=true
TRUST_PROXY_HEADERS=true
FORWARDED_ALLOW_IPS=*
PASSWORD_RESET_BASE_URL=https://api.bebidasscan.com.br/resetar-senha
APP_WEB_URL=https://bebidasscan.com.br
```

Use `FORWARDED_ALLOW_IPS=*` apenas quando o acesso publico passar exclusivamente pelo proxy/tunnel confiavel.

## Rodar O App Mobile

```powershell
cd mobile\bebidas_scan_app
flutter pub get
flutter run
```

Para emulador Android usando backend local:

```powershell
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

Para celular fisico na mesma rede:

```powershell
flutter run --dart-define=API_BASE_URL=http://SEU_IP_LOCAL:8000
```

Para dominio HTTPS:

```powershell
flutter run --dart-define=API_BASE_URL=https://api.bebidasscan.com.br
```

## Gerar APK

APK local/release apontando para a API local:

```powershell
cd mobile\bebidas_scan_app
flutter build apk --release --dart-define=API_BASE_URL=http://SEU_IP_LOCAL:8000
```

APK apontando para o dominio:

```powershell
cd mobile\bebidas_scan_app
flutter build apk --release --dart-define=API_BASE_URL=https://api.bebidasscan.com.br
```

O APK gerado fica em:

```text
mobile\bebidas_scan_app\build\app\outputs\flutter-apk\app-release.apk
```

## QA

Backend:

```powershell
cd backend
.\venv\Scripts\python.exe -m compileall app tests -q
.\venv\Scripts\python.exe -m pytest tests -q
```

Mobile:

```powershell
cd mobile\bebidas_scan_app
flutter analyze
flutter test
```

Git:

```powershell
git diff --check
git status --short
```

## Observabilidade E Seguranca

- Logs estruturados em JSON.
- Niveis: `info`, `warn`, `error`, `fatal`.
- Contexto de log com `requestId`, `userId` e `action` quando disponivel.
- Mascara de dados sensiveis como senha, token, segredo, CPF e e-mail.
- Rate limit em rotas de autenticacao.
- CSRF no web app/admin.
- Cookies seguros configuraveis para uso com HTTPS.
- Validacao de e-mail e senha forte.

## Documentos Complementares

- `PROJETO_COMPLETO.md`: documentacao ampla do projeto.
- `ARQUITETURA_MVC.md`: detalhes da separacao MVC.
- `OBSERVABILIDADE.md`: detalhes de logs e monitoramento.
- `backend/README.md`: detalhes especificos do backend.
- `mobile/bebidas_scan_app/README.md`: detalhes especificos do app Flutter.
