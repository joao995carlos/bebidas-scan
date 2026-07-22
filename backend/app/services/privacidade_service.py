from ..lgpd import LGPD_DOCUMENT_VERSION, politica_privacidade_texto, termos_uso_texto


def obter_politica_privacidade() -> dict[str, str]:
    return {"versao": LGPD_DOCUMENT_VERSION, "texto": politica_privacidade_texto()}


def obter_termos_uso() -> dict[str, str]:
    return {"versao": LGPD_DOCUMENT_VERSION, "texto": termos_uso_texto()}

