from fastapi import APIRouter

from .services.privacidade_service import obter_politica_privacidade, obter_termos_uso

router = APIRouter(prefix="/privacidade", tags=["privacidade"])


@router.get("/politica")
def politica():
    return obter_politica_privacidade()


@router.get("/termos")
def termos():
    return obter_termos_uso()

