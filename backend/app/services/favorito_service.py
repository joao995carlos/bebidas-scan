from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..models import Bebida, Favorito


def listar_favoritos_usuario(db: Session, usuario) -> list[Favorito]:
    return (
        db.query(Favorito)
        .filter(Favorito.id_usuario == usuario.id_usuario)
        .order_by(Favorito.data_favorito.desc())
        .all()
    )


def favoritar_bebida(id_bebida: int, db: Session, usuario) -> Favorito:
    bebida = db.query(Bebida).filter(Bebida.id_bebida == id_bebida).first()
    if not bebida:
        raise HTTPException(status_code=404, detail="Bebida não encontrada")

    favorito = (
        db.query(Favorito)
        .filter(Favorito.id_usuario == usuario.id_usuario, Favorito.id_bebida == id_bebida)
        .first()
    )
    if favorito:
        return favorito

    favorito = Favorito(id_usuario=usuario.id_usuario, id_bebida=id_bebida)
    db.add(favorito)
    db.commit()
    db.refresh(favorito)
    return favorito


def remover_favorito_usuario(id_bebida: int, db: Session, usuario) -> dict[str, str]:
    favorito = (
        db.query(Favorito)
        .filter(Favorito.id_usuario == usuario.id_usuario, Favorito.id_bebida == id_bebida)
        .first()
    )
    if not favorito:
        raise HTTPException(status_code=404, detail="Favorito não encontrado")

    db.delete(favorito)
    db.commit()
    return {"detail": "Favorito removido"}

