import re
import unicodedata


def normalizar_tipo_bebida(valor: str | None) -> str:
    texto = (valor or "").strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(caractere for caractere in texto if not unicodedata.combining(caractere))


def bebida_e_cachaca(valor: str | None) -> bool:
    tipo = normalizar_tipo_bebida(valor)
    return bool(re.search(r"\b(cachaca|aguardente)\b", tipo))
