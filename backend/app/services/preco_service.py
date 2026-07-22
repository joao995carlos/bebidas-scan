from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..logging_config import audit_logger, log_event
from ..models import Bebida, Preco
from ..schemas import PrecoCreate


def registrar_preco_usuario(dados: PrecoCreate, db: Session, usuario) -> Preco:
    bebida = db.query(Bebida).filter(Bebida.id_bebida == dados.id_bebida).first()
    if not bebida:
        raise HTTPException(status_code=404, detail="Bebida não encontrada")

    preco = Preco(id_usuario=usuario.id_usuario, **dados.model_dump())
    db.add(preco)
    db.commit()
    db.refresh(preco)
    log_event(
        audit_logger,
        20,
        "preco_registrado",
        "Preço registrado",
        action="precos.create",
        userId=usuario.id_usuario,
        idPreco=preco.id_preco,
        idBebida=dados.id_bebida,
    )
    return preco


def listar_precos_bebida(id_bebida: int, db: Session) -> list[Preco]:
    return (
        db.query(Preco)
        .filter(Preco.id_bebida == id_bebida)
        .order_by(Preco.data_registro.desc())
        .limit(50)
        .all()
    )

