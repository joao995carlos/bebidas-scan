from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session

from .database import get_db
from .dependencies import usuario_logado
from .email_service import enviar_email_transacional_seguro
from .schemas import (
    AccessTokenResposta,
    AlterarSenhaRequest,
    ConfirmarResetSenhaRequest,
    RefreshRequest,
    SolicitarResetSenhaRequest,
    TokenResposta,
    UsuarioCreate,
    UsuarioLogin,
)
from .services.auth_service import (
    alterar_senha_usuario,
    autenticar_usuario,
    confirmar_reset_senha,
    encerrar_sessao,
    registrar_usuario,
    renovar_access_token,
    solicitar_reset_senha,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/registrar", response_model=TokenResposta)
def registrar(
    dados: UsuarioCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    resposta = registrar_usuario(dados, request, db)
    background_tasks.add_task(
        enviar_email_transacional_seguro,
        "boas_vindas",
        email=resposta.usuario.email,
        nome=resposta.usuario.nome,
        user_id=resposta.usuario.id_usuario,
    )
    return resposta


@router.post("/login", response_model=TokenResposta)
def login(dados: UsuarioLogin, request: Request, db: Session = Depends(get_db)):
    return autenticar_usuario(dados, request, db)


@router.post("/refresh", response_model=AccessTokenResposta)
def refresh(dados: RefreshRequest, db: Session = Depends(get_db)):
    return renovar_access_token(dados, db)


@router.post("/logout")
def logout(dados: RefreshRequest, db: Session = Depends(get_db)):
    return encerrar_sessao(dados, db)


@router.post("/alterar-senha")
def alterar_senha(
    dados: AlterarSenhaRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    usuario=Depends(usuario_logado),
):
    resposta = alterar_senha_usuario(dados, db, usuario)
    background_tasks.add_task(
        enviar_email_transacional_seguro,
        "senha_alterada",
        email=usuario.email,
        nome=usuario.nome,
        user_id=usuario.id_usuario,
    )
    return resposta


@router.post("/solicitar-reset-senha")
async def solicitar_reset(
    dados: SolicitarResetSenhaRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    return await solicitar_reset_senha(dados, request, db)


@router.post("/confirmar-reset-senha")
def confirmar_reset(
    dados: ConfirmarResetSenhaRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    return confirmar_reset_senha(
        dados,
        db,
        lambda usuario: background_tasks.add_task(
            enviar_email_transacional_seguro,
            "senha_redefinida",
            email=usuario.email,
            nome=usuario.nome,
            user_id=usuario.id_usuario,
        ),
    )
