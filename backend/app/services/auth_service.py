from datetime import datetime, timezone

from fastapi import HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..lgpd import calcular_maioridade, registrar_aceite_lgpd
from ..logging_config import audit_logger, log_event, security_logger
from ..models import RefreshToken, Usuario
from ..rate_limit import limitar_auth, registrar_auth_sucesso
from ..schemas import AccessTokenResposta, RefreshRequest, TokenResposta, UsuarioCreate, UsuarioLogin
from ..security import (
    criar_access_token,
    criar_refresh_token,
    gerar_hash_senha,
    hash_token,
    refresh_expira_em,
    verificar_senha,
)
from ..usernames import normalizar_nome_usuario


def emitir_tokens(db: Session, usuario: Usuario) -> TokenResposta:
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
    return TokenResposta(access_token=access_token, refresh_token=refresh_token, usuario=usuario)


def registrar_usuario(dados: UsuarioCreate, request: Request, db: Session) -> TokenResposta:
    email = str(dados.email).strip().lower()
    if not dados.aceitou_privacidade or not dados.aceitou_termos:
        raise HTTPException(status_code=422, detail="É necessário aceitar a Política de Privacidade e os Termos de Uso.")
    if not calcular_maioridade(dados.data_nascimento):
        raise HTTPException(status_code=422, detail="O Bebidas Scan é destinado a maiores de 18 anos.")

    try:
        nome_usuario = normalizar_nome_usuario(dados.nome_usuario)
    except ValueError as erro:
        raise HTTPException(status_code=422, detail=str(erro))

    limitar_auth(request, "registrar", nome_usuario)
    usuario_existente = (
        db.query(Usuario)
        .filter((Usuario.email == email) | (Usuario.nome_usuario == nome_usuario))
        .first()
    )
    if usuario_existente:
        if usuario_existente.email == email:
            raise HTTPException(status_code=400, detail="E-mail já cadastrado")
        raise HTTPException(status_code=400, detail="Nome de usuário já cadastrado")

    usuario = Usuario(
        nome=dados.nome.strip(),
        nome_usuario=nome_usuario,
        email=email,
        senha_hash=gerar_hash_senha(dados.senha),
    )
    registrar_aceite_lgpd(
        usuario,
        data_nascimento=dados.data_nascimento,
        marketing_consentimento=dados.marketing_consentimento,
    )
    db.add(usuario)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="E-mail ou nome de usuário já cadastrado")
    db.refresh(usuario)

    registrar_auth_sucesso(request, "registrar", nome_usuario)
    log_event(
        audit_logger,
        20,
        "usuario_registrado",
        "Usuário registrado",
        action="auth.register",
        userId=usuario.id_usuario,
    )
    return emitir_tokens(db, usuario)


def autenticar_usuario(dados: UsuarioLogin, request: Request, db: Session) -> TokenResposta:
    identificador = dados.identificador.strip().lower().lstrip("@")
    limitar_auth(request, "login", identificador)
    usuario = (
        db.query(Usuario)
        .filter(
            Usuario.ativo.is_(True),
            (Usuario.email == identificador) | (Usuario.nome_usuario == identificador),
        )
        .first()
    )
    if not usuario or not verificar_senha(dados.senha, usuario.senha_hash):
        log_event(
            security_logger,
            30,
            "login_falhou",
            "Falha de login",
            action="auth.login",
            client=request.client.host if request.client else "unknown",
            identity=identificador,
        )
        raise HTTPException(status_code=401, detail="Nome de usuário ou senha inválidos")

    registrar_auth_sucesso(request, "login", identificador)
    log_event(
        audit_logger,
        20,
        "login_sucesso",
        "Login realizado com sucesso",
        action="auth.login",
        userId=usuario.id_usuario,
    )
    return emitir_tokens(db, usuario)


def renovar_access_token(dados: RefreshRequest, db: Session) -> AccessTokenResposta:
    token_hash = hash_token(dados.refresh_token)
    registro = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revogado.is_(False),
            RefreshToken.expiracao > datetime.now(timezone.utc).replace(tzinfo=None),
        )
        .first()
    )
    if not registro:
        raise HTTPException(status_code=401, detail="Refresh token inválido ou expirado")

    usuario = (
        db.query(Usuario)
        .filter(Usuario.id_usuario == registro.id_usuario, Usuario.ativo.is_(True))
        .first()
    )
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuário não encontrado ou inativo")

    return AccessTokenResposta(access_token=criar_access_token(usuario.id_usuario, usuario.email))


def encerrar_sessao(dados: RefreshRequest, db: Session) -> dict[str, str]:
    registro = db.query(RefreshToken).filter(RefreshToken.token_hash == hash_token(dados.refresh_token)).first()
    if registro and not registro.revogado:
        registro.revogado = True
        registro.revogado_em = datetime.now(timezone.utc).replace(tzinfo=None)
        db.commit()
        log_event(
            audit_logger,
            20,
            "logout",
            "Logout realizado",
            action="auth.logout",
            userId=registro.id_usuario,
        )
    return {"detail": "Logout realizado"}
