from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..lgpd import (
    LGPD_DOCUMENT_VERSION,
    anonimizar_usuario,
    calcular_maioridade,
    exportar_dados_usuario_csv,
    lgpd_pendente,
    registrar_aceite_lgpd,
)
from ..logging_config import audit_logger, log_event, security_logger
from ..schemas import ExclusaoContaRequest, LGPDAceiteRequest, LGPDStatusResposta

CATEGORIAS_EXPORTACAO_PERMITIDAS = {"perfil", "avaliacoes", "favoritos", "precos", "bebidas"}


def obter_status_lgpd(usuario) -> LGPDStatusResposta:
    return LGPDStatusResposta(
        pendente=lgpd_pendente(usuario),
        versao_atual=LGPD_DOCUMENT_VERSION,
        privacidade_versao_aceita=usuario.privacidade_versao_aceita,
        termos_versao_aceita=usuario.termos_versao_aceita,
        lgpd_aceite_em=usuario.lgpd_aceite_em,
    )


def aceitar_lgpd_usuario(dados: LGPDAceiteRequest, db: Session, usuario) -> LGPDStatusResposta:
    if not dados.aceitou_privacidade or not dados.aceitou_termos:
        raise HTTPException(status_code=422, detail="É necessário aceitar a Política de Privacidade e os Termos de Uso.")
    if not calcular_maioridade(dados.data_nascimento):
        raise HTTPException(status_code=422, detail="O Bebidas Scan é destinado a maiores de 18 anos.")

    registrar_aceite_lgpd(
        usuario,
        data_nascimento=dados.data_nascimento,
        marketing_consentimento=dados.marketing_consentimento,
    )
    db.commit()
    log_event(
        audit_logger,
        20,
        "lgpd_aceita",
        "LGPD aceita pelo usuário",
        action="lgpd.accept",
        userId=usuario.id_usuario,
        version=LGPD_DOCUMENT_VERSION,
        marketingConsentimento=dados.marketing_consentimento,
    )
    return obter_status_lgpd(usuario)


def selecionar_categorias_exportacao(categorias: str) -> set[str]:
    selecionadas = {item.strip().lower() for item in categorias.split(",") if item.strip()}
    selecionadas &= CATEGORIAS_EXPORTACAO_PERMITIDAS
    if not selecionadas:
        raise HTTPException(status_code=422, detail="Selecione pelo menos uma categoria válida.")
    return selecionadas


def exportar_dados_usuario(categorias: str, db: Session, usuario) -> str:
    selecionadas = selecionar_categorias_exportacao(categorias)
    conteudo = exportar_dados_usuario_csv(db, usuario, selecionadas)
    log_event(
        audit_logger,
        20,
        "dados_exportados_csv",
        "Usuário exportou dados pessoais em CSV",
        action="privacy.export_csv",
        userId=usuario.id_usuario,
        categorias=sorted(selecionadas),
    )
    return conteudo


def anonimizar_conta_usuario(dados: ExclusaoContaRequest, db: Session, usuario) -> dict[str, str]:
    try:
        anonimizar_usuario(db, usuario, email=str(dados.email), senha=dados.senha)
    except ValueError as erro:
        log_event(
            security_logger,
            30,
            "anonimizacao_confirmacao_falhou",
            "Falha na confirmação para anonimizar conta",
            action="privacy.anonymize",
            userId=usuario.id_usuario,
        )
        raise HTTPException(status_code=403, detail=str(erro))

    log_event(
        audit_logger,
        20,
        "conta_anonimizada",
        "Conta anonimizada pelo usuário",
        action="privacy.anonymize",
        userId=usuario.id_usuario,
    )
    return {"detail": "Conta anonimizada e desativada com sucesso."}

