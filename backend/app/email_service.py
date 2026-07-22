import os

import httpx

from .logging_config import app_logger, log_event

RESEND_API_URL = "https://api.resend.com/emails"
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_FROM = os.getenv("EMAIL_FROM", "Bebidas Scan <nao-responda@bebidasscan.com.br>")
PASSWORD_RESET_BASE_URL = os.getenv(
    "PASSWORD_RESET_BASE_URL",
    "https://api.bebidasscan.com.br/web/resetar-senha",
)


class EmailNaoConfigurado(RuntimeError):
    pass


async def enviar_email_reset_senha(*, email: str, token: str) -> None:
    if not RESEND_API_KEY:
        raise EmailNaoConfigurado("RESEND_API_KEY não configurada")

    link = f"{PASSWORD_RESET_BASE_URL}?token={token}"
    html = f"""
    <p>Olá,</p>
    <p>Recebemos uma solicitação para redefinir sua senha no Bebidas Scan.</p>
    <p><a href="{link}">Redefinir minha senha</a></p>
    <p>Esse link expira em 30 minutos. Se você não pediu isso, ignore este e-mail.</p>
    """

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                RESEND_API_URL,
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "from": EMAIL_FROM,
                    "to": [email],
                    "subject": "Redefinição de senha - Bebidas Scan",
                    "html": html,
                },
            )
            response.raise_for_status()
    except httpx.HTTPError as erro:
        log_event(
            app_logger,
            40,
            "email_reset_senha_falhou",
            "Falha ao enviar e-mail de reset de senha",
            action="email.password_reset",
            errorType=type(erro).__name__,
        )
        raise
