from datetime import datetime, timezone
from datetime import timedelta
from typing import Callable

from fastapi import HTTPException, Request
import httpx
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..lgpd import calcular_maioridade, registrar_aceite_lgpd
from ..logging_config import app_logger, audit_logger, log_event, security_logger
from ..models import RefreshToken, Usuario
from ..models import PasswordResetToken
from ..rate_limit import limitar_auth, registrar_auth_sucesso
from ..schemas import (
    AccessTokenResposta,
    AlterarSenhaRequest,
    ConfirmarResetSenhaRequest,
    RefreshRequest,
    SolicitarResetSenhaRequest,
    TokenResposta,
    UsuarioCreate,
    UsuarioLogin,
)
from ..security import (
    criar_access_token,
    criar_refresh_token,
    gerar_hash_senha,
    hash_token,
    refresh_expira_em,
    verificar_senha,
)
from ..email_service import EmailNaoConfigurado, enviar_email_reset_senha
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


def revogar_tokens_usuario(db: Session, id_usuario: int) -> None:
    agora = datetime.now(timezone.utc).replace(tzinfo=None)
    tokens = (
        db.query(RefreshToken)
        .filter(RefreshToken.id_usuario == id_usuario, RefreshToken.revogado.is_(False))
        .all()
    )
    for token in tokens:
        token.revogado = True
        token.revogado_em = agora


def alterar_senha_usuario(dados: AlterarSenhaRequest, db: Session, usuario) -> dict[str, str]:
    if not verificar_senha(dados.senha_atual, usuario.senha_hash):
        log_event(
            security_logger,
            30,
            "alteracao_senha_confirmacao_falhou",
            "Senha atual inválida ao alterar senha",
            action="auth.change_password",
            userId=usuario.id_usuario,
        )
        raise HTTPException(status_code=403, detail="Senha atual não confere")
    if verificar_senha(dados.nova_senha, usuario.senha_hash):
        raise HTTPException(status_code=422, detail="A nova senha precisa ser diferente da atual")

    usuario.senha_hash = gerar_hash_senha(dados.nova_senha)
    revogar_tokens_usuario(db, usuario.id_usuario)
    db.commit()
    log_event(
        audit_logger,
        20,
        "senha_alterada",
        "Senha alterada pelo usuário",
        action="auth.change_password",
        userId=usuario.id_usuario,
    )
    return {"detail": "Senha alterada com sucesso. Entre novamente nos outros dispositivos."}


async def solicitar_reset_senha(
    dados: SolicitarResetSenhaRequest,
    request: Request,
    db: Session,
) -> dict[str, str]:
    email = str(dados.email).strip().lower()
    limitar_auth(request, "password_reset", email)
    usuario = db.query(Usuario).filter(Usuario.email == email, Usuario.ativo.is_(True)).first()
    resposta = {"detail": "Se o e-mail existir, enviaremos instruções para redefinir a senha."}
    if not usuario:
        return resposta

    token = criar_refresh_token()
    registro = PasswordResetToken(
        id_usuario=usuario.id_usuario,
        token_hash=hash_token(token),
        expiracao=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=30),
    )
    db.add(registro)
    db.commit()
    try:
        await enviar_email_reset_senha(email=email, token=token)
    except EmailNaoConfigurado:
        log_event(
            app_logger,
            40,
            "email_reset_senha_nao_configurado",
            "Recuperação de senha solicitada sem Resend configurado",
            action="auth.password_reset_request",
        )
        raise HTTPException(status_code=503, detail="Envio de e-mail ainda não configurado")
    except httpx.HTTPError as erro:
        log_event(
            app_logger,
            40,
            "email_reset_senha_falhou",
            "Falha ao enviar e-mail de reset de senha",
            action="auth.password_reset_request",
            userId=usuario.id_usuario,
            errorType=type(erro).__name__,
        )
        raise HTTPException(status_code=502, detail="Falha temporária ao enviar e-mail")

    log_event(
        audit_logger,
        20,
        "reset_senha_solicitado",
        "Reset de senha solicitado",
        action="auth.password_reset_request",
        userId=usuario.id_usuario,
    )
    return resposta


def confirmar_reset_senha(
    dados: ConfirmarResetSenhaRequest,
    db: Session,
    ao_confirmar: Callable[[Usuario], None] | None = None,
) -> dict[str, str]:
    token_hash = hash_token(dados.token)
    registro = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == token_hash,
            PasswordResetToken.usado.is_(False),
            PasswordResetToken.expiracao > datetime.now(timezone.utc).replace(tzinfo=None),
        )
        .first()
    )
    if not registro:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")

    usuario = db.query(Usuario).filter(Usuario.id_usuario == registro.id_usuario, Usuario.ativo.is_(True)).first()
    if not usuario:
        raise HTTPException(status_code=400, detail="Usuário não encontrado ou inativo")
    if verificar_senha(dados.nova_senha, usuario.senha_hash):
        raise HTTPException(status_code=422, detail="A nova senha precisa ser diferente da atual")

    usuario.senha_hash = gerar_hash_senha(dados.nova_senha)
    registro.usado = True
    registro.usado_em = datetime.now(timezone.utc).replace(tzinfo=None)
    revogar_tokens_usuario(db, usuario.id_usuario)
    db.commit()
    if ao_confirmar:
        ao_confirmar(usuario)
    log_event(
        audit_logger,
        20,
        "senha_redefinida",
        "Senha redefinida por token de recuperação",
        action="auth.password_reset_confirm",
        userId=usuario.id_usuario,
    )
    return {"detail": "Senha redefinida com sucesso."}
