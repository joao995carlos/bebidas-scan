from typing import Optional
import os

import httpx
from pydantic import ValidationError

from .logging_config import app_logger, log_event
from .schemas import BebidaCreate

OPEN_FOOD_FACTS_URL = "https://world.openfoodfacts.org/api/v2/product/{codigo}.json"
OPEN_FOOD_FACTS_SEARCH_URL = "https://world.openfoodfacts.org/cgi/search.pl"
OPEN_FOOD_FACTS_USER_AGENT = os.getenv("OPEN_FOOD_FACTS_USER_AGENT", "BebidasScan/0.1")
OPEN_FOOD_FACTS_LOCALE_PARAMS = {"lc": "pt", "cc": "br"}
OPEN_FOOD_FACTS_BRASIL_TAG = "en:brazil"
OPEN_FOOD_FACTS_FIELDS = ",".join(
    [
        "code",
        "product_name_pt",
        "product_name",
        "generic_name_pt",
        "generic_name",
        "categories_pt",
        "categories",
        "categories_tags",
        "brands",
        "ingredients_text_pt",
        "ingredients_text_with_allergens_pt",
        "ingredients_text",
        "ingredients_text_with_allergens",
        "image_front_url",
        "image_url",
        "nutriscore_grade",
        "nova_group",
        "ecoscore_grade",
        "allergens_pt",
        "allergens",
        "allergens_tags",
        "quantity",
        "packaging_pt",
        "packaging",
        "packaging_tags",
        "countries_pt",
        "countries",
        "countries_tags",
        "nutriments",
    ]
)


def _texto_de_tags(valor: object) -> Optional[str]:
    if isinstance(valor, str) and valor.strip():
        return valor.strip()
    if not isinstance(valor, list):
        return None

    itens = []
    for item in valor:
        texto = str(item).strip()
        if not texto:
            continue
        if ":" in texto:
            texto = texto.split(":", 1)[1]
        texto = texto.replace("-", " ").strip()
        if texto:
            itens.append(texto)
    return ", ".join(itens) or None


def _inteiro(valor: object) -> Optional[int]:
    try:
        return int(valor)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _float(valor: object) -> Optional[float]:
    try:
        return float(valor)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def _texto_limitado(valor: object, limite: int) -> Optional[str]:
    if valor is None:
        return None
    texto = str(valor).strip()
    if not texto or len(texto) > limite:
        return None
    return texto


def _codigo_barras_valido(valor: object) -> Optional[str]:
    if valor is None:
        return None
    codigo = str(valor).strip()
    if not 6 <= len(codigo) <= 80:
        return None
    return codigo


def _tem_tag_brasil(valor: object) -> bool:
    if not isinstance(valor, list):
        return False
    return any(str(item).strip().lower() == OPEN_FOOD_FACTS_BRASIL_TAG for item in valor)


def _produto_marcado_fora_do_brasil(produto: dict) -> bool:
    tags = produto.get("countries_tags")
    return isinstance(tags, list) and len(tags) > 0 and not _tem_tag_brasil(tags)


def _classificar_tipo(categorias: str) -> Optional[str]:
    if not any(
        token in categorias
        for token in (
            "beverage",
            "bebida",
            "drink",
            "alcohol",
            "cerveja",
            "beer",
            "wine",
            "vinho",
            "spirit",
            "liquor",
            "juice",
            "suco",
            "water",
            "agua",
            "soda",
            "refrigerante",
            "soft-drink",
            "energy-drink",
            "energetico",
            "tea",
            "cha",
            "coffee",
            "cafe",
        )
    ):
        return None

    if "beer" in categorias or "cerveja" in categorias:
        return "cerveja"
    if "wine" in categorias or "vinho" in categorias:
        return "vinho"
    if "spirit" in categorias or "liquor" in categorias:
        return "destilado"
    if "energy-drink" in categorias or "energetico" in categorias:
        return "energetico"
    if "soda" in categorias or "soft-drink" in categorias or "refrigerante" in categorias:
        return "refrigerante"
    if "juice" in categorias or "suco" in categorias:
        return "suco"
    if "water" in categorias or "agua" in categorias:
        return "agua"
    if "tea" in categorias or "cha" in categorias:
        return "cha"
    if "coffee" in categorias or "cafe" in categorias:
        return "cafe"
    return "bebida"


def _bebida_create_from_produto(produto: dict, codigo_barras: str | None = None) -> Optional[BebidaCreate]:
    codigo = codigo_barras or produto.get("code")
    nome = (
        produto.get("product_name_pt")
        or produto.get("product_name")
        or produto.get("generic_name_pt")
        or produto.get("generic_name")
    )
    if not nome:
        return None

    categorias = " ".join(produto.get("categories_tags") or []).lower()
    tipo = _classificar_tipo(categorias)
    if tipo is None:
        return None

    marcas = produto.get("brands") or None
    ingredientes = (
        produto.get("ingredients_text_pt")
        or produto.get("ingredients_text_with_allergens_pt")
        or produto.get("ingredients_text")
        or produto.get("ingredients_text_with_allergens")
    )
    imagem_url = produto.get("image_front_url") or produto.get("image_url")
    nutrimentos = produto.get("nutriments") if isinstance(produto.get("nutriments"), dict) else {}
    teor_alcoolico = _float(
        nutrimentos.get("alcohol_100g")
        or nutrimentos.get("alcohol")
        or nutrimentos.get("alcohol_value")
    )

    try:
        return BebidaCreate(
            nome=str(nome).strip()[:200],
            marca=_texto_limitado(marcas, 150),
            tipo=tipo,
            codigo_barras=_codigo_barras_valido(codigo),
            teor_alcoolico=teor_alcoolico,
            ingredientes=ingredientes,
            imagem_url=imagem_url,
            nutri_score=_texto_limitado(produto.get("nutriscore_grade"), 10),
            nova_grupo=_inteiro(produto.get("nova_group")),
            eco_score=_texto_limitado(produto.get("ecoscore_grade"), 30),
            alergenos=(
                produto.get("allergens_pt")
                or produto.get("allergens")
                or _texto_de_tags(produto.get("allergens_tags"))
            ),
            categorias=(
                produto.get("categories_pt")
                or produto.get("categories")
                or _texto_de_tags(produto.get("categories_tags"))
            ),
            quantidade=_texto_limitado(produto.get("quantity"), 80),
            embalagem=(
                produto.get("packaging_pt")
                or produto.get("packaging")
                or _texto_de_tags(produto.get("packaging_tags"))
            ),
            paises=(
                produto.get("countries_pt")
                or produto.get("countries")
                or _texto_de_tags(produto.get("countries_tags"))
            ),
        )
    except ValidationError as erro:
        log_event(
            app_logger,
            30,
            "open_food_facts_produto_invalido",
            "Produto externo ignorado por falha de validação",
            action="open_food_facts.normalize",
            codigoBarras=_codigo_barras_valido(codigo),
            errorType=type(erro).__name__,
        )
        return None


async def buscar_bebida_open_food_facts(codigo_barras: str) -> Optional[BebidaCreate]:
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(
                OPEN_FOOD_FACTS_URL.format(codigo=codigo_barras),
                headers={"User-Agent": OPEN_FOOD_FACTS_USER_AGENT},
                params={"fields": OPEN_FOOD_FACTS_FIELDS, **OPEN_FOOD_FACTS_LOCALE_PARAMS},
            )
    except httpx.HTTPError as erro:
        log_event(
            app_logger,
            30,
            "open_food_facts_http_error",
            "Falha HTTP ao consultar Open Food Facts",
            action="open_food_facts.lookup",
            codigoBarras=codigo_barras,
            errorType=type(erro).__name__,
        )
        return None

    if response.status_code != 200:
        log_event(
            app_logger,
            30,
            "open_food_facts_status_invalido",
            "Open Food Facts retornou status HTTP inesperado",
            action="open_food_facts.lookup",
            codigoBarras=codigo_barras,
            statusCode=response.status_code,
        )
        return None

    try:
        data = response.json()
    except ValueError as erro:
        log_event(
            app_logger,
            30,
            "open_food_facts_json_invalido",
            "Resposta inválida do Open Food Facts",
            action="open_food_facts.lookup",
            codigoBarras=codigo_barras,
            errorType=type(erro).__name__,
        )
        return None
    if data.get("status") != 1:
        log_event(
            app_logger,
            20,
            "open_food_facts_produto_nao_encontrado",
            "Produto não encontrado no Open Food Facts",
            action="open_food_facts.lookup",
            codigoBarras=codigo_barras,
        )
        return None

    produto = data.get("product") or {}
    if _produto_marcado_fora_do_brasil(produto):
        log_event(
            app_logger,
            20,
            "open_food_facts_produto_fora_do_brasil",
            "Produto encontrado, mas nÃ£o marcado como vendido no Brasil",
            action="open_food_facts.lookup",
            codigoBarras=codigo_barras,
        )
        return None

    bebida = _bebida_create_from_produto(produto, codigo_barras)
    if bebida is None:
        log_event(
            app_logger,
            20,
            "open_food_facts_produto_ignorado",
            "Produto encontrado, mas não classificado como bebida",
            action="open_food_facts.lookup",
            codigoBarras=codigo_barras,
        )
        return None

    return bebida


async def buscar_bebidas_open_food_facts_por_nome(termo: str, limite: int = 10) -> list[BebidaCreate]:
    termo = termo.strip()
    if len(termo) < 2:
        return []

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(
                OPEN_FOOD_FACTS_SEARCH_URL,
                headers={"User-Agent": OPEN_FOOD_FACTS_USER_AGENT},
                params={
                    "search_terms": termo,
                    "search_simple": 1,
                    "action": "process",
                    "json": 1,
                    "page_size": limite,
                    "fields": OPEN_FOOD_FACTS_FIELDS,
                    "tagtype_0": "countries",
                    "tag_contains_0": "contains",
                    "tag_0": "brazil",
                    **OPEN_FOOD_FACTS_LOCALE_PARAMS,
                },
            )
    except httpx.HTTPError as erro:
        log_event(
            app_logger,
            30,
            "open_food_facts_search_http_error",
            "Falha HTTP ao pesquisar Open Food Facts",
            action="open_food_facts.search",
            termo=termo,
            errorType=type(erro).__name__,
        )
        return []

    if response.status_code != 200:
        log_event(
            app_logger,
            30,
            "open_food_facts_search_status_invalido",
            "Open Food Facts retornou status HTTP inesperado na pesquisa",
            action="open_food_facts.search",
            termo=termo,
            statusCode=response.status_code,
        )
        return []

    try:
        data = response.json()
    except ValueError as erro:
        log_event(
            app_logger,
            30,
            "open_food_facts_search_json_invalido",
            "Resposta inválida da pesquisa Open Food Facts",
            action="open_food_facts.search",
            termo=termo,
            errorType=type(erro).__name__,
        )
        return []

    produtos = data.get("products") if isinstance(data, dict) else None
    if not isinstance(produtos, list):
        return []

    bebidas: list[BebidaCreate] = []
    codigos_vistos: set[str] = set()
    for produto in produtos:
        if not isinstance(produto, dict):
            continue
        if _produto_marcado_fora_do_brasil(produto):
            continue
        bebida = _bebida_create_from_produto(produto)
        if bebida is None:
            continue
        codigo = bebida.codigo_barras or ""
        if codigo and codigo in codigos_vistos:
            continue
        if codigo:
            codigos_vistos.add(codigo)
        bebidas.append(bebida)
        if len(bebidas) >= limite:
            break
    return bebidas
