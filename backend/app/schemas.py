from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field, field_validator

from .validacao import validar_senha_forte


class UsuarioCreate(BaseModel):
    nome: str = Field(min_length=2, max_length=150)
    nome_usuario: str = Field(min_length=3, max_length=80)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=100)
    data_nascimento: date
    aceitou_privacidade: bool = False
    aceitou_termos: bool = False
    marketing_consentimento: bool = False

    @field_validator("senha")
    @classmethod
    def senha_forte(cls, senha: str) -> str:
        return validar_senha_forte(senha)


class UsuarioLogin(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    identificador: str = Field(
        min_length=3,
        max_length=150,
        validation_alias=AliasChoices("identificador", "email", "nome_usuario"),
    )
    senha: str = Field(min_length=1, max_length=100)


class UsuarioResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_usuario: int
    nome: str
    nome_usuario: Optional[str] = None
    email: EmailStr
    ativo: bool
    confirmou_maioridade: bool
    tipo_usuario: str
    data_nascimento: Optional[date] = None
    privacidade_versao_aceita: Optional[str] = None
    termos_versao_aceita: Optional[str] = None
    lgpd_aceite_em: Optional[datetime] = None
    marketing_consentimento: bool = False


class TokenResposta(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    usuario: UsuarioResposta


class AccessTokenResposta(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20, max_length=300)


class LGPDAceiteRequest(BaseModel):
    data_nascimento: date
    aceitou_privacidade: bool
    aceitou_termos: bool
    marketing_consentimento: bool = False


class ExclusaoContaRequest(BaseModel):
    email: EmailStr
    senha: str = Field(min_length=1, max_length=100)


class LGPDStatusResposta(BaseModel):
    pendente: bool
    versao_atual: str
    privacidade_versao_aceita: Optional[str] = None
    termos_versao_aceita: Optional[str] = None
    lgpd_aceite_em: Optional[datetime] = None


class CachacaBase(BaseModel):
    volume_ml: Optional[int] = Field(default=None, ge=1, le=100000)
    classificacao: Optional[str] = Field(default=None, max_length=100)
    madeira: Optional[str] = Field(default=None, max_length=100)
    tempo_envelhecimento_meses: Optional[int] = Field(default=None, ge=0, le=1200)
    cidade_origem: Optional[str] = Field(default=None, max_length=100)
    estado_origem: Optional[str] = Field(default=None, min_length=2, max_length=2)
    regiao_origem: Optional[str] = Field(default=None, max_length=100)
    alambique: Optional[str] = Field(default=None, max_length=150)
    produtor: Optional[str] = Field(default=None, max_length=150)
    lote: Optional[str] = Field(default=None, max_length=80)


class CachacaCreate(CachacaBase):
    pass


class CachacaUpdate(CachacaBase):
    pass


class CachacaResposta(CachacaBase):
    model_config = ConfigDict(from_attributes=True)

    id_cachaca: int
    id_bebida: int


class BebidaBase(BaseModel):
    nome: str = Field(min_length=1, max_length=200)
    marca: Optional[str] = Field(default=None, max_length=150)
    tipo: str = Field(min_length=1, max_length=80)
    codigo_barras: Optional[str] = Field(default=None, min_length=6, max_length=80)
    teor_alcoolico: Optional[float] = Field(default=None, ge=0, le=100)
    ingredientes: Optional[str] = None
    imagem_url: Optional[str] = None
    nutri_score: Optional[str] = Field(default=None, max_length=10)
    nova_grupo: Optional[int] = Field(default=None, ge=1, le=4)
    eco_score: Optional[str] = Field(default=None, max_length=30)
    alergenos: Optional[str] = None
    categorias: Optional[str] = None
    quantidade: Optional[str] = Field(default=None, max_length=80)
    embalagem: Optional[str] = None
    paises: Optional[str] = None


class BebidaCreate(BebidaBase, CachacaBase):
    cachaca: Optional[CachacaCreate] = None


class BebidaUpdate(CachacaBase):
    nome: Optional[str] = Field(default=None, min_length=1, max_length=200)
    marca: Optional[str] = Field(default=None, max_length=150)
    tipo: Optional[str] = Field(default=None, min_length=1, max_length=80)
    codigo_barras: Optional[str] = Field(default=None, min_length=6, max_length=80)
    teor_alcoolico: Optional[float] = Field(default=None, ge=0, le=100)
    ingredientes: Optional[str] = None
    imagem_url: Optional[str] = None
    nutri_score: Optional[str] = Field(default=None, max_length=10)
    nova_grupo: Optional[int] = Field(default=None, ge=1, le=4)
    eco_score: Optional[str] = Field(default=None, max_length=30)
    alergenos: Optional[str] = None
    categorias: Optional[str] = None
    quantidade: Optional[str] = Field(default=None, max_length=80)
    embalagem: Optional[str] = None
    paises: Optional[str] = None
    cachaca: Optional[CachacaUpdate] = None


class BebidaResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_bebida: int
    nome: str
    marca: Optional[str] = None
    tipo: str
    codigo_barras: Optional[str] = None
    teor_alcoolico: Optional[Decimal] = None
    ingredientes: Optional[str] = None
    imagem_url: Optional[str] = None
    nutri_score: Optional[str] = None
    nova_grupo: Optional[int] = None
    eco_score: Optional[str] = None
    alergenos: Optional[str] = None
    categorias: Optional[str] = None
    quantidade: Optional[str] = None
    embalagem: Optional[str] = None
    paises: Optional[str] = None
    cachaca: Optional[CachacaResposta] = None
    origem_dados: Optional[str] = None
    id_criado_por: Optional[int] = None


class AvaliacaoCreate(BaseModel):
    id_bebida: int
    nota: int = Field(ge=1, le=5)
    comentario: Optional[str] = Field(default=None, max_length=1000)
    compraria_novamente: Optional[bool] = None


class AvaliacaoResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_avaliacao: int
    id_bebida: int
    nota: int
    comentario: Optional[str] = None
    compraria_novamente: Optional[bool] = None
    data_avaliacao: datetime


class FavoritoResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_favorito: int
    bebida: BebidaResposta
    data_favorito: datetime


class PrecoCreate(BaseModel):
    id_bebida: int
    mercado: Optional[str] = Field(default=None, max_length=150)
    cidade: Optional[str] = Field(default=None, max_length=100)
    estado: Optional[str] = Field(default=None, min_length=2, max_length=2)
    valor: float = Field(ge=0)


class PrecoResposta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_preco: int
    id_bebida: int
    mercado: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    valor: Decimal
    data_registro: datetime
