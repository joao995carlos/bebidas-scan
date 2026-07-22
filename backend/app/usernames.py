import re
import unicodedata


USERNAME_PATTERN = re.compile(r"^[a-z0-9._-]{3,80}$")


def normalizar_nome_usuario(valor: str) -> str:
    nome_usuario = valor.strip().lower().lstrip("@")
    if not USERNAME_PATTERN.fullmatch(nome_usuario):
        raise ValueError(
            "Nome de usuário deve ter 3 a 80 caracteres e usar apenas letras, números, ponto, hífen ou sublinhado."
        )
    return nome_usuario


def slug_nome_usuario(valor: str) -> str:
    texto = unicodedata.normalize("NFKD", valor.strip().lower())
    texto = "".join(char for char in texto if not unicodedata.combining(char))
    texto = re.sub(r"[^a-z0-9._-]+", ".", texto)
    texto = re.sub(r"[._-]{2,}", ".", texto).strip("._-")
    if len(texto) < 3:
        texto = f"usuario{texto}"
    return texto[:80]
