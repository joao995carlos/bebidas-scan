from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .logging_config import set_log_user_id
from .models import Usuario
from .security import verificar_access_token

bearer_scheme = HTTPBearer()


def usuario_logado(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    payload = verificar_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    id_usuario = payload.get("sub")
    if not id_usuario:
        raise HTTPException(status_code=401, detail="Token sem usuário")

    try:
        id_usuario_int = int(id_usuario)
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    usuario = (
        db.query(Usuario)
        .filter(Usuario.id_usuario == id_usuario_int, Usuario.ativo.is_(True))
        .first()
    )
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuário não encontrado ou inativo")

    set_log_user_id(usuario.id_usuario)
    return usuario


def usuario_admin(usuario: Usuario = Depends(usuario_logado)) -> Usuario:
    if usuario.tipo_usuario != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao administrador")
    return usuario


def usuario_e_admin(usuario: Usuario) -> bool:
    return usuario.tipo_usuario == "admin"
