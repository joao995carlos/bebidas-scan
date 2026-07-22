from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from .database import get_db
from .dependencies import usuario_logado
from .schemas import ExclusaoContaRequest, LGPDAceiteRequest, LGPDStatusResposta, UsuarioResposta
from .services.perfil_service import (
    aceitar_lgpd_usuario,
    anonimizar_conta_usuario,
    exportar_dados_usuario,
    obter_status_lgpd,
)

router = APIRouter(prefix="/perfil", tags=["perfil"])


@router.get("/me", response_model=UsuarioResposta)
def perfil(usuario=Depends(usuario_logado)):
    return usuario


@router.get("/lgpd/status", response_model=LGPDStatusResposta)
def status_lgpd(usuario=Depends(usuario_logado)):
    return obter_status_lgpd(usuario)


@router.post("/lgpd/aceitar", response_model=LGPDStatusResposta)
def aceitar_lgpd(
    dados: LGPDAceiteRequest,
    db: Session = Depends(get_db),
    usuario=Depends(usuario_logado),
):
    return aceitar_lgpd_usuario(dados, db, usuario)


@router.get("/exportar.csv")
def exportar_dados(
    categorias: str = Query("perfil,avaliacoes,favoritos,precos,bebidas", max_length=120),
    db: Session = Depends(get_db),
    usuario=Depends(usuario_logado),
):
    conteudo = exportar_dados_usuario(categorias, db, usuario)
    return Response(
        content=conteudo,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="meus-dados-bebidas-scan.csv"'},
    )


@router.post("/anonimizar")
def anonimizar_conta(
    dados: ExclusaoContaRequest,
    db: Session = Depends(get_db),
    usuario=Depends(usuario_logado),
):
    return anonimizar_conta_usuario(dados, db, usuario)

