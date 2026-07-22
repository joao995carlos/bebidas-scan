import os
import secrets
import hmac
import hashlib

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import get_db
from .models import Bebida, Cachaca
from .services.admin_service import (
    alternar_status_usuario,
    criar_avaliacao_admin_service,
    criar_favorito_admin_service,
    criar_preco_admin_service,
    criar_usuario_admin_service,
    excluir_avaliacao_admin_service,
    excluir_bebida_admin_service,
    excluir_favorito_admin_service,
    excluir_preco_admin_service,
    excluir_usuario_admin_service,
    exigir_usuario_e_bebida,
    listar_bebidas_admin,
    listar_avaliacoes_admin,
    listar_favoritos_admin,
    listar_precos_admin,
    listar_usuarios_admin,
    marcar_email_verificado,
    obter_bebida_admin,
    obter_atividade_recente,
    obter_metricas_dashboard,
    revogar_tokens_usuario_admin,
)
from .views.admin_views import (
    html_response as render_admin_html_response,
    render_activity_list,
    render_avaliacoes_page,
    render_bebidas_page,
    render_dashboard,
    render_editar_bebida_form,
    render_favoritos_page,
    render_nova_bebida_form,
    render_precos_page,
    render_usuarios_page,
)

router = APIRouter(prefix="/admin", tags=["admin"])
security = HTTPBasic()


def _admin_credentials() -> tuple[str | None, str | None]:
    return os.getenv("ADMIN_USERNAME"), os.getenv("ADMIN_PASSWORD")


def _admin_secret() -> str:
    secret = os.getenv("ADMIN_CSRF_SECRET") or os.getenv("JWT_SECRET_KEY")
    if not secret or len(secret) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Segredo do painel admin não configurado",
        )
    return secret


def _csrf_token() -> str:
    return hmac.new(
        _admin_secret().encode("utf-8"),
        b"bebidas-scan-admin-csrf",
        hashlib.sha256,
    ).hexdigest()


def _csrf_input() -> str:
    return f'<input type="hidden" name="csrf_token" value="{_csrf_token()}">'


def _validar_csrf(csrf_token: str) -> None:
    if not secrets.compare_digest(csrf_token, _csrf_token()):
        raise HTTPException(status_code=403, detail="Token CSRF inválido")


def _html_response(html: str) -> HTMLResponse:
    return render_admin_html_response(html)


def admin_logado(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    username, password = _admin_credentials()
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Painel admin não configurado",
        )

    usuario_ok = secrets.compare_digest(credentials.username, username)
    senha_ok = secrets.compare_digest(credentials.password, password)
    if not (usuario_ok and senha_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@router.get("", include_in_schema=False)
def admin_raiz(admin: str = Depends(admin_logado)):
    return RedirectResponse("/admin/", status_code=303)
@router.get("/", response_class=HTMLResponse)
def dashboard(db: Session = Depends(get_db), admin: str = Depends(admin_logado)):
    metricas = obter_metricas_dashboard(db)
    atividade_html = render_activity_list(obter_atividade_recente(db))
    return render_dashboard(admin, metricas, atividade_html)


@router.get("/atividade-fragment", response_class=HTMLResponse)
def atividade_fragment(db: Session = Depends(get_db), admin: str = Depends(admin_logado)):
    atividade_html = render_activity_list(obter_atividade_recente(db))
    return render_admin_html_response(atividade_html)


@router.get("/usuarios", response_class=HTMLResponse)
def usuarios(db: Session = Depends(get_db), admin: str = Depends(admin_logado)):
    return render_usuarios_page(listar_usuarios_admin(db), _csrf_input())

@router.post("/usuarios/{id_usuario}/status")
def alternar_usuario(
    id_usuario: int,
    csrf_token: str = Form(""),
    db: Session = Depends(get_db),
    admin: str = Depends(admin_logado),
):
    _validar_csrf(csrf_token)
    alternar_status_usuario(db, id_usuario)
    return RedirectResponse("/admin/usuarios", status_code=303)


@router.post("/usuarios/{id_usuario}/verificar-email")
def verificar_email_usuario(
    id_usuario: int,
    csrf_token: str = Form(""),
    db: Session = Depends(get_db),
    admin: str = Depends(admin_logado),
):
    _validar_csrf(csrf_token)
    marcar_email_verificado(db, id_usuario)
    return RedirectResponse("/admin/usuarios", status_code=303)


@router.post("/usuarios/{id_usuario}/revogar-tokens")
def revogar_tokens_usuario(
    id_usuario: int,
    csrf_token: str = Form(""),
    db: Session = Depends(get_db),
    admin: str = Depends(admin_logado),
):
    _validar_csrf(csrf_token)
    revogar_tokens_usuario_admin(db, id_usuario)
    return RedirectResponse("/admin/usuarios", status_code=303)


@router.post("/usuarios/criar")
def criar_usuario_admin(
    nome: str = Form(...),
    nome_usuario: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    confirmou_maioridade: str | None = Form(None),
    email_verificado: str | None = Form(None),
    ativo: str | None = Form(None),
    csrf_token: str = Form(""),
    db: Session = Depends(get_db),
    admin: str = Depends(admin_logado),
):
    _validar_csrf(csrf_token)
    criar_usuario_admin_service(
        db,
        nome,
        nome_usuario,
        email,
        senha,
        confirmou_maioridade == "true",
        email_verificado == "true",
        ativo == "true",
    )
    return RedirectResponse("/admin/usuarios", status_code=303)


@router.post("/usuarios/{id_usuario}/excluir")
def excluir_usuario_admin(
    id_usuario: int,
    csrf_token: str = Form(""),
    db: Session = Depends(get_db),
    admin: str = Depends(admin_logado),
):
    _validar_csrf(csrf_token)
    excluir_usuario_admin_service(db, id_usuario)
    return RedirectResponse("/admin/usuarios", status_code=303)


@router.get("/bebidas", response_class=HTMLResponse)
def bebidas(
    q: str = "",
    db: Session = Depends(get_db),
    admin: str = Depends(admin_logado),
):
    return render_bebidas_page(listar_bebidas_admin(db, q), q)

@router.get("/bebidas/nova", response_class=HTMLResponse)
def nova_bebida_form(db: Session = Depends(get_db), admin: str = Depends(admin_logado)):
    return render_nova_bebida_form(_csrf_input())

@router.post("/bebidas/nova")
def criar_bebida_admin(
    nome: str = Form(...),
    marca: str = Form(""),
    tipo: str = Form(...),
    codigo_barras: str = Form(""),
    teor_alcoolico: str = Form(""),
    volume_ml: str = Form(""),
    classificacao: str = Form(""),
    madeira: str = Form(""),
    tempo_envelhecimento_meses: str = Form(""),
    cidade_origem: str = Form(""),
    estado_origem: str = Form(""),
    regiao_origem: str = Form(""),
    alambique: str = Form(""),
    produtor: str = Form(""),
    lote: str = Form(""),
    imagem_url: str = Form(""),
    ingredientes: str = Form(""),
    csrf_token: str = Form(""),
    db: Session = Depends(get_db),
    admin: str = Depends(admin_logado),
):
    _validar_csrf(csrf_token)
    bebida = Bebida(nome=nome.strip(), tipo=tipo.strip(), origem_dados="admin")
    _atribuir_bebida_form(
        bebida,
        nome,
        marca,
        tipo,
        codigo_barras,
        teor_alcoolico,
        volume_ml,
        classificacao,
        madeira,
        tempo_envelhecimento_meses,
        cidade_origem,
        estado_origem,
        regiao_origem,
        alambique,
        produtor,
        lote,
        imagem_url,
        ingredientes,
    )
    db.add(bebida)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Código de barras já cadastrado")
    return RedirectResponse("/admin/bebidas", status_code=303)


@router.get("/bebidas/{id_bebida}/editar", response_class=HTMLResponse)
def editar_bebida_form(id_bebida: int, db: Session = Depends(get_db), admin: str = Depends(admin_logado)):
    bebida = obter_bebida_admin(db, id_bebida)
    if not bebida:
        raise HTTPException(status_code=404, detail="Bebida não encontrada")
    return render_editar_bebida_form(bebida, _csrf_input())

@router.post("/bebidas/{id_bebida}/editar")
def editar_bebida(
    id_bebida: int,
    nome: str = Form(""),
    marca: str = Form(""),
    tipo: str = Form(""),
    codigo_barras: str = Form(""),
    teor_alcoolico: str = Form(""),
    volume_ml: str = Form(""),
    classificacao: str = Form(""),
    madeira: str = Form(""),
    tempo_envelhecimento_meses: str = Form(""),
    cidade_origem: str = Form(""),
    estado_origem: str = Form(""),
    regiao_origem: str = Form(""),
    alambique: str = Form(""),
    produtor: str = Form(""),
    lote: str = Form(""),
    imagem_url: str = Form(""),
    ingredientes: str = Form(""),
    csrf_token: str = Form(""),
    db: Session = Depends(get_db),
    admin: str = Depends(admin_logado),
):
    _validar_csrf(csrf_token)
    bebida = obter_bebida_admin(db, id_bebida)
    if not bebida:
        raise HTTPException(status_code=404, detail="Bebida não encontrada")

    _atribuir_bebida_form(
        bebida,
        nome,
        marca,
        tipo,
        codigo_barras,
        teor_alcoolico,
        volume_ml,
        classificacao,
        madeira,
        tempo_envelhecimento_meses,
        cidade_origem,
        estado_origem,
        regiao_origem,
        alambique,
        produtor,
        lote,
        imagem_url,
        ingredientes,
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Código de barras já cadastrado")
    return RedirectResponse(f"/admin/bebidas/{id_bebida}/editar", status_code=303)


@router.post("/bebidas/{id_bebida}/excluir")
def excluir_bebida(
    id_bebida: int,
    csrf_token: str = Form(""),
    db: Session = Depends(get_db),
    admin: str = Depends(admin_logado),
):
    _validar_csrf(csrf_token)
    excluir_bebida_admin_service(db, id_bebida)
    return RedirectResponse("/admin/bebidas", status_code=303)
@router.get("/avaliacoes", response_class=HTMLResponse)
def avaliacoes(db: Session = Depends(get_db), admin: str = Depends(admin_logado)):
    return render_avaliacoes_page(listar_avaliacoes_admin(db), _csrf_input())

@router.post("/avaliacoes/criar")
def criar_avaliacao_admin(
    id_usuario: int = Form(...),
    id_bebida: int = Form(...),
    nota: int = Form(...),
    comentario: str = Form(""),
    compraria_novamente: str | None = Form(None),
    csrf_token: str = Form(""),
    db: Session = Depends(get_db),
    admin: str = Depends(admin_logado),
):
    _validar_csrf(csrf_token)
    criar_avaliacao_admin_service(
        db,
        id_usuario,
        id_bebida,
        nota,
        comentario,
        compraria_novamente == "true",
    )
    return RedirectResponse("/admin/avaliacoes", status_code=303)


@router.post("/avaliacoes/{id_avaliacao}/excluir")
def excluir_avaliacao(
    id_avaliacao: int,
    csrf_token: str = Form(""),
    db: Session = Depends(get_db),
    admin: str = Depends(admin_logado),
):
    _validar_csrf(csrf_token)
    excluir_avaliacao_admin_service(db, id_avaliacao)
    return RedirectResponse("/admin/avaliacoes", status_code=303)


@router.get("/favoritos", response_class=HTMLResponse)
def favoritos(db: Session = Depends(get_db), admin: str = Depends(admin_logado)):
    return render_favoritos_page(listar_favoritos_admin(db), _csrf_input())

@router.post("/favoritos/criar")
def criar_favorito_admin(
    id_usuario: int = Form(...),
    id_bebida: int = Form(...),
    csrf_token: str = Form(""),
    db: Session = Depends(get_db),
    admin: str = Depends(admin_logado),
):
    _validar_csrf(csrf_token)
    criar_favorito_admin_service(db, id_usuario, id_bebida)
    return RedirectResponse("/admin/favoritos", status_code=303)


@router.post("/favoritos/{id_favorito}/excluir")
def excluir_favorito(
    id_favorito: int,
    csrf_token: str = Form(""),
    db: Session = Depends(get_db),
    admin: str = Depends(admin_logado),
):
    _validar_csrf(csrf_token)
    excluir_favorito_admin_service(db, id_favorito)
    return RedirectResponse("/admin/favoritos", status_code=303)


@router.get("/precos", response_class=HTMLResponse)
def precos(db: Session = Depends(get_db), admin: str = Depends(admin_logado)):
    return render_precos_page(listar_precos_admin(db), _csrf_input())

@router.post("/precos/criar")
def criar_preco_admin(
    id_usuario: int = Form(...),
    id_bebida: int = Form(...),
    valor: str = Form(...),
    mercado: str = Form(""),
    cidade: str = Form(""),
    estado: str = Form(""),
    csrf_token: str = Form(""),
    db: Session = Depends(get_db),
    admin: str = Depends(admin_logado),
):
    _validar_csrf(csrf_token)
    criar_preco_admin_service(db, id_usuario, id_bebida, valor, mercado, cidade, estado)
    return RedirectResponse("/admin/precos", status_code=303)


@router.post("/precos/{id_preco}/excluir")
def excluir_preco(
    id_preco: int,
    csrf_token: str = Form(""),
    db: Session = Depends(get_db),
    admin: str = Depends(admin_logado),
):
    _validar_csrf(csrf_token)
    excluir_preco_admin_service(db, id_preco)
    return RedirectResponse("/admin/precos", status_code=303)
