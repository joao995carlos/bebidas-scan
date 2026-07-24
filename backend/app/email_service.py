import os
from html import escape
from typing import Literal

import httpx

from .logging_config import app_logger, log_event

RESEND_API_URL = "https://api.resend.com/emails"


class EmailNaoConfigurado(RuntimeError):
    pass


TipoEmail = Literal[
    "boas_vindas",
    "reset_senha",
    "senha_alterada",
    "senha_redefinida",
]


def _resend_api_key() -> str:
    return os.getenv("RESEND_API_KEY", "").strip()


def _email_from() -> str:
    return os.getenv("EMAIL_FROM", "Bebidas Scan <nao-responda@bebidasscan.com.br>").strip()


def _password_reset_base_url() -> str:
    return os.getenv(
        "PASSWORD_RESET_BASE_URL",
        "https://api.bebidasscan.com.br/web/resetar-senha",
    ).strip()


def _app_web_url() -> str:
    return os.getenv("APP_WEB_URL", "https://bebidasscan.com.br").strip()


async def _enviar_resend(*, email: str, subject: str, html: str) -> None:
    api_key = _resend_api_key()
    if not api_key:
        raise EmailNaoConfigurado("RESEND_API_KEY não configurada")

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            RESEND_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": _email_from(),
                "to": [email],
                "subject": subject,
                "html": html,
            },
        )
        response.raise_for_status()


def _html_base(*, titulo: str, conteudo: str) -> str:
    return f"""
    <div style="font-family: Arial, sans-serif; color: #1f1a17; line-height: 1.55;">
      <h1 style="color: #5a2b14;">{escape(titulo)}</h1>
      {conteudo}
      <hr style="border: none; border-top: 1px solid #eadfd5; margin: 24px 0;">
      <p style="font-size: 12px; color: #6f625b;">
        Este é um e-mail transacional do Bebidas Scan.
      </p>
    </div>
    """


def _botao(link: str, texto: str) -> str:
    return f"""
    <p>
      <a href="{escape(link)}"
         style="background: #111111; color: #ffffff; display: inline-block; padding: 12px 18px; border-radius: 10px; text-decoration: none;">
        {escape(texto)}
      </a>
    </p>
    """


async def enviar_email_boas_vindas(*, email: str, nome: str) -> None:
    nome_seguro = escape(nome.strip() or "usuário")
    conteudo = f"""
    <p>Olá, {nome_seguro}.</p>
    <p>Sua conta no Bebidas Scan foi criada com sucesso.</p>
    <p>Agora você pode escanear bebidas, salvar favoritos, avaliar produtos e manter seu histórico com mais segurança.</p>
    {_botao(_app_web_url(), "Abrir Bebidas Scan")}
    """
    await _enviar_resend(
        email=email,
        subject="Bem-vindo ao Bebidas Scan",
        html=_html_base(titulo="Bem-vindo ao Bebidas Scan", conteudo=conteudo),
    )


async def enviar_email_reset_senha(*, email: str, token: str) -> None:
    link = f"{_password_reset_base_url()}?token={token}"
    conteudo = f"""
    <p>Recebemos uma solicitação para redefinir sua senha no Bebidas Scan.</p>
    {_botao(link, "Redefinir minha senha")}
    <p>Esse link expira em 30 minutos. Se você não pediu isso, ignore este e-mail.</p>
    """
    await _enviar_resend(
        email=email,
        subject="Redefinição de senha - Bebidas Scan",
        html=_html_base(titulo="Redefinir senha", conteudo=conteudo),
    )


async def enviar_email_senha_alterada(*, email: str, nome: str) -> None:
    nome_seguro = escape(nome.strip() or "usuário")
    conteudo = f"""
    <p>Olá, {nome_seguro}.</p>
    <p>Sua senha do Bebidas Scan foi alterada com sucesso.</p>
    <p>Se você não fez essa alteração, solicite uma recuperação de senha imediatamente.</p>
    """
    await _enviar_resend(
        email=email,
        subject="Senha alterada - Bebidas Scan",
        html=_html_base(titulo="Senha alterada", conteudo=conteudo),
    )


async def enviar_email_senha_redefinida(*, email: str, nome: str) -> None:
    nome_seguro = escape(nome.strip() or "usuário")
    conteudo = f"""
    <p>Olá, {nome_seguro}.</p>
    <p>Sua senha do Bebidas Scan foi redefinida com sucesso.</p>
    <p>Se você não fez essa redefinição, solicite uma nova recuperação de senha e revise a segurança da sua conta.</p>
    """
    await _enviar_resend(
        email=email,
        subject="Senha redefinida - Bebidas Scan",
        html=_html_base(titulo="Senha redefinida", conteudo=conteudo),
    )


async def enviar_email_transacional_seguro(
    tipo: TipoEmail,
    *,
    email: str,
    nome: str = "",
    token: str = "",
    user_id: int | None = None,
) -> None:
    try:
        if tipo == "boas_vindas":
            await enviar_email_boas_vindas(email=email, nome=nome)
        elif tipo == "reset_senha":
            await enviar_email_reset_senha(email=email, token=token)
        elif tipo == "senha_alterada":
            await enviar_email_senha_alterada(email=email, nome=nome)
        elif tipo == "senha_redefinida":
            await enviar_email_senha_redefinida(email=email, nome=nome)
    except EmailNaoConfigurado:
        log_event(
            app_logger,
            30,
            f"email_{tipo}_nao_configurado",
            "E-mail transacional não enviado porque o Resend não está configurado",
            action=f"email.{tipo}",
            userId=user_id,
        )
    except httpx.HTTPError as erro:
        log_event(
            app_logger,
            40,
            f"email_{tipo}_falhou",
            "Falha ao enviar e-mail transacional",
            action=f"email.{tipo}",
            userId=user_id,
            errorType=type(erro).__name__,
        )
