package br.com.bebidasscan.api.lgpd;

import java.util.Map;
import org.springframework.stereotype.Service;

@Service
public class LgpdDocumentService {

    public static final String DOCUMENT_VERSION = "2026-07-14";
    private static final String CONTACT_TEXT = "canal de privacidade a ser definido";
    private static final String BACKUP_RETENTION_TEXT = "ate 180 dias, conforme necessidade tecnica de restauracao";
    private static final String LOG_RETENTION_TEXT = "180 dias";
    public static final int REFRESH_TOKEN_RETENTION_DAYS = 30;

    public Map<String, String> privacyPolicy() {
        return Map.of("versao", DOCUMENT_VERSION, "texto", privacyPolicyText());
    }

    public Map<String, String> termsOfUse() {
        return Map.of("versao", DOCUMENT_VERSION, "texto", termsOfUseText());
    }

    public String privacyPolicyText() {
        return """
                Politica de Privacidade do Bebidas Scan

                Versao: %s

                O Bebidas Scan trata dados pessoais para criar e proteger contas de usuario, permitir login, cadastro de bebidas, avaliacoes, favoritos, registro de precos, funcionamento do scanner e seguranca do servico.

                Controlador: Bebidas Scan, em fase de projeto provisorio.
                Contato de privacidade: %s.

                Dados tratados: nome, nome de usuario, e-mail, senha protegida por hash, data de nascimento, aceite de maioridade, versoes aceitas da Politica de Privacidade e dos Termos de Uso, consentimento opcional de marketing, avaliacoes, favoritos, precos cadastrados, bebidas cadastradas e dados tecnicos de seguranca como IP em logs por prazo limitado.

                Finalidades: autenticacao, prevencao de fraude, operacao do app, melhoria da base de bebidas, cumprimento de obrigacoes legais, atendimento de solicitacoes de titulares e envio de comunicacoes de marketing quando houver consentimento separado.

                Compartilhamento: o app pode consultar a base publica Open Food Facts usando codigo de barras da bebida. O Bebidas Scan tambem usa infraestrutura tecnica de hospedagem, banco de dados, backups e rede. Nao vendemos dados pessoais.

                Retencao: logs de seguranca e auditoria podem ser mantidos por %s. Backups podem reter dados por %s. Refresh tokens expirados ou revogados devem ser limpos apos %d dias.

                Direitos do titular: o usuario pode solicitar confirmacao de tratamento, acesso, correcao, exportacao, anonimizacao, exclusao, informacao sobre compartilhamento, revogacao de consentimento e revisao de preferencias, conforme a LGPD.

                Exclusao/anonimizacao: mediante confirmacao por e-mail e senha, a conta e desativada, tokens sao revogados, favoritos sao apagados, comentarios de avaliacoes sao removidos, e avaliacoes, precos e bebidas podem ser mantidos sem vinculo direto com o usuario.
                """.formatted(DOCUMENT_VERSION, CONTACT_TEXT, LOG_RETENTION_TEXT, BACKUP_RETENTION_TEXT, REFRESH_TOKEN_RETENTION_DAYS);
    }

    public String termsOfUseText() {
        return """
                Termos de Uso do Bebidas Scan

                Versao: %s

                O Bebidas Scan permite consultar bebidas, cadastrar informacoes, avaliar produtos, favoritar itens e registrar precos. O usuario deve fornecer informacoes verdadeiras, manter sua senha protegida e usar o servico de forma licita.

                O app e destinado a pessoas maiores de 18 anos. Ao criar conta, o usuario informa sua data de nascimento e declara cumprir esse requisito.

                Dados de bebidas podem vir de cadastro de usuarios ou de bases publicas como Open Food Facts. As informacoes podem estar incompletas ou incorretas, e o usuario deve avaliar criticamente os dados exibidos.

                E proibido inserir conteudo ofensivo, ilegal, enganoso, que viole direitos de terceiros ou que prejudique o funcionamento do servico.

                O Bebidas Scan pode remover ou corrigir dados, bloquear contas, revogar sessoes e alterar funcionalidades para seguranca, conformidade legal ou melhoria do produto.

                Estes termos podem ser atualizados. Quando a versao mudar, o usuario devera aceitar novamente para continuar usando o servico.
                """.formatted(DOCUMENT_VERSION);
    }
}
