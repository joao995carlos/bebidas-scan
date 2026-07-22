from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from .database import get_db
from .schemas import AccessTokenResposta, RefreshRequest, TokenResposta, UsuarioCreate, UsuarioLogin
from .services.auth_service import (
    autenticar_usuario,
    encerrar_sessao,
    registrar_usuario,
    renovar_access_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/registrar", response_model=TokenResposta)
def registrar(dados: UsuarioCreate, request: Request, db: Session = Depends(get_db)):
    return registrar_usuario(dados, request, db)


@router.post("/login", response_model=TokenResposta)
def login(dados: UsuarioLogin, request: Request, db: Session = Depends(get_db)):
    return autenticar_usuario(dados, request, db)


@router.post("/refresh", response_model=AccessTokenResposta)
def refresh(dados: RefreshRequest, db: Session = Depends(get_db)):
    return renovar_access_token(dados, db)


@router.post("/logout")
def logout(dados: RefreshRequest, db: Session = Depends(get_db)):
    return encerrar_sessao(dados, db)

