from html import escape
from urllib.parse import quote

from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session

from .database import get_db
from .email_service import enviar_email_transacional_seguro
from .schemas import ConfirmarResetSenhaRequest
from .services.auth_service import confirmar_reset_senha

router = APIRouter(tags=["password-reset"])


def _reset_layout(title: str, content: str) -> HTMLResponse:
    return HTMLResponse(
        f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} - Bebidas Scan</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f2ea;
      --panel: #fffdf9;
      --ink: #191512;
      --muted: #665b53;
      --line: #dfd2c4;
      --accent: #111111;
      --ok: #1f7a5c;
      --danger: #b3261e;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      font-family: Arial, Helvetica, sans-serif;
      background:
        linear-gradient(rgba(247, 242, 234, .84), rgba(247, 242, 234, .96)),
        url("https://images.unsplash.com/photo-1605270012917-bf157c5a9541?auto=format&fit=crop&w=1600&q=80") center / cover fixed;
      color: var(--ink);
    }}
    main {{
      width: min(560px, calc(100% - 32px));
      min-height: 100vh;
      margin: 0 auto;
      display: grid;
      align-content: center;
      padding: 32px 0;
    }}
    section {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: clamp(22px, 6vw, 40px);
      box-shadow: 0 20px 70px rgba(43, 31, 22, .18);
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: clamp(2rem, 8vw, 3.2rem);
      line-height: 1;
      letter-spacing: 0;
    }}
    p {{
      color: var(--muted);
      line-height: 1.6;
      margin: 0 0 14px;
    }}
    label {{
      display: block;
      margin: 18px 0 8px;
      font-weight: 800;
    }}
    input {{
      width: 100%;
      min-height: 48px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px 14px;
      font-size: 1rem;
      background: #fff;
      color: var(--ink);
    }}
    button, .button {{
      display: inline-flex;
      justify-content: center;
      align-items: center;
      min-height: 48px;
      width: 100%;
      border: 2px solid var(--accent);
      border-radius: 999px;
      background: var(--accent);
      color: #fff;
      padding: 12px 18px;
      margin-top: 18px;
      font-weight: 800;
      font-size: 1rem;
      text-decoration: none;
      cursor: pointer;
    }}
    .success {{ color: var(--ok); font-weight: 800; }}
    .error {{ color: var(--danger); font-weight: 800; }}
    .muted {{ font-size: .94rem; }}
  </style>
</head>
<body>
  <main>
    {content}
  </main>
</body>
</html>"""
    )


def _reset_form(token: str, mensagem: str = "", erro: str = "") -> str:
    mensagem_html = f'<p class="success">{escape(mensagem)}</p>' if mensagem else ""
    erro_html = f'<p class="error" role="alert">{escape(erro)}</p>' if erro else ""
    if mensagem:
        return f"""
<section>
  <h1>Senha redefinida</h1>
  {mensagem_html}
  <p>Agora abra o app e entre novamente usando sua nova senha.</p>
  <a class="button" href="/">Voltar para a entrada</a>
</section>
"""
    return f"""
<section>
  <h1>Redefinir senha</h1>
  <p>Crie uma nova senha para acessar sua conta no Bebidas Scan.</p>
  {erro_html}
  <form method="post" action="/resetar-senha">
    <input type="hidden" name="token" value="{escape(token)}">
    <label for="nova_senha">Nova senha</label>
    <input id="nova_senha" name="nova_senha" type="password" required minlength="8" maxlength="100" autocomplete="new-password">
    <p class="muted">Use pelo menos 8 caracteres, uma letra maiúscula, um número e um caractere especial.</p>
    <button type="submit">Salvar nova senha</button>
  </form>
</section>
"""


@router.get("/resetar-senha", response_class=HTMLResponse)
def reset_senha_form(token: str = Query("", min_length=1, max_length=300)):
    return _reset_layout("Redefinir senha", _reset_form(token))


@router.post("/resetar-senha", response_class=HTMLResponse)
def reset_senha_post(
    background_tasks: BackgroundTasks,
    token: str = Form(...),
    nova_senha: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        confirmar_reset_senha(
            ConfirmarResetSenhaRequest(token=token, nova_senha=nova_senha),
            db,
            lambda usuario: background_tasks.add_task(
                enviar_email_transacional_seguro,
                "senha_redefinida",
                email=usuario.email,
                nome=usuario.nome,
                user_id=usuario.id_usuario,
            ),
        )
    except HTTPException as erro:
        return _reset_layout("Redefinir senha", _reset_form(token, erro=str(erro.detail)))
    except ValidationError:
        return _reset_layout(
            "Redefinir senha",
            _reset_form(
                token,
                erro="Use uma senha com pelo menos 8 caracteres, uma letra maiúscula, um número e um caractere especial.",
            ),
        )
    return _reset_layout(
        "Senha redefinida",
        _reset_form("", mensagem="Senha redefinida com sucesso."),
    )


@router.get("/web/resetar-senha", include_in_schema=False)
def reset_senha_legado(token: str = Query("", min_length=1, max_length=300)):
    return HTMLResponse(
        status_code=308,
        headers={"Location": f"/resetar-senha?token={quote(token)}"},
        content="",
    )
