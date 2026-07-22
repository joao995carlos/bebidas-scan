from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .database import get_db
from .dependencies import usuario_logado
from .schemas import FavoritoResposta
from .services.favorito_service import favoritar_bebida, listar_favoritos_usuario, remover_favorito_usuario

router = APIRouter(prefix="/favoritos", tags=["favoritos"])


@router.get("", response_model=list[FavoritoResposta])
def listar_favoritos(db: Session = Depends(get_db), usuario=Depends(usuario_logado)):
    return listar_favoritos_usuario(db, usuario)


@router.post("/{id_bebida}", response_model=FavoritoResposta)
def favoritar(id_bebida: int, db: Session = Depends(get_db), usuario=Depends(usuario_logado)):
    return favoritar_bebida(id_bebida, db, usuario)


@router.delete("/{id_bebida}")
def remover_favorito(id_bebida: int, db: Session = Depends(get_db), usuario=Depends(usuario_logado)):
    return remover_favorito_usuario(id_bebida, db, usuario)

