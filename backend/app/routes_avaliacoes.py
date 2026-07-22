from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .database import get_db
from .dependencies import usuario_logado
from .schemas import AvaliacaoCreate, AvaliacaoResposta
from .services.avaliacao_service import listar_avaliacoes_usuario, salvar_avaliacao_usuario

router = APIRouter(prefix="/avaliacoes", tags=["avaliacoes"])


@router.post("", response_model=AvaliacaoResposta)
def salvar_avaliacao(dados: AvaliacaoCreate, db: Session = Depends(get_db), usuario=Depends(usuario_logado)):
    return salvar_avaliacao_usuario(dados, db, usuario)


@router.get("/minhas", response_model=list[AvaliacaoResposta])
def minhas_avaliacoes(db: Session = Depends(get_db), usuario=Depends(usuario_logado)):
    return listar_avaliacoes_usuario(db, usuario)

