import os
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from . import models
from .database import Base, SessionLocal, engine
from .lgpd import limpar_refresh_tokens_antigos
from .logging_config import (
    app_logger,
    configurar_logging,
    log_event,
    reset_request_id,
    security_logger,
    set_request_id,
)
from .migrations import aplicar_migracoes_leves
from .controllers.admin_controller import router as admin_router
from .controllers.auth_controller import router as auth_router
from .controllers.avaliacoes_controller import router as avaliacoes_router
from .controllers.bebidas_controller import router as bebidas_router
from .controllers.favoritos_controller import router as favoritos_router
from .controllers.perfil_controller import router as perfil_router
from .controllers.precos_controller import router as precos_router
from .controllers.privacidade_controller import router as privacidade_router
from .controllers.web_controller import router as web_router
from .routes_password_reset import router as password_reset_router

Base.metadata.create_all(bind=engine)
aplicar_migracoes_leves(engine)
configurar_logging()
with SessionLocal() as session:
    limpar_refresh_tokens_antigos(session)

app = FastAPI(title="Bebidas Scan API", version="0.1.0")
MAX_REQUEST_BODY_BYTES = int(os.getenv("MAX_REQUEST_BODY_BYTES", "1048576"))


@app.middleware("http")
async def limitar_tamanho_requisicao(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            tamanho = int(content_length)
        except ValueError:
            tamanho = 0
        if tamanho > MAX_REQUEST_BODY_BYTES:
            log_event(
                security_logger,
                30,
                "request_too_large",
                "Requisição bloqueada por tamanho excessivo",
                action="http_request",
                path=request.url.path,
                size=tamanho,
                client=request.client.host if request.client else "unknown",
            )
            return JSONResponse(
                status_code=413,
                content={"detail": "Requisição muito grande"},
            )
    return await call_next(request)


@app.middleware("http")
async def contexto_observabilidade(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request_token = set_request_id(request_id)
    inicio = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception:
        log_event(
            app_logger,
            40,
            "unhandled_exception",
            "Erro não tratado durante requisição HTTP",
            action="http_request",
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else "unknown",
            exc_info=True,
        )
        raise
    finally:
        duracao_ms = round((time.perf_counter() - inicio) * 1000, 2)
        level = 30 if status_code >= 400 else 20
        log_event(
            app_logger,
            level,
            "request_completed",
            "Requisição HTTP concluída",
            action="http_request",
            method=request.method,
            path=request.url.path,
            statusCode=status_code,
            durationMs=duracao_ms,
            client=request.client.host if request.client else "unknown",
        )
        reset_request_id(request_token)

cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(perfil_router)
app.include_router(bebidas_router)
app.include_router(avaliacoes_router)
app.include_router(favoritos_router)
app.include_router(precos_router)
app.include_router(privacidade_router)
app.include_router(admin_router)
app.include_router(password_reset_router)
app.include_router(web_router)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def raiz():
    return HTMLResponse(
        """<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Bebidas Scan</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f6f2eb;
      --ink: #15120f;
      --muted: #5f574f;
      --line: #d7cbbd;
      --disabled: #b8b8b8;
      --disabled-ink: #f3f3f3;
      --accent: #1f7a5c;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      background:
        linear-gradient(rgba(246, 242, 235, .82), rgba(246, 242, 235, .92)),
        url("https://images.unsplash.com/photo-1514933651103-005eec06c04b?auto=format&fit=crop&w=1800&q=80") center / cover fixed;
      color: var(--ink);
      min-height: 100vh;
    }
    main {
      width: min(920px, calc(100% - 32px));
      min-height: 100vh;
      margin: 0 auto;
      display: grid;
      align-content: center;
      padding: 48px 0;
    }
    section {
      background: rgba(255, 255, 255, .94);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: clamp(22px, 5vw, 48px);
      box-shadow: 0 22px 70px rgba(35, 28, 21, .18);
    }
    h1 {
      margin: 0 0 12px;
      font-size: clamp(2.25rem, 7vw, 5.5rem);
      line-height: .92;
      letter-spacing: 0;
    }
    p {
      color: var(--muted);
      font-size: 1.05rem;
      line-height: 1.65;
      margin: 0 0 14px;
      max-width: 720px;
    }
    ul {
      margin: 20px 0;
      padding-left: 20px;
      color: var(--muted);
      line-height: 1.65;
    }
    label {
      display: flex;
      gap: 10px;
      align-items: flex-start;
      margin: 24px 0 18px;
      font-weight: 700;
    }
    input[type="checkbox"] {
      width: 20px;
      height: 20px;
      margin-top: 1px;
      accent-color: var(--accent);
      flex: 0 0 auto;
    }
    .button {
      display: inline-flex;
      justify-content: center;
      align-items: center;
      min-height: 48px;
      padding: 13px 24px;
      border-radius: 999px;
      border: 2px solid #000;
      background: #000;
      color: #fff;
      text-decoration: none;
      font-weight: 800;
      transition: transform .16s ease, background .16s ease, border-color .16s ease;
    }
    .button[aria-disabled="true"] {
      pointer-events: none;
      border-color: var(--disabled);
      background: var(--disabled);
      color: var(--disabled-ink);
    }
    .button:not([aria-disabled="true"]):hover {
      transform: translateY(-1px);
    }
  </style>
</head>
<body>
  <main>
    <section aria-labelledby="titulo">
      <h1 id="titulo">Bebidas Scan</h1>
      <p>
        O Bebidas Scan ajuda você a consultar bebidas por código de barras,
        completar informações de rótulo, salvar favoritos e registrar avaliações.
      </p>
      <p>
        Na versão web, o acesso ao aplicativo exige login para proteger os dados
        cadastrados e manter avaliações, favoritos e histórico vinculados a uma conta.
      </p>
      <ul>
        <li>Use o scanner para buscar bebidas pelo código de barras.</li>
        <li>Cadastre ou complete dados quando uma bebida não for encontrada.</li>
        <li>Avalie, favorite e acompanhe suas bebidas após entrar.</li>
      </ul>
      <label for="confirmacao">
        <input id="confirmacao" type="checkbox">
        Li e entendi que preciso entrar para usar o Bebidas Scan pela web.
      </label>
      <a id="entrar" class="button" href="/web/login" aria-disabled="true">Ir para o app</a>
    </section>
  </main>
  <script>
    const checkbox = document.getElementById('confirmacao');
    const entrar = document.getElementById('entrar');
    checkbox.addEventListener('change', () => {
      entrar.setAttribute('aria-disabled', checkbox.checked ? 'false' : 'true');
    });
  </script>
</body>
</html>"""
    )


@app.get("/health")
def healthcheck():
    return {"app": "Bebidas Scan API", "status": "ok"}
