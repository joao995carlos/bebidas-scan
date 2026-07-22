# Bebidas Scan

Aplicativo para escanear bebidas por codigo de barras, consultar dados, avaliar, favoritar e registrar precos.

## Estrutura

- `backend/`: API FastAPI com JWT, refresh token, SQLAlchemy e integracao com Open Food Facts.
- `mobile/bebidas_scan_app/`: app Flutter com login, cadastro, scanner, detalhes da bebida e avaliacao.

## Backend

### Com Docker: API + Postgres

Na raiz do projeto:

```powershell
Copy-Item .env.docker.example .env.docker
docker compose --env-file .env.docker up --build
```

Isso sobe:

- Pagina inicial em `http://localhost:8000/`
- App web protegido por login em `http://localhost:8000/web/`
- API FastAPI em `http://localhost:8000`
- Healthcheck em `http://localhost:8000/health`
- Postgres em container interno
- volume Docker `bebidasscan_bebidas_postgres_data` para persistir o banco

Antes de publicar em uma VPS, altere `POSTGRES_PASSWORD` e `JWT_SECRET_KEY` no `.env.docker`.

### Publicar com dominio/Cloudflare

Para usar atras de Cloudflare Tunnel ou proxy HTTPS, configure no `.env.docker`:

```env
CORS_ORIGINS=https://seudominio.com.br,https://www.seudominio.com.br,https://api.seudominio.com.br
WEB_COOKIE_SECURE=true
TRUST_PROXY_HEADERS=true
FORWARDED_ALLOW_IPS=*
RESEND_API_KEY=re_sua_chave
EMAIL_FROM=Bebidas Scan <nao-responda@bebidasscan.com.br>
PASSWORD_RESET_BASE_URL=https://api.bebidasscan.com.br/web/resetar-senha
```

Use `FORWARDED_ALLOW_IPS=*` apenas quando o acesso público passar exclusivamente por um proxy confiável, como Cloudflare Tunnel. Se a porta da API ficar aberta diretamente na internet, restrinja esse valor aos IPs do proxy.

Para recuperacao de senha, crie e verifique `bebidasscan.com.br` no Resend. Depois copie para a Cloudflare os registros DNS exibidos pelo Resend e crie uma API key. O remetente em `EMAIL_FROM` precisa usar um dominio verificado.

Depois reconstrua:

```powershell
docker compose --env-file .env.docker up -d --build
```

Use `https://seudominio.com.br/` para a pagina inicial publica. O botao leva para `https://seudominio.com.br/web/login`, e o app web exige login. Para o app mobile, aponte `API_BASE_URL` para `https://api.seudominio.com.br` ou para o mesmo dominio, se ele tambem expuser a API.

Para parar sem apagar dados:

```powershell
docker compose --env-file .env.docker down
```

Para apagar tambem o banco/volume:

```powershell
docker compose --env-file .env.docker down -v
```

### Sem Docker

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Configure `DATABASE_URL` em `backend/.env`. Em desenvolvimento, a API cria as tabelas automaticamente ao iniciar.

## Mobile

Instale Flutter e Android SDK, depois:

```powershell
cd mobile\bebidas_scan_app
flutter create --platforms=android .
flutter pub get
flutter run
```

Para gerar APK apontando para uma API especifica:

```powershell
flutter build apk --release --dart-define=API_BASE_URL=http://SEU_IP_OU_DOMINIO:8000
```

Para dominio HTTPS:

```powershell
flutter build apk --release --dart-define=API_BASE_URL=https://api.seudominio.com.br
```
