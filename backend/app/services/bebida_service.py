import unicodedata

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..dependencies import usuario_e_admin
from ..logging_config import audit_logger, log_event, security_logger
from ..models import Bebida, Cachaca
from ..open_food_facts import buscar_bebida_open_food_facts, buscar_bebidas_open_food_facts_por_nome
from ..schemas import BebidaCreate, BebidaUpdate
from ..tipos_bebida import bebida_e_cachaca

CAMPOS_CACHACA = {
    "volume_ml",
    "classificacao",
    "madeira",
    "tempo_envelhecimento_meses",
    "cidade_origem",
    "estado_origem",
    "regiao_origem",
    "alambique",
    "produtor",
    "lote",
}

PAISES_BRASIL = ("brazil", "brasil")


def normalizar_payload(payload: dict) -> dict:
    for campo, valor in list(payload.items()):
        if isinstance(valor, str):
            valor = valor.strip()
            payload[campo] = valor or None
    return payload


def separar_payload_bebida_cachaca(payload: dict) -> tuple[dict, dict]:
    payload = normalizar_payload(payload)
    cachaca_payload = payload.pop("cachaca", None) or {}
    cachaca_payload = normalizar_payload(cachaca_payload)

    # Compatibilidade temporaria: aceita campos antigos enviados na raiz.
    for campo in CAMPOS_CACHACA:
        if campo in payload:
            cachaca_payload[campo] = payload.pop(campo)

    if cachaca_payload.get("estado_origem"):
        cachaca_payload["estado_origem"] = cachaca_payload["estado_origem"].upper()

    cachaca_payload = {
        campo: valor
        for campo, valor in cachaca_payload.items()
        if campo in CAMPOS_CACHACA and valor is not None
    }
    if not bebida_e_cachaca(payload.get("tipo")):
        cachaca_payload = {}
    return payload, cachaca_payload


def bebida_externa_do_brasil(bebida: Bebida) -> bool:
    if bebida.origem_dados != "open_food_facts":
        return True

    paises = _normalizar_termo_busca(bebida.paises or "")
    return any(pais in paises for pais in PAISES_BRASIL)


def salvar_cachaca(bebida: Bebida, payload: dict) -> None:
    if not bebida_e_cachaca(bebida.tipo):
        bebida.cachaca = None
        return

    if not payload:
        return

    if bebida.cachaca is None:
        bebida.cachaca = Cachaca()

    for campo, valor in payload.items():
        setattr(bebida.cachaca, campo, valor)


def criar_bebida_usuario(dados: BebidaCreate, db: Session, usuario) -> Bebida:
    payload, cachaca_payload = separar_payload_bebida_cachaca(dados.model_dump(exclude_unset=True))
    if payload.get("codigo_barras"):
        existente = db.query(Bebida).filter(Bebida.codigo_barras == payload["codigo_barras"]).first()
        if existente:
            raise HTTPException(status_code=400, detail="Código de barras já cadastrado")

    bebida = Bebida(**payload, origem_dados="usuario", id_criado_por=usuario.id_usuario)
    salvar_cachaca(bebida, cachaca_payload)
    db.add(bebida)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        log_event(
            audit_logger,
            30,
            "bebida_criacao_conflito",
            "Conflito ao criar bebida",
            action="bebidas.create",
            userId=usuario.id_usuario,
            codigoBarras=payload.get("codigo_barras"),
        )
        raise HTTPException(status_code=400, detail="Código de barras já cadastrado")
    db.refresh(bebida)
    log_event(
        audit_logger,
        20,
        "bebida_criada",
        "Bebida criada",
        action="bebidas.create",
        userId=usuario.id_usuario,
        idBebida=bebida.id_bebida,
        origem=bebida.origem_dados,
    )
    return bebida


def atualizar_bebida_usuario(id_bebida: int, dados: BebidaUpdate, db: Session, usuario) -> Bebida:
    bebida = db.query(Bebida).filter(Bebida.id_bebida == id_bebida).first()
    if not bebida:
        raise HTTPException(status_code=404, detail="Bebida não encontrada")
    if bebida.id_criado_por != usuario.id_usuario and not usuario_e_admin(usuario):
        log_event(
            security_logger,
            30,
            "edicao_bebida_negada",
            "Edição de bebida negada",
            action="bebidas.update",
            userId=usuario.id_usuario,
            idBebida=id_bebida,
            ownerId=bebida.id_criado_por,
        )
        raise HTTPException(status_code=403, detail="Você não pode editar esta bebida")

    payload, cachaca_payload = separar_payload_bebida_cachaca(dados.model_dump(exclude_unset=True))

    if payload.get("codigo_barras") and payload["codigo_barras"] != bebida.codigo_barras:
        existente = db.query(Bebida).filter(Bebida.codigo_barras == payload["codigo_barras"]).first()
        if existente:
            raise HTTPException(status_code=400, detail="Código de barras já cadastrado")

    for campo, valor in payload.items():
        setattr(bebida, campo, valor)

    salvar_cachaca(bebida, cachaca_payload)
    bebida.origem_dados = "usuario"
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        log_event(
            audit_logger,
            30,
            "bebida_edicao_conflito",
            "Conflito ao editar bebida",
            action="bebidas.update",
            userId=usuario.id_usuario,
            idBebida=id_bebida,
            codigoBarras=payload.get("codigo_barras"),
        )
        raise HTTPException(status_code=400, detail="Código de barras já cadastrado")
    db.refresh(bebida)
    log_event(
        audit_logger,
        20,
        "bebida_editada",
        "Bebida editada",
        action="bebidas.update",
        userId=usuario.id_usuario,
        idBebida=bebida.id_bebida,
    )
    return bebida


async def buscar_bebida_por_codigo(codigo_barras: str, db: Session) -> Bebida:
    codigo_barras = codigo_barras.strip()
    bebida = db.query(Bebida).filter(Bebida.codigo_barras == codigo_barras).first()
    if bebida and bebida_externa_do_brasil(bebida):
        return bebida

    dados_externos = await buscar_bebida_open_food_facts(codigo_barras)
    if not dados_externos:
        log_event(
            audit_logger,
            20,
            "bebida_codigo_nao_encontrado",
            "Bebida não encontrada por código",
            action="bebidas.lookup",
            codigoBarras=codigo_barras,
        )
        raise HTTPException(status_code=404, detail="Bebida não encontrada")

    payload, cachaca_payload = separar_payload_bebida_cachaca(dados_externos.model_dump(exclude_unset=True))
    bebida = Bebida(**payload, origem_dados="open_food_facts")
    salvar_cachaca(bebida, cachaca_payload)
    db.add(bebida)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        bebida = db.query(Bebida).filter(Bebida.codigo_barras == codigo_barras).first()
        if bebida:
            return bebida
        log_event(
            audit_logger,
            40,
            "bebida_open_food_facts_conflito",
            "Conflito ao salvar bebida externa",
            action="bebidas.lookup",
            codigoBarras=codigo_barras,
        )
        raise HTTPException(status_code=409, detail="Conflito ao salvar bebida")
    db.refresh(bebida)
    return bebida


def _buscar_bebidas_locais_por_nome(q: str, db: Session, limite: int = 25) -> list[Bebida]:
    q = q.strip()
    bebidas = [
        bebida
        for bebida in db.query(Bebida)
        .filter(Bebida.nome.ilike(f"%{q}%"))
        .order_by(Bebida.nome)
        .limit(limite * 2)
        .all()
        if bebida_externa_do_brasil(bebida)
    ][:limite]
    if len(bebidas) >= limite:
        return bebidas

    termo_normalizado = _normalizar_termo_busca(q)
    ids = {bebida.id_bebida for bebida in bebidas}
    candidatos = db.query(Bebida).order_by(Bebida.nome).limit(300).all()
    for bebida in candidatos:
        if bebida.id_bebida in ids:
            continue
        if not bebida_externa_do_brasil(bebida):
            continue
        texto = " ".join(
            str(valor or "")
            for valor in (
                bebida.nome,
                bebida.marca,
                bebida.tipo,
                bebida.categorias,
                bebida.ingredientes,
            )
        )
        if termo_normalizado in _normalizar_termo_busca(texto):
            bebidas.append(bebida)
            ids.add(bebida.id_bebida)
            if len(bebidas) >= limite:
                break
    return bebidas


def _normalizar_termo_busca(valor: str) -> str:
    texto = unicodedata.normalize("NFKD", valor or "")
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    return texto.casefold().strip()


def _termos_busca_externa(q: str) -> list[str]:
    termo = q.strip()
    termos = [termo]
    normalizado = _normalizar_termo_busca(termo)
    sinonimos = {
        "agua": ["água", "water"],
        "coca": ["coca cola", "cola"],
        "refrigerante": ["soda", "soft drink"],
        "cerveja": ["beer"],
        "suco": ["juice"],
        "energetico": ["energy drink"],
    }
    termos.extend(sinonimos.get(normalizado, []))
    unicos: list[str] = []
    for item in termos:
        if item and item not in unicos:
            unicos.append(item)
    return unicos


async def buscar_bebidas_por_nome(q: str, db: Session) -> list[Bebida]:
    q = q.strip()
    bebidas = _buscar_bebidas_locais_por_nome(q, db)
    if len(bebidas) >= 10:
        return bebidas

    dados_externos = []
    for termo_externo in _termos_busca_externa(q):
        dados_externos.extend(await buscar_bebidas_open_food_facts_por_nome(termo_externo, limite=10))
        if len(dados_externos) >= 10:
            dados_externos = dados_externos[:10]
            break
    if not dados_externos:
        return bebidas

    codigos_locais = {bebida.codigo_barras for bebida in bebidas if bebida.codigo_barras}
    ids_locais = {bebida.id_bebida for bebida in bebidas}
    for dados in dados_externos:
        payload, cachaca_payload = separar_payload_bebida_cachaca(dados.model_dump(exclude_unset=True))
        codigo = payload.get("codigo_barras")
        if codigo and codigo in codigos_locais:
            continue
        if codigo:
            existente = db.query(Bebida).filter(Bebida.codigo_barras == codigo).first()
            if existente:
                codigos_locais.add(codigo)
                if existente.id_bebida not in ids_locais and bebida_externa_do_brasil(existente):
                    bebidas.append(existente)
                    ids_locais.add(existente.id_bebida)
                continue
        bebida = Bebida(**payload, origem_dados="open_food_facts")
        salvar_cachaca(bebida, cachaca_payload)
        db.add(bebida)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            continue
        db.refresh(bebida)
        codigos_locais.add(bebida.codigo_barras or "")
        ids_locais.add(bebida.id_bebida)
        bebidas.append(bebida)
        if len(bebidas) >= 25:
            break

    return bebidas[:25]
