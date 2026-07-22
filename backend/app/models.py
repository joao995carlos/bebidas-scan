from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class Usuario(Base):
    __tablename__ = "usuario"

    id_usuario = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    nome_usuario = Column(String(80), unique=True, index=True)
    email = Column(String(150), unique=True, nullable=False, index=True)
    senha_hash = Column(Text, nullable=False)
    data_nascimento = Column(Date)
    confirmou_maioridade = Column(Boolean, default=False)
    email_verificado = Column(Boolean, default=False)
    ativo = Column(Boolean, default=True)
    tipo_usuario = Column(String(20), nullable=False, default="comum")
    privacidade_versao_aceita = Column(String(20))
    termos_versao_aceita = Column(String(20))
    lgpd_aceite_em = Column(DateTime)
    marketing_consentimento = Column(Boolean, default=False)
    marketing_consentimento_em = Column(DateTime)
    anonimizado_em = Column(DateTime)
    data_criacao = Column(DateTime, server_default=func.now())


class RefreshToken(Base):
    __tablename__ = "refresh_token"

    id_token = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=True)
    token_hash = Column(Text, nullable=False, index=True)
    expiracao = Column(DateTime, nullable=False)
    revogado = Column(Boolean, default=False)
    criado_em = Column(DateTime, server_default=func.now())
    revogado_em = Column(DateTime)

    usuario = relationship("Usuario")


class Bebida(Base):
    __tablename__ = "bebida"

    id_bebida = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), nullable=False)
    marca = Column(String(150))
    tipo = Column(String(80), nullable=False)
    codigo_barras = Column(String(80), unique=True, index=True)
    teor_alcoolico = Column(Numeric(5, 2))
    volume_ml = Column(Integer)
    ingredientes = Column(Text)
    imagem_url = Column(Text)
    nutri_score = Column(String(10))
    nova_grupo = Column(Integer)
    eco_score = Column(String(30))
    alergenos = Column(Text)
    categorias = Column(Text)
    quantidade = Column(String(80))
    embalagem = Column(Text)
    paises = Column(Text)
    classificacao = Column(String(100))
    madeira = Column(String(100))
    tempo_envelhecimento_meses = Column(Integer)
    cidade_origem = Column(String(100))
    estado_origem = Column(String(2))
    regiao_origem = Column(String(100))
    alambique = Column(String(150))
    produtor = Column(String(150))
    lote = Column(String(80))
    origem_dados = Column(String(80))
    id_criado_por = Column(Integer, ForeignKey("usuario.id_usuario"))
    criada_em = Column(DateTime, server_default=func.now())

    cachaca = relationship(
        "Cachaca",
        back_populates="bebida",
        cascade="all, delete-orphan",
        uselist=False,
    )
    criado_por = relationship("Usuario")


class Cachaca(Base):
    __tablename__ = "cachaca"

    id_cachaca = Column(Integer, primary_key=True, index=True)
    id_bebida = Column(Integer, ForeignKey("bebida.id_bebida"), unique=True, nullable=False)
    volume_ml = Column(Integer)
    classificacao = Column(String(100))
    madeira = Column(String(100))
    tempo_envelhecimento_meses = Column(Integer)
    cidade_origem = Column(String(100))
    estado_origem = Column(String(2))
    regiao_origem = Column(String(100))
    alambique = Column(String(150))
    produtor = Column(String(150))
    lote = Column(String(80))
    criada_em = Column(DateTime, server_default=func.now())

    bebida = relationship("Bebida", back_populates="cachaca")


class Avaliacao(Base):
    __tablename__ = "avaliacao"
    __table_args__ = (
        UniqueConstraint("id_usuario", "id_bebida", name="uq_avaliacao_usuario_bebida"),
        CheckConstraint("nota >= 1 AND nota <= 5", name="ck_avaliacao_nota"),
    )

    id_avaliacao = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    id_bebida = Column(Integer, ForeignKey("bebida.id_bebida"), nullable=False)
    nota = Column(Integer, nullable=False)
    comentario = Column(Text)
    compraria_novamente = Column(Boolean)
    data_avaliacao = Column(DateTime, server_default=func.now())

    bebida = relationship("Bebida")
    usuario = relationship("Usuario")


class Favorito(Base):
    __tablename__ = "favorito"
    __table_args__ = (UniqueConstraint("id_usuario", "id_bebida", name="uq_favorito_usuario_bebida"),)

    id_favorito = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=False)
    id_bebida = Column(Integer, ForeignKey("bebida.id_bebida"), nullable=False)
    data_favorito = Column(DateTime, server_default=func.now())

    bebida = relationship("Bebida")
    usuario = relationship("Usuario")


class Preco(Base):
    __tablename__ = "preco"
    __table_args__ = (CheckConstraint("valor >= 0", name="ck_preco_valor"),)

    id_preco = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id_usuario"), nullable=True)
    id_bebida = Column(Integer, ForeignKey("bebida.id_bebida"), nullable=False)
    mercado = Column(String(150))
    cidade = Column(String(100))
    estado = Column(String(2))
    valor = Column(Numeric(10, 2), nullable=False)
    data_registro = Column(DateTime, server_default=func.now())

    bebida = relationship("Bebida")
    usuario = relationship("Usuario")
