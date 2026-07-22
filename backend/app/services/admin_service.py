from decimal import Decimal, InvalidOperation

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import Avaliacao, Bebida, Favorito, Preco, RefreshToken, Usuario
from ..security import gerar_hash_senha
from ..usernames import normalizar_nome_usuario


def obter_metricas_dashboard(db: Session) -> dict[str, int]:
    return {
        "total_usuarios": db.query(func.count(Usuario.id_usuario)).scalar() or 0,
        "usuarios_ativos": db.query(func.count(Usuario.id_usuario)).filter(Usuario.ativo.is_(True)).scalar() or 0,
        "total_bebidas": db.query(func.count(Bebida.id_bebida)).scalar() or 0,
        "total_avaliacoes": db.query(func.count(Avaliacao.id_avaliacao)).scalar() or 0,
        "total_favoritos": db.query(func.count(Favorito.id_favorito)).scalar() or 0,
        "total_precos": db.query(func.count(Preco.id_preco)).scalar() or 0,
    }


def obter_atividade_recente(db: Session) -> dict[str, list]:
    return {
        "usuarios": db.query(Usuario).order_by(Usuario.data_criacao.desc()).limit(5).all(),
        "bebidas": db.query(Bebida).order_by(Bebida.criada_em.desc()).limit(5).all(),
        "avaliacoes": db.query(Avaliacao).order_by(Avaliacao.data_avaliacao.desc()).limit(5).all(),
        "precos": db.query(Preco).order_by(Preco.data_registro.desc()).limit(5).all(),
    }


def listar_usuarios_admin(db: Session, limite: int = 200) -> list[Usuario]:
    return db.query(Usuario).order_by(Usuario.id_usuario.desc()).limit(limite).all()


def alternar_status_usuario(db: Session, id_usuario: int) -> None:
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if usuario:
        usuario.ativo = not usuario.ativo
        db.commit()


def marcar_email_verificado(db: Session, id_usuario: int) -> None:
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if usuario:
        usuario.email_verificado = True
        db.commit()


def revogar_tokens_usuario_admin(db: Session, id_usuario: int) -> None:
    db.query(RefreshToken).filter(RefreshToken.id_usuario == id_usuario).update(
        {RefreshToken.revogado: True},
        synchronize_session=False,
    )
    db.commit()


def criar_usuario_admin_service(
    db: Session,
    nome: str,
    nome_usuario: str,
    email: str,
    senha: str,
    confirmou_maioridade: bool,
    email_verificado: bool,
    ativo: bool,
) -> None:
    try:
        nome_usuario_normalizado = normalizar_nome_usuario(nome_usuario)
    except ValueError as erro:
        raise HTTPException(status_code=422, detail=str(erro))

    usuario = Usuario(
        nome=nome.strip(),
        nome_usuario=nome_usuario_normalizado,
        email=email.strip().lower(),
        senha_hash=gerar_hash_senha(senha),
        confirmou_maioridade=confirmou_maioridade,
        email_verificado=email_verificado,
        ativo=ativo,
    )
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="E-mail ou nome de usuário já cadastrado")


def excluir_usuario_admin_service(db: Session, id_usuario: int) -> None:
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if usuario:
        db.query(RefreshToken).filter(RefreshToken.id_usuario == id_usuario).delete()
        db.query(Avaliacao).filter(Avaliacao.id_usuario == id_usuario).delete()
        db.query(Favorito).filter(Favorito.id_usuario == id_usuario).delete()
        db.query(Preco).filter(Preco.id_usuario == id_usuario).delete()
        db.delete(usuario)
        db.commit()


def exigir_usuario_e_bebida(db: Session, id_usuario: int, id_bebida: int) -> None:
    usuario_existe = db.query(Usuario.id_usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario_existe:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    bebida_existe = db.query(Bebida.id_bebida).filter(Bebida.id_bebida == id_bebida).first()
    if not bebida_existe:
        raise HTTPException(status_code=404, detail="Bebida não encontrada")


def listar_bebidas_admin(db: Session, q: str = "", limite: int = 200) -> list[Bebida]:
    consulta = db.query(Bebida)
    if q:
        termo = f"%{q.strip()}%"
        consulta = consulta.filter(Bebida.nome.ilike(termo))
    return consulta.order_by(Bebida.id_bebida.desc()).limit(limite).all()


def obter_bebida_admin(db: Session, id_bebida: int) -> Bebida | None:
    return db.query(Bebida).filter(Bebida.id_bebida == id_bebida).first()


def excluir_bebida_admin_service(db: Session, id_bebida: int) -> None:
    bebida = obter_bebida_admin(db, id_bebida)
    if bebida:
        db.query(Avaliacao).filter(Avaliacao.id_bebida == id_bebida).delete()
        db.query(Favorito).filter(Favorito.id_bebida == id_bebida).delete()
        db.query(Preco).filter(Preco.id_bebida == id_bebida).delete()
        db.delete(bebida)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Não é possível excluir bebida com dados vinculados")


def listar_avaliacoes_admin(db: Session, limite: int = 200) -> list[Avaliacao]:
    return db.query(Avaliacao).order_by(Avaliacao.id_avaliacao.desc()).limit(limite).all()


def criar_avaliacao_admin_service(
    db: Session,
    id_usuario: int,
    id_bebida: int,
    nota: int,
    comentario: str,
    compraria_novamente: bool,
) -> None:
    if nota < 1 or nota > 5:
        raise HTTPException(status_code=400, detail="Nota deve ficar entre 1 e 5")
    exigir_usuario_e_bebida(db, id_usuario, id_bebida)

    avaliacao = Avaliacao(
        id_usuario=id_usuario,
        id_bebida=id_bebida,
        nota=nota,
        comentario=comentario.strip() or None,
        compraria_novamente=compraria_novamente,
    )
    db.add(avaliacao)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Este usuário já avaliou esta bebida")


def excluir_avaliacao_admin_service(db: Session, id_avaliacao: int) -> None:
    item = db.query(Avaliacao).filter(Avaliacao.id_avaliacao == id_avaliacao).first()
    if item:
        db.delete(item)
        db.commit()


def listar_favoritos_admin(db: Session, limite: int = 200) -> list[Favorito]:
    return db.query(Favorito).order_by(Favorito.id_favorito.desc()).limit(limite).all()


def criar_favorito_admin_service(db: Session, id_usuario: int, id_bebida: int) -> None:
    exigir_usuario_e_bebida(db, id_usuario, id_bebida)
    favorito = Favorito(id_usuario=id_usuario, id_bebida=id_bebida)
    db.add(favorito)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Este usuário já favoritou esta bebida")


def excluir_favorito_admin_service(db: Session, id_favorito: int) -> None:
    item = db.query(Favorito).filter(Favorito.id_favorito == id_favorito).first()
    if item:
        db.delete(item)
        db.commit()


def listar_precos_admin(db: Session, limite: int = 200) -> list[Preco]:
    return db.query(Preco).order_by(Preco.id_preco.desc()).limit(limite).all()


def criar_preco_admin_service(
    db: Session,
    id_usuario: int,
    id_bebida: int,
    valor: str,
    mercado: str,
    cidade: str,
    estado: str,
) -> None:
    exigir_usuario_e_bebida(db, id_usuario, id_bebida)
    try:
        valor_decimal = Decimal(valor.replace(",", "."))
    except (InvalidOperation, AttributeError):
        raise HTTPException(status_code=400, detail="Valor inválido")
    if valor_decimal < 0:
        raise HTTPException(status_code=400, detail="Valor não pode ser negativo")

    preco = Preco(
        id_usuario=id_usuario,
        id_bebida=id_bebida,
        valor=valor_decimal,
        mercado=mercado.strip() or None,
        cidade=cidade.strip() or None,
        estado=(estado.strip().upper() or None),
    )
    db.add(preco)
    db.commit()


def excluir_preco_admin_service(db: Session, id_preco: int) -> None:
    item = db.query(Preco).filter(Preco.id_preco == id_preco).first()
    if item:
        db.delete(item)
        db.commit()
