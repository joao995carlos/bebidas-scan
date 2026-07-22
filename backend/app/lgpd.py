from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from io import StringIO
import csv

from sqlalchemy.orm import Session

from .models import Avaliacao, Bebida, Favorito, Preco, RefreshToken, Usuario
from .security import verificar_senha

LGPD_DOCUMENT_VERSION = "2026-07-14"
LGPD_CONTACT_TEXT = "canal de privacidade a ser definido"
BACKUP_RETENTION_TEXT = "até 180 dias, conforme necessidade técnica de restauração"
LOG_RETENTION_TEXT = "180 dias"
REFRESH_TOKEN_RETENTION_DAYS = 30


def utc_agora() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def calcular_maioridade(data_nascimento: date | None, hoje: date | None = None) -> bool:
    if data_nascimento is None:
        return False
    hoje = hoje or date.today()
    idade = hoje.year - data_nascimento.year
    if (hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day):
        idade -= 1
    return idade >= 18


def lgpd_pendente(usuario: Usuario) -> bool:
    return (
        usuario.data_nascimento is None
        or not usuario.confirmou_maioridade
        or usuario.privacidade_versao_aceita != LGPD_DOCUMENT_VERSION
        or usuario.termos_versao_aceita != LGPD_DOCUMENT_VERSION
        or usuario.lgpd_aceite_em is None
    )


def registrar_aceite_lgpd(
    usuario: Usuario,
    *,
    data_nascimento: date,
    marketing_consentimento: bool,
) -> None:
    usuario.data_nascimento = data_nascimento
    usuario.confirmou_maioridade = calcular_maioridade(data_nascimento)
    usuario.privacidade_versao_aceita = LGPD_DOCUMENT_VERSION
    usuario.termos_versao_aceita = LGPD_DOCUMENT_VERSION
    usuario.lgpd_aceite_em = utc_agora()
    usuario.marketing_consentimento = marketing_consentimento
    usuario.marketing_consentimento_em = utc_agora() if marketing_consentimento else None


def anonimizar_usuario(db: Session, usuario: Usuario, *, email: str, senha: str) -> None:
    if usuario.email != email.strip().lower() or not verificar_senha(senha, usuario.senha_hash):
        raise ValueError("E-mail ou senha não conferem.")

    anon_id = f"usuario_excluido_{usuario.id_usuario}"
    agora = utc_agora()

    db.query(RefreshToken).filter(RefreshToken.id_usuario == usuario.id_usuario).update(
        {RefreshToken.revogado: True, RefreshToken.revogado_em: agora},
        synchronize_session=False,
    )
    db.query(Favorito).filter(Favorito.id_usuario == usuario.id_usuario).delete()
    db.query(Avaliacao).filter(Avaliacao.id_usuario == usuario.id_usuario).update(
        {Avaliacao.id_usuario: None, Avaliacao.comentario: None},
        synchronize_session=False,
    )
    db.query(Preco).filter(Preco.id_usuario == usuario.id_usuario).update(
        {Preco.id_usuario: None},
        synchronize_session=False,
    )
    db.query(Bebida).filter(Bebida.id_criado_por == usuario.id_usuario).update(
        {Bebida.id_criado_por: None},
        synchronize_session=False,
    )

    usuario.nome = "Usuário excluído"
    usuario.nome_usuario = anon_id
    usuario.email = f"{anon_id}@anonimo.example.com"
    usuario.senha_hash = "anonimizado"
    usuario.data_nascimento = None
    usuario.confirmou_maioridade = False
    usuario.email_verificado = False
    usuario.ativo = False
    usuario.marketing_consentimento = False
    usuario.marketing_consentimento_em = None
    usuario.anonimizado_em = agora
    db.commit()


def limpar_refresh_tokens_antigos(db: Session) -> int:
    limite = utc_agora() - timedelta(days=REFRESH_TOKEN_RETENTION_DAYS)
    removidos = (
        db.query(RefreshToken)
        .filter(
            (RefreshToken.revogado.is_(True) & (RefreshToken.revogado_em < limite))
            | (RefreshToken.expiracao < limite)
        )
        .delete(synchronize_session=False)
    )
    db.commit()
    return removidos


def exportar_dados_usuario_csv(db: Session, usuario: Usuario, categorias: set[str]) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(["categoria", "campo", "valor"])

    if "perfil" in categorias:
        writer.writerow(["perfil", "id_usuario", usuario.id_usuario])
        writer.writerow(["perfil", "nome", usuario.nome])
        writer.writerow(["perfil", "nome_usuario", usuario.nome_usuario])
        writer.writerow(["perfil", "email", usuario.email])
        writer.writerow(["perfil", "data_nascimento", usuario.data_nascimento or ""])
        writer.writerow(["perfil", "confirmou_maioridade", usuario.confirmou_maioridade])
        writer.writerow(["perfil", "privacidade_versao_aceita", usuario.privacidade_versao_aceita or ""])
        writer.writerow(["perfil", "termos_versao_aceita", usuario.termos_versao_aceita or ""])
        writer.writerow(["perfil", "lgpd_aceite_em", usuario.lgpd_aceite_em or ""])
        writer.writerow(["perfil", "marketing_consentimento", usuario.marketing_consentimento])

    if "avaliacoes" in categorias:
        writer.writerow(["avaliacoes", "colunas", "id_avaliacao,id_bebida,nota,comentario,compraria_novamente,data_avaliacao"])
        for item in db.query(Avaliacao).filter(Avaliacao.id_usuario == usuario.id_usuario).all():
            writer.writerow([
                "avaliacoes",
                item.id_avaliacao,
                f"{item.id_bebida},{item.nota},{item.comentario or ''},{item.compraria_novamente},{item.data_avaliacao}",
            ])

    if "favoritos" in categorias:
        writer.writerow(["favoritos", "colunas", "id_favorito,id_bebida,data_favorito"])
        for item in db.query(Favorito).filter(Favorito.id_usuario == usuario.id_usuario).all():
            writer.writerow(["favoritos", item.id_favorito, f"{item.id_bebida},{item.data_favorito}"])

    if "precos" in categorias:
        writer.writerow(["precos", "colunas", "id_preco,id_bebida,mercado,cidade,estado,valor,data_registro"])
        for item in db.query(Preco).filter(Preco.id_usuario == usuario.id_usuario).all():
            writer.writerow([
                "precos",
                item.id_preco,
                f"{item.id_bebida},{item.mercado or ''},{item.cidade or ''},{item.estado or ''},{item.valor},{item.data_registro}",
            ])

    if "bebidas" in categorias:
        writer.writerow(["bebidas", "colunas", "id_bebida,nome,marca,tipo,codigo_barras,criada_em"])
        for item in db.query(Bebida).filter(Bebida.id_criado_por == usuario.id_usuario).all():
            writer.writerow([
                "bebidas",
                item.id_bebida,
                f"{item.nome},{item.marca or ''},{item.tipo},{item.codigo_barras or ''},{item.criada_em}",
            ])

    return buffer.getvalue()


def politica_privacidade_texto() -> str:
    return f"""Política de Privacidade do Bebidas Scan

Versão: {LGPD_DOCUMENT_VERSION}

O Bebidas Scan trata dados pessoais para criar e proteger contas de usuário, permitir login, cadastro de bebidas, avaliações, favoritos, registro de preços, funcionamento do scanner e segurança do serviço.

Controlador: Bebidas Scan, em fase de projeto provisório.
Contato de privacidade: {LGPD_CONTACT_TEXT}.

Dados tratados: nome, nome de usuário, e-mail, senha protegida por hash, data de nascimento, aceite de maioridade, versões aceitas da Política de Privacidade e dos Termos de Uso, consentimento opcional de marketing, avaliações, favoritos, preços cadastrados, bebidas cadastradas e dados técnicos de segurança como IP em logs por prazo limitado.

Finalidades: autenticação, prevenção de fraude, operação do app, melhoria da base de bebidas, cumprimento de obrigações legais, atendimento de solicitações de titulares e envio de comunicações de marketing quando houver consentimento separado.

Compartilhamento: o app pode consultar a base pública Open Food Facts usando código de barras da bebida. O Bebidas Scan também usa infraestrutura técnica de hospedagem, banco de dados, backups e rede. Não vendemos dados pessoais.

Retenção: logs de segurança e auditoria podem ser mantidos por {LOG_RETENTION_TEXT}. Backups podem reter dados por {BACKUP_RETENTION_TEXT}. Refresh tokens expirados ou revogados devem ser limpos após {REFRESH_TOKEN_RETENTION_DAYS} dias.

Direitos do titular: o usuário pode solicitar confirmação de tratamento, acesso, correção, exportação, anonimização, exclusão, informação sobre compartilhamento, revogação de consentimento e revisão de preferências, conforme a LGPD.

Exclusão/anonimização: mediante confirmação por e-mail e senha, a conta é desativada, tokens são revogados, favoritos são apagados, comentários de avaliações são removidos, e avaliações, preços e bebidas podem ser mantidos sem vínculo direto com o usuário.
"""


def termos_uso_texto() -> str:
    return f"""Termos de Uso do Bebidas Scan

Versão: {LGPD_DOCUMENT_VERSION}

O Bebidas Scan permite consultar bebidas, cadastrar informações, avaliar produtos, favoritar itens e registrar preços. O usuário deve fornecer informações verdadeiras, manter sua senha protegida e usar o serviço de forma lícita.

O app é destinado a pessoas maiores de 18 anos. Ao criar conta, o usuário informa sua data de nascimento e declara cumprir esse requisito.

Dados de bebidas podem vir de cadastro de usuários ou de bases públicas como Open Food Facts. As informações podem estar incompletas ou incorretas, e o usuário deve avaliar criticamente os dados exibidos.

É proibido inserir conteúdo ofensivo, ilegal, enganoso, que viole direitos de terceiros ou que prejudique o funcionamento do serviço.

O Bebidas Scan pode remover ou corrigir dados, bloquear contas, revogar sessões e alterar funcionalidades para segurança, conformidade legal ou melhoria do produto.

Estes termos podem ser atualizados. Quando a versão mudar, o usuário deverá aceitar novamente para continuar usando o serviço.
"""
