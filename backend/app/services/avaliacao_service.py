from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..logging_config import audit_logger, log_event
from ..models import Avaliacao, Bebida
from ..schemas import AvaliacaoCreate


def salvar_avaliacao_usuario(dados: AvaliacaoCreate, db: Session, usuario) -> Avaliacao:
    bebida = db.query(Bebida).filter(Bebida.id_bebida == dados.id_bebida).first()
    if not bebida:
        raise HTTPException(status_code=404, detail="Bebida não encontrada")

    avaliacao = (
        db.query(Avaliacao)
        .filter(Avaliacao.id_usuario == usuario.id_usuario, Avaliacao.id_bebida == dados.id_bebida)
        .first()
    )
    if avaliacao:
        avaliacao.nota = dados.nota
        avaliacao.comentario = dados.comentario
        avaliacao.compraria_novamente = dados.compraria_novamente
    else:
        avaliacao = Avaliacao(id_usuario=usuario.id_usuario, **dados.model_dump())
        db.add(avaliacao)

    db.commit()
    db.refresh(avaliacao)
    log_event(
        audit_logger,
        20,
        "avaliacao_salva",
        "Avaliação salva",
        action="avaliacoes.save",
        userId=usuario.id_usuario,
        idAvaliacao=avaliacao.id_avaliacao,
        idBebida=dados.id_bebida,
        nota=avaliacao.nota,
    )
    return avaliacao


def listar_avaliacoes_usuario(db: Session, usuario) -> list[Avaliacao]:
    return (
        db.query(Avaliacao)
        .filter(Avaliacao.id_usuario == usuario.id_usuario)
        .order_by(Avaliacao.data_avaliacao.desc())
        .all()
    )

