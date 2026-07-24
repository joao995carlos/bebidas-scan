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

## E-mail com Resend

O backend usa o Resend para enviar links de recuperacao de senha. Configure o dominio no painel do Resend, copie os registros DNS exatamente como ele mostrar para o DNS da Cloudflare e, depois da verificacao, preencha:

```env
RESEND_API_KEY=re_sua_chave
EMAIL_FROM=Bebidas Scan <nao-responda@bebidasscan.com.br>
PASSWORD_RESET_BASE_URL=https://api.bebidasscan.com.br/resetar-senha
APP_WEB_URL=https://bebidasscan.com.br
```

Nao grave a chave `RESEND_API_KEY` no Git. Ela deve ficar somente no `.env`, `.env.docker` ou no provedor de hospedagem.

E-mails transacionais enviados:

- boas-vindas apos cadastro no app ou web;
- link de recuperacao de senha;
- aviso de senha alterada;
- aviso de senha redefinida.

A página pública de redefinição fica em `/resetar-senha`, separada do app web em `/web`.

## Rotas principais

- `POST /auth/registrar`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`
- `POST /auth/alterar-senha`
- `POST /auth/solicitar-reset-senha`
- `POST /auth/confirmar-reset-senha`
- `GET /perfil/me`
- `GET /bebidas/codigo/{codigo_barras}`
- `POST /bebidas`
- `POST /avaliacoes`
- `GET /favoritos`
- `POST /favoritos/{id_bebida}`
- `DELETE /favoritos/{id_bebida}`
- `POST /precos`
- `GET /precos/bebida/{id_bebida}`
