from datetime import date, datetime, timezone

from fastapi import HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..lgpd import anonimizar_usuario, calcular_maioridade, exportar_dados_usuario_csv, registrar_aceite_lgpd
from ..models import Avaliacao, Bebida, Favorito, RefreshToken, Usuario
from ..rate_limit import limitar_auth, registrar_auth_sucesso
from ..security import (
    criar_access_token,
    criar_refresh_token,
    gerar_hash_senha,
    hash_token,
    refresh_expira_em,
    verificar_access_token,
    verificar_senha,
)
from ..usernames import normalizar_nome_usuario
from ..validacao import SENHA_FORTE_MENSAGEM, normalizar_email_valido, validar_senha_forte


def obter_usuario_por_access_token(web_access_token: str | None, db: Session) -> Usuario | None:
    if not web_access_token:
        return None
    payload = verificar_access_token(web_access_token)
    if not payload:
        return None
    try:
        id_usuario = int(payload.get("sub"))
    except (TypeError, ValueError):
        return None
    return db.query(Usuario).filter(Usuario.id_usuario == id_usuario, Usuario.ativo.is_(True)).first()


def emitir_tokens_web(db: Session, usuario: Usuario) -> tuple[str, str]:
    access_token = criar_access_token(usuario.id_usuario, usuario.email)
    refresh_token = criar_refresh_token()
    db.add(
        RefreshToken(
            id_usuario=usuario.id_usuario,
            token_hash=hash_token(refresh_token),
            expiracao=refresh_expira_em(),
        )
    )
    db.commit()
    return access_token, refresh_token


def autenticar_usuario_web(
    request: Request,
    identificador: str,
    senha: str,
    db: Session,
) -> tuple[Usuario, str, str] | None:
    identificador_normalizado = identificador.strip().lower().lstrip("@")
    limitar_auth(request, "web_login", identificador_normalizado)
    usuario = (
        db.query(Usuario)
        .filter(
            Usuario.ativo.is_(True),
            (Usuario.email == identificador_normalizado) | (Usuario.nome_usuario == identificador_normalizado),
        )
        .first()
    )
    if not usuario or not verificar_senha(senha, usuario.senha_hash):
        return None

    registrar_auth_sucesso(request, "web_login", identificador_normalizado)
    access_token, refresh_token = emitir_tokens_web(db, usuario)
    return usuario, access_token, refresh_token


def registrar_usuario_web(
    request: Request,
    nome: str,
    nome_usuario: str,
    email: str,
    senha: str,
    data_nascimento: date,
    aceitou_privacidade: bool,
    aceitou_termos: bool,
    marketing_consentimento: bool,
    db: Session,
) -> tuple[Usuario, str, str]:
    try:
        email_normalizado = normalizar_email_valido(email)
        nome_usuario_normalizado = normalizar_nome_usuario(nome_usuario)
    except ValueError as erro:
        raise ValueError(str(erro))

    limitar_auth(request, "web_registrar", nome_usuario_normalizado)
    try:
        validar_senha_forte(senha)
    except ValueError:
        raise ValueError(SENHA_FORTE_MENSAGEM)
    if not aceitou_privacidade or not aceitou_termos:
        raise ValueError("É necessário aceitar a Política de Privacidade e os Termos de Uso.")
    if not calcular_maioridade(data_nascimento):
        raise ValueError("O Bebidas Scan é destinado a maiores de 18 anos.")

    existente = (
        db.query(Usuario)
        .filter((Usuario.email == email_normalizado) | (Usuario.nome_usuario == nome_usuario_normalizado))
        .first()
    )
    if existente:
        if existente.email == email_normalizado:
            raise ValueError("Este e-mail já está cadastrado.")
        raise ValueError("Este nome de usuário já está cadastrado.")

    usuario = Usuario(
        nome=nome.strip(),
        nome_usuario=nome_usuario_normalizado,
        email=email_normalizado,
        senha_hash=gerar_hash_senha(senha),
    )
    registrar_aceite_lgpd(
        usuario,
        data_nascimento=data_nascimento,
        marketing_consentimento=marketing_consentimento,
    )
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("E-mail ou nome de usuário já cadastrado.")
    db.refresh(usuario)

    registrar_auth_sucesso(request, "web_registrar", nome_usuario_normalizado)
    access_token, refresh_token = emitir_tokens_web(db, usuario)
    return usuario, access_token, refresh_token


def aceitar_lgpd_web(
    db: Session,
    usuario: Usuario,
    data_nascimento: date,
    aceitou_privacidade: bool,
    aceitou_termos: bool,
    marketing_consentimento: bool,
) -> str | None:
    if not aceitou_privacidade or not aceitou_termos:
        return "É necessário aceitar a Política de Privacidade e os Termos de Uso."
    if not calcular_maioridade(data_nascimento):
        return "O Bebidas Scan é destinado a maiores de 18 anos."

    registrar_aceite_lgpd(
        usuario,
        data_nascimento=data_nascimento,
        marketing_consentimento=marketing_consentimento,
    )
    db.commit()
    return None


def exportar_dados_web(db: Session, usuario: Usuario, categorias: list[str]) -> str:
    return exportar_dados_usuario_csv(db, usuario, {item.strip() for item in ",".join(categorias).split(",")})


def anonimizar_conta_web(db: Session, usuario: Usuario, email_confirmacao: str, senha_confirmacao: str) -> None:
    email_validado = normalizar_email_valido(email_confirmacao)
    anonimizar_usuario(db, usuario, email=email_validado, senha=senha_confirmacao)


def revogar_refresh_token_web(db: Session, web_refresh_token: str | None) -> None:
    if not web_refresh_token:
        return
    registro = db.query(RefreshToken).filter(RefreshToken.token_hash == hash_token(web_refresh_token)).first()
    if registro and not registro.revogado:
        registro.revogado = True
        registro.revogado_em = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()


def favoritar_bebida_web(db: Session, usuario: Usuario, id_bebida: int) -> None:
    bebida = db.query(Bebida).filter(Bebida.id_bebida == id_bebida).first()
    if not bebida:
        raise HTTPException(status_code=404, detail="Bebida não encontrada")
    favorito = (
        db.query(Favorito)
        .filter(Favorito.id_usuario == usuario.id_usuario, Favorito.id_bebida == id_bebida)
        .first()
    )
    if not favorito:
        db.add(Favorito(id_usuario=usuario.id_usuario, id_bebida=id_bebida))
        db.commit()


def buscar_bebidas_web(db: Session, q: str, limite: int = 24) -> list[Bebida]:
    if not q.strip():
        return []
    return (
        db.query(Bebida)
        .filter(Bebida.nome.ilike(f"%{q.strip()}%"))
        .order_by(Bebida.nome)
        .limit(limite)
        .all()
    )


def obter_bebida_por_codigo_local(db: Session, codigo: str) -> Bebida | None:
    return db.query(Bebida).filter(Bebida.codigo_barras == codigo).first()


def obter_bebida_web(db: Session, id_bebida: int) -> Bebida | None:
    return db.query(Bebida).filter(Bebida.id_bebida == id_bebida).first()


def listar_favoritos_web(db: Session, usuario: Usuario, limite: int = 100) -> list[Favorito]:
    return (
        db.query(Favorito)
        .filter(Favorito.id_usuario == usuario.id_usuario)
        .order_by(Favorito.data_favorito.desc())
        .limit(limite)
        .all()
    )


def listar_avaliacoes_web(db: Session, usuario: Usuario, limite: int = 100) -> list[Avaliacao]:
    return (
        db.query(Avaliacao)
        .filter(Avaliacao.id_usuario == usuario.id_usuario)
        .order_by(Avaliacao.data_avaliacao.desc())
        .limit(limite)
        .all()
    )


def salvar_avaliacao_web(
    db: Session,
    usuario: Usuario,
    id_bebida: int,
    nota: int,
    comentario: str | None,
    compraria_novamente: bool,
) -> None:
    if nota < 1 or nota > 5:
        raise HTTPException(status_code=400, detail="Nota inválida")
    bebida = db.query(Bebida).filter(Bebida.id_bebida == id_bebida).first()
    if not bebida:
        raise HTTPException(status_code=404, detail="Bebida não encontrada")
    avaliacao = (
        db.query(Avaliacao)
        .filter(Avaliacao.id_usuario == usuario.id_usuario, Avaliacao.id_bebida == id_bebida)
        .first()
    )
    if not avaliacao:
        avaliacao = Avaliacao(id_usuario=usuario.id_usuario, id_bebida=id_bebida)
        db.add(avaliacao)
    avaliacao.nota = nota
    avaliacao.comentario = comentario
    avaliacao.compraria_novamente = compraria_novamente
    db.commit()
