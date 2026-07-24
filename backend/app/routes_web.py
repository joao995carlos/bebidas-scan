from datetime import date
import hmac
import hashlib
import os
from html import escape
from urllib.parse import quote

from fastapi import APIRouter, BackgroundTasks, Cookie, Depends, Form, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import get_db
from .email_service import enviar_email_transacional_seguro
from .lgpd import (
    LGPD_DOCUMENT_VERSION,
    lgpd_pendente,
    politica_privacidade_texto,
    termos_uso_texto,
)
from .models import Bebida, Cachaca, Usuario
from .services.web_service import (
    aceitar_lgpd_web,
    anonimizar_conta_web,
    autenticar_usuario_web,
    emitir_tokens_web,
    exportar_dados_web,
    favoritar_bebida_web,
    buscar_bebidas_web,
    listar_avaliacoes_web,
    listar_favoritos_web,
    obter_bebida_por_codigo_local,
    obter_bebida_web,
    obter_usuario_por_access_token,
    registrar_usuario_web,
    revogar_refresh_token_web,
    salvar_avaliacao_web,
)
from .tipos_bebida import bebida_e_cachaca
from .views.web_views import (
    html_response as render_web_html_response,
    layout as render_web_layout,
    render_cards_page,
    render_documento_legal,
    render_home,
    render_lgpd_aceite_form,
    render_login_form,
    render_minha_privacidade,
    render_minha_privacidade_erro,
    render_minhas_avaliacoes,
    render_registrar_form,
    render_bebida_card,
    render_bebida_detalhe,
    render_bebida_form,
    render_scanner,
)

router = APIRouter(prefix="/web", tags=["web"])


def _cookie_secure() -> bool:
    return os.getenv("WEB_COOKIE_SECURE", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "sim",
    }


def _txt(value) -> str:
    if value is None:
        return ""
    return escape(str(value))


def _web_secret() -> str:
    secret = os.getenv("WEB_CSRF_SECRET") or os.getenv("JWT_SECRET_KEY")
    if not secret or len(secret) < 32:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Segredo da web não configurado",
        )
    return secret


def _csrf_token(refresh_token: str | None) -> str:
    base = refresh_token or "guest"
    return hmac.new(
        _web_secret().encode("utf-8"),
        f"bebidas-scan-web:{base}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def _csrf_input(refresh_token: str | None) -> str:
    return f'<input type="hidden" name="csrf_token" value="{_csrf_token(refresh_token)}">'


def _validar_csrf(csrf_token: str, refresh_token: str | None) -> None:
    if not hmac.compare_digest(csrf_token, _csrf_token(refresh_token)):
        raise HTTPException(status_code=403, detail="Token CSRF inválido")


def _html_response(html: str) -> HTMLResponse:
    return render_web_html_response(html)


def _layout(
    title: str,
    content: str,
    usuario: Usuario | None = None,
    refresh_token: str | None = None,
) -> HTMLResponse:
    csrf_input_html = _csrf_input(refresh_token) if usuario else ""
    return render_web_layout(title, content, usuario, csrf_input_html)


def _set_auth_cookies(response: RedirectResponse, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        "web_access_token",
        access_token,
        httponly=True,
        samesite="lax",
        secure=_cookie_secure(),
        path="/web",
        max_age=60 * 60,
    )
    response.set_cookie(
        "web_refresh_token",
        refresh_token,
        httponly=True,
        samesite="lax",
        secure=_cookie_secure(),
        path="/web",
        max_age=60 * 60 * 24 * 30,
    )


def _clear_auth_cookies(response: RedirectResponse) -> None:
    response.delete_cookie("web_access_token", path="/web")
    response.delete_cookie("web_refresh_token", path="/web")


def _usuario_cookie(
    web_access_token: str | None,
    db: Session,
) -> Usuario | None:
    return obter_usuario_por_access_token(web_access_token, db)


def usuario_web_opcional(
    web_access_token: str | None = Cookie(None),
    db: Session = Depends(get_db),
) -> Usuario | None:
    return _usuario_cookie(web_access_token, db)


def usuario_web_obrigatorio(
    request: Request,
    web_access_token: str | None = Cookie(None),
    db: Session = Depends(get_db),
) -> Usuario:
    usuario = _usuario_cookie(web_access_token, db)
    if not usuario:
        raise HTTPException(status_code=303, headers={"Location": "/web/login"})
    caminho = request.url.path
    caminhos_lgpd = {
        "/web/lgpd/aceitar",
        "/web/logout",
        "/web/privacidade",
        "/web/termos",
    }
    if lgpd_pendente(usuario) and caminho not in caminhos_lgpd:
        raise HTTPException(status_code=303, headers={"Location": "/web/lgpd/aceitar"})
    return usuario


def _emitir_tokens_web(db: Session, usuario: Usuario) -> tuple[str, str]:
    return emitir_tokens_web(db, usuario)


@router.get("", include_in_schema=False)
def web_raiz():
    return RedirectResponse("/web/", status_code=303)


@router.get("/", response_class=HTMLResponse)
def home(
    q: str = Query("", max_length=80),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_web_obrigatorio),
    web_refresh_token: str | None = Cookie(None),
):
    cards = ""
    bebidas = buscar_bebidas_web(db, q)

    for bebida in bebidas:
        cards += _bebida_card(bebida)

    content = render_home(q, cards, bool(q.strip() and not bebidas))
    return _layout("Início", content, usuario, web_refresh_token)


@router.get("/login", response_class=HTMLResponse)
def login_form(usuario: Usuario | None = Depends(usuario_web_opcional)):
    if usuario:
        destino = "/web/lgpd/aceitar" if lgpd_pendente(usuario) else "/web/"
        return RedirectResponse(destino, status_code=303)
    return _layout("Entrar", render_login_form())


@router.post("/login")
def login_post(
    request: Request,
    identificador: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db),
):
    resultado = autenticar_usuario_web(request, identificador, senha, db)
    if not resultado:
        return _layout("Entrar", render_login_form("Nome de usuário ou senha inválidos. Confira os dados e tente novamente."))

    usuario, access_token, refresh_token = resultado
    destino = "/web/lgpd/aceitar" if lgpd_pendente(usuario) else "/web/"
    response = RedirectResponse(destino, status_code=303)
    _set_auth_cookies(response, access_token, refresh_token)
    return response


@router.get("/registrar", response_class=HTMLResponse)
def registrar_form(usuario: Usuario | None = Depends(usuario_web_opcional)):
    if usuario:
        return RedirectResponse("/web/", status_code=303)
    return _layout("Criar conta", render_registrar_form())


def _registrar_form_html(erro: str = "") -> str:
    return render_registrar_form(erro)


@router.post("/registrar")
def registrar_post(
    request: Request,
    background_tasks: BackgroundTasks,
    nome: str = Form(...),
    nome_usuario: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    data_nascimento: date = Form(...),
    aceitou_privacidade: str | None = Form(None),
    aceitou_termos: str | None = Form(None),
    marketing_consentimento: str | None = Form(None),
    db: Session = Depends(get_db),
):
    try:
        usuario, access_token, refresh_token = registrar_usuario_web(
            request,
            nome,
            nome_usuario,
            email,
            senha,
            data_nascimento,
            aceitou_privacidade == "true",
            aceitou_termos == "true",
            marketing_consentimento == "true",
            db,
        )
    except ValueError as erro:
        return _layout("Criar conta", render_registrar_form(str(erro)))

    background_tasks.add_task(
        enviar_email_transacional_seguro,
        "boas_vindas",
        email=usuario.email,
        nome=usuario.nome,
        user_id=usuario.id_usuario,
    )
    response = RedirectResponse("/web/", status_code=303)
    _set_auth_cookies(response, access_token, refresh_token)
    return response


@router.get("/privacidade", response_class=HTMLResponse)
def privacidade():
    content = render_documento_legal("Política de Privacidade", LGPD_DOCUMENT_VERSION, politica_privacidade_texto())
    return _layout("Política de Privacidade", content)


@router.get("/termos", response_class=HTMLResponse)
def termos():
    content = render_documento_legal("Termos de Uso", LGPD_DOCUMENT_VERSION, termos_uso_texto())
    return _layout("Termos de Uso", content)


def _lgpd_aceite_form_html(usuario: Usuario, erro: str = "") -> str:
    return render_lgpd_aceite_form(usuario, erro)


@router.get("/lgpd/aceitar", response_class=HTMLResponse)
def lgpd_aceitar_form(
    usuario: Usuario = Depends(usuario_web_obrigatorio),
    web_refresh_token: str | None = Cookie(None),
):
    return _layout("Atualização de privacidade", render_lgpd_aceite_form(usuario), usuario, web_refresh_token)


@router.post("/lgpd/aceitar")
def lgpd_aceitar_post(
    data_nascimento: date = Form(...),
    aceitou_privacidade: str | None = Form(None),
    aceitou_termos: str | None = Form(None),
    marketing_consentimento: str | None = Form(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_web_obrigatorio),
    web_refresh_token: str | None = Cookie(None),
):
    erro = aceitar_lgpd_web(
        db,
        usuario,
        data_nascimento,
        aceitou_privacidade == "true",
        aceitou_termos == "true",
        marketing_consentimento == "true",
    )
    if erro:
        return _layout("Atualização de privacidade", _lgpd_aceite_form_html(usuario, erro), usuario, web_refresh_token)
    return RedirectResponse("/web/", status_code=303)
@router.get("/minha-privacidade", response_class=HTMLResponse)
def minha_privacidade(
    usuario: Usuario = Depends(usuario_web_obrigatorio),
    web_refresh_token: str | None = Cookie(None),
):
    content = render_minha_privacidade(usuario, _csrf_input(web_refresh_token))
    return _layout("Minha privacidade", content, usuario, web_refresh_token)


@router.get("/minha-privacidade/exportar")
def minha_privacidade_exportar(
    categoria: list[str] = Query(default=["perfil", "avaliacoes", "favoritos", "precos", "bebidas"]),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_web_obrigatorio),
):
    conteudo = exportar_dados_web(db, usuario, categoria)
    return Response(
        content=conteudo,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="meus-dados-bebidas-scan.csv"'},
    )
@router.post("/minha-privacidade/anonimizar")
def minha_privacidade_anonimizar(
    email_confirmacao: str = Form(...),
    senha_confirmacao: str = Form(...),
    csrf_token: str = Form(""),
    web_refresh_token: str | None = Cookie(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_web_obrigatorio),
):
    _validar_csrf(csrf_token, web_refresh_token)
    try:
        anonimizar_conta_web(db, usuario, email_confirmacao, senha_confirmacao)
    except ValueError as erro:
        content = render_minha_privacidade_erro(str(erro))
        return _layout("Minha privacidade", content, usuario, web_refresh_token)
    response = RedirectResponse("/web/login", status_code=303)
    _clear_auth_cookies(response)
    return response


@router.get("/logout")
def logout_get(usuario: Usuario = Depends(usuario_web_obrigatorio)):
    return RedirectResponse("/web/", status_code=303)


@router.post("/logout")
def logout(
    csrf_token: str = Form(""),
    web_refresh_token: str | None = Cookie(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_web_obrigatorio),
):
    _validar_csrf(csrf_token, web_refresh_token)
    revogar_refresh_token_web(db, web_refresh_token)
    response = RedirectResponse("/web/login", status_code=303)
    _clear_auth_cookies(response)
    return response
@router.get("/scanner", response_class=HTMLResponse)
def scanner(
    usuario: Usuario = Depends(usuario_web_obrigatorio),
    web_refresh_token: str | None = Cookie(None),
):
    content = render_scanner(_csrf_input(web_refresh_token))
    return _layout("Scanner", content, usuario, web_refresh_token)


@router.post("/buscar-codigo")
def buscar_codigo(
    codigo: str = Form(...),
    csrf_token: str = Form(""),
    web_refresh_token: str | None = Cookie(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_web_obrigatorio),
):
    _validar_csrf(csrf_token, web_refresh_token)
    codigo = codigo.strip()
    bebida = obter_bebida_por_codigo_local(db, codigo)
    if bebida:
        return RedirectResponse(f"/web/bebidas/{bebida.id_bebida}", status_code=303)
    return RedirectResponse(f"/web/bebidas/nova?codigo_barras={quote(codigo)}", status_code=303)


def _bebida_card(bebida: Bebida) -> str:
    return render_bebida_card(bebida)


@router.get("/bebidas/nova", response_class=HTMLResponse)
def nova_bebida_form(
    codigo_barras: str = Query("", max_length=80),
    usuario: Usuario = Depends(usuario_web_obrigatorio),
    web_refresh_token: str | None = Cookie(None),
):
    return _layout(
        "Cadastrar bebida",
        _bebida_form(None, codigo_barras, web_refresh_token),
        usuario,
        web_refresh_token,
    )


@router.post("/bebidas/nova")
def nova_bebida_post(
    nome: str = Form(...),
    marca: str = Form(""),
    tipo: str = Form(...),
    codigo_barras: str = Form(""),
    teor_alcoolico: str = Form(""),
    ingredientes: str = Form(""),
    imagem_url: str = Form(""),
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
    csrf_token: str = Form(""),
    web_refresh_token: str | None = Cookie(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_web_obrigatorio),
):
    _validar_csrf(csrf_token, web_refresh_token)
    bebida = Bebida(
        nome=nome.strip(),
        tipo=tipo.strip(),
        origem_dados="web",
        id_criado_por=usuario.id_usuario,
    )
    _aplicar_form_bebida(
        bebida,
        marca,
        codigo_barras,
        teor_alcoolico,
        ingredientes,
        imagem_url,
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
    )
    db.add(bebida)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return _layout(
            "Cadastrar bebida",
            _bebida_form(None, codigo_barras, web_refresh_token, "Código de barras já cadastrado."),
            usuario,
            web_refresh_token,
        )
    db.refresh(bebida)
    return RedirectResponse(f"/web/bebidas/{bebida.id_bebida}", status_code=303)


def _bebida_form(bebida: Bebida | None, codigo_barras: str, refresh_token: str | None, erro: str = "") -> str:
    return render_bebida_form(bebida, codigo_barras, _csrf_input(refresh_token), erro)


def _clean(value: str) -> str | None:
    value = value.strip()
    return value or None


def _aplicar_form_bebida(
    bebida: Bebida,
    marca: str,
    codigo_barras: str,
    teor_alcoolico: str,
    ingredientes: str,
    imagem_url: str,
    volume_ml: str,
    classificacao: str,
    madeira: str,
    tempo_envelhecimento_meses: str,
    cidade_origem: str,
    estado_origem: str,
    regiao_origem: str,
    alambique: str,
    produtor: str,
    lote: str,
) -> None:
    bebida.marca = _clean(marca)
    bebida.codigo_barras = _clean(codigo_barras)
    bebida.teor_alcoolico = _clean(teor_alcoolico)
    bebida.ingredientes = _clean(ingredientes)
    bebida.imagem_url = _clean(imagem_url)

    if not bebida_e_cachaca(bebida.tipo):
        bebida.cachaca = None
        return

    campos_cachaca = [
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
    ]
    if not any(_clean(valor) for valor in campos_cachaca):
        bebida.cachaca = None
        return

    bebida.cachaca = bebida.cachaca or Cachaca()
    bebida.cachaca.volume_ml = int(volume_ml) if volume_ml.strip().isdigit() else None
    bebida.cachaca.classificacao = _clean(classificacao)
    bebida.cachaca.madeira = _clean(madeira)
    bebida.cachaca.tempo_envelhecimento_meses = (
        int(tempo_envelhecimento_meses)
        if tempo_envelhecimento_meses.strip().isdigit()
        else None
    )
    bebida.cachaca.cidade_origem = _clean(cidade_origem)
    bebida.cachaca.estado_origem = _clean(estado_origem)
    if bebida.cachaca.estado_origem:
        bebida.cachaca.estado_origem = bebida.cachaca.estado_origem.upper()
    bebida.cachaca.regiao_origem = _clean(regiao_origem)
    bebida.cachaca.alambique = _clean(alambique)
    bebida.cachaca.produtor = _clean(produtor)
    bebida.cachaca.lote = _clean(lote)


@router.get("/bebidas/{id_bebida}", response_class=HTMLResponse)
def detalhe_bebida(
    id_bebida: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_web_obrigatorio),
    web_refresh_token: str | None = Cookie(None),
):
    bebida = obter_bebida_web(db, id_bebida)
    if not bebida:
        raise HTTPException(status_code=404, detail="Bebida não encontrada")
    content = render_bebida_detalhe(bebida, _csrf_input(web_refresh_token))
    return _layout(bebida.nome, content, usuario, web_refresh_token)


@router.post("/favoritos/{id_bebida}")
def web_favoritar(
    id_bebida: int,
    csrf_token: str = Form(""),
    web_refresh_token: str | None = Cookie(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_web_obrigatorio),
):
    _validar_csrf(csrf_token, web_refresh_token)
    favoritar_bebida_web(db, usuario, id_bebida)
    return RedirectResponse(f"/web/bebidas/{id_bebida}", status_code=303)
@router.post("/avaliacoes")
def web_avaliar(
    id_bebida: int = Form(...),
    nota: int = Form(...),
    comentario: str = Form(""),
    compraria_novamente: str | None = Form(None),
    csrf_token: str = Form(""),
    web_refresh_token: str | None = Cookie(None),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_web_obrigatorio),
):
    _validar_csrf(csrf_token, web_refresh_token)
    salvar_avaliacao_web(
        db,
        usuario,
        id_bebida,
        nota,
        _clean(comentario),
        compraria_novamente == "true",
    )
    return RedirectResponse(f"/web/bebidas/{id_bebida}", status_code=303)
@router.get("/favoritos", response_class=HTMLResponse)
def web_favoritos(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_web_obrigatorio),
    web_refresh_token: str | None = Cookie(None),
):
    favoritos = listar_favoritos_web(db, usuario)
    cards = "".join(_bebida_card(item.bebida) for item in favoritos)
    return _layout(
        "Favoritos",
        render_cards_page("Favoritos", cards, "Nenhum favorito ainda."),
        usuario,
        web_refresh_token,
    )
@router.get("/minhas-avaliacoes", response_class=HTMLResponse)
def web_minhas_avaliacoes(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(usuario_web_obrigatorio),
    web_refresh_token: str | None = Cookie(None),
):
    avaliacoes = listar_avaliacoes_web(db, usuario)
    return _layout(
        "Minhas avaliações",
        render_minhas_avaliacoes(avaliacoes),
        usuario,
        web_refresh_token,
    )
