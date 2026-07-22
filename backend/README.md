# Backend Bebidas Scan

API FastAPI para cadastro, login, refresh token, logout, perfil, bebidas, avaliacoes, favoritos e precos.

## Rodar localmente

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
```

Site web: `http://localhost:8000/web/`.

Healthcheck: `http://localhost:8000/health`.

Documentacao interativa: `http://localhost:8000/docs`.

## Rodar com Docker

Na raiz do projeto:

```powershell
Copy-Item .env.docker.example .env.docker
docker compose --env-file .env.docker up --build
```

API: `http://localhost:8000`.

Site web: `http://localhost:8000/web/`.

Healthcheck: `http://localhost:8000/health`.

Para publicar em uma VPS, altere `POSTGRES_PASSWORD` e `JWT_SECRET_KEY` no `.env.docker` antes de subir. O banco usa o volume Docker `bebidas_postgres_data`, entao os dados continuam salvos quando os containers reiniciam.

Para Cloudflare Tunnel ou proxy HTTPS, configure tambem:

```env
WEB_COOKIE_SECURE=true
TRUST_PROXY_HEADERS=true
CORS_ORIGINS=https://seudominio.com.br,https://www.seudominio.com.br,https://api.seudominio.com.br
```

## Rotas principais

- `POST /auth/registrar`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `GET /perfil/me`
- `GET /bebidas/codigo/{codigo_barras}`
- `POST /bebidas`
- `POST /avaliacoes`
- `GET /favoritos`
- `POST /favoritos/{id_bebida}`
- `DELETE /favoritos/{id_bebida}`
- `POST /precos`
- `GET /precos/bebida/{id_bebida}`
