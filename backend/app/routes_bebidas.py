from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from .database import get_db
from .dependencies import usuario_logado
from .schemas import BebidaCreate, BebidaResposta, BebidaUpdate
from .services.bebida_service import (
    atualizar_bebida_usuario,
    buscar_bebida_por_codigo,
    buscar_bebidas_por_nome,
    criar_bebida_usuario,
)

router = APIRouter(prefix="/bebidas", tags=["bebidas"])


@router.post("", response_model=BebidaResposta)
def criar_bebida(dados: BebidaCreate, db: Session = Depends(get_db), usuario=Depends(usuario_logado)):
    return criar_bebida_usuario(dados, db, usuario)


@router.patch("/{id_bebida}", response_model=BebidaResposta)
def atualizar_bebida(
    id_bebida: int,
    dados: BebidaUpdate,
    db: Session = Depends(get_db),
    usuario=Depends(usuario_logado),
):
    return atualizar_bebida_usuario(id_bebida, dados, db, usuario)


@router.get("/codigo/{codigo_barras}", response_model=BebidaResposta)
async def buscar_por_codigo(
    codigo_barras: str = Path(min_length=6, max_length=80),
    db: Session = Depends(get_db),
):
    return await buscar_bebida_por_codigo(codigo_barras, db)


@router.get("/buscar", response_model=list[BebidaResposta])
async def buscar_por_nome(q: str = Query(min_length=2, max_length=80), db: Session = Depends(get_db)):
    return await buscar_bebidas_por_nome(q, db)
