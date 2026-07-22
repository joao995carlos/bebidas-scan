from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .database import get_db
from .dependencies import usuario_logado
from .schemas import PrecoCreate, PrecoResposta
from .services.preco_service import listar_precos_bebida, registrar_preco_usuario

router = APIRouter(prefix="/precos", tags=["precos"])


@router.post("", response_model=PrecoResposta)
def registrar_preco(dados: PrecoCreate, db: Session = Depends(get_db), usuario=Depends(usuario_logado)):
    return registrar_preco_usuario(dados, db, usuario)


@router.get("/bebida/{id_bebida}", response_model=list[PrecoResposta])
def listar_precos(id_bebida: int, db: Session = Depends(get_db), usuario=Depends(usuario_logado)):
    return listar_precos_bebida(id_bebida, db)

