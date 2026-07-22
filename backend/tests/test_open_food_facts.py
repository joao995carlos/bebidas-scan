from app.open_food_facts import _bebida_create_from_produto, _produto_marcado_fora_do_brasil


def test_open_food_facts_ignora_produto_marcado_fora_do_brasil():
    produto = {
        "code": "1234567890123",
        "product_name": "Imported Soda",
        "categories_tags": ["en:beverages", "en:sodas"],
        "countries_tags": ["en:united-states"],
    }

    assert _produto_marcado_fora_do_brasil(produto) is True


def test_open_food_facts_prefere_campos_em_portugues():
    produto = {
        "code": "7894900010015",
        "product_name": "Coke can",
        "product_name_pt": "Coca-Cola lata",
        "categories_tags": ["en:beverages", "en:sodas"],
        "countries_tags": ["en:brazil"],
        "ingredients_text": "Carbonated water, sugar",
        "ingredients_text_pt": "Agua gaseificada, acucar",
        "countries": "Brazil",
    }

    bebida = _bebida_create_from_produto(produto)

    assert bebida is not None
    assert bebida.nome == "Coca-Cola lata"
    assert bebida.ingredientes == "Agua gaseificada, acucar"
    assert bebida.tipo == "refrigerante"
