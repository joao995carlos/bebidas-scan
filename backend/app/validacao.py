import re

from pydantic import EmailStr, TypeAdapter


SENHA_FORTE_MENSAGEM = (
    "A senha precisa ter pelo menos 8 caracteres, uma letra maiúscula, "
    "um número e um caractere especial."
)

_email_adapter = TypeAdapter(EmailStr)


def validar_senha_forte(senha: str) -> str:
    if (
        len(senha) < 8
        or not re.search(r"[A-Z]", senha)
        or not re.search(r"\d", senha)
        or not re.search(r"[^A-Za-z0-9]", senha)
    ):
        raise ValueError(SENHA_FORTE_MENSAGEM)
    return senha


def normalizar_email_valido(email: str) -> str:
    valor = email.strip().lower()
    if len(valor) > 150:
        raise ValueError("Informe um e-mail válido.")
    try:
        return str(_email_adapter.validate_python(valor))
    except ValueError as erro:
        raise ValueError("Informe um e-mail válido.") from erro
