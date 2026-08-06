package br.com.bebidasscan.api.email;

import br.com.bebidasscan.api.config.BebidasScanProperties;
import org.springframework.stereotype.Service;
import org.springframework.web.util.HtmlUtils;

@Service
public class EmailTemplateService {

    private final BebidasScanProperties properties;

    public EmailTemplateService(BebidasScanProperties properties) {
        this.properties = properties;
    }

    public EmailMessage welcome(String email, String name) {
        String safeName = HtmlUtils.htmlEscape((name == null || name.isBlank()) ? "usuario" : name.trim());
        String content = """
                <p>Ola, %s.</p>
                <p>Sua conta no Bebidas Scan foi criada com sucesso.</p>
                <p>Agora voce pode escanear bebidas, salvar favoritos, avaliar produtos e manter seu historico com mais seguranca.</p>
                %s
                """.formatted(safeName, button(properties.appWebUrl(), "Abrir Bebidas Scan"));
        return new EmailMessage(email, "Bem-vindo ao Bebidas Scan", htmlBase("Bem-vindo ao Bebidas Scan", content));
    }

    public EmailMessage passwordReset(String email, String token) {
        String link = properties.passwordResetBaseUrl() + "?token=" + HtmlUtils.htmlEscape(token);
        String content = """
                <p>Recebemos uma solicitacao para redefinir sua senha no Bebidas Scan.</p>
                %s
                <p>Esse link expira em 30 minutos. Se voce nao pediu isso, ignore este e-mail.</p>
                """.formatted(button(link, "Redefinir minha senha"));
        return new EmailMessage(email, "Redefinicao de senha - Bebidas Scan", htmlBase("Redefinir senha", content));
    }

    public EmailMessage passwordChanged(String email, String name) {
        String safeName = HtmlUtils.htmlEscape((name == null || name.isBlank()) ? "usuario" : name.trim());
        String content = """
                <p>Ola, %s.</p>
                <p>Sua senha do Bebidas Scan foi alterada com sucesso.</p>
                <p>Se voce nao fez essa alteracao, solicite uma recuperacao de senha imediatamente.</p>
                """.formatted(safeName);
        return new EmailMessage(email, "Senha alterada - Bebidas Scan", htmlBase("Senha alterada", content));
    }

    public EmailMessage passwordRedefined(String email, String name) {
        String safeName = HtmlUtils.htmlEscape((name == null || name.isBlank()) ? "usuario" : name.trim());
        String content = """
                <p>Ola, %s.</p>
                <p>Sua senha do Bebidas Scan foi redefinida com sucesso.</p>
                <p>Se voce nao fez essa redefinicao, solicite uma nova recuperacao de senha e revise a seguranca da sua conta.</p>
                """.formatted(safeName);
        return new EmailMessage(email, "Senha redefinida - Bebidas Scan", htmlBase("Senha redefinida", content));
    }

    private static String htmlBase(String title, String content) {
        return """
                <div style="font-family: Arial, sans-serif; color: #1f1a17; line-height: 1.55;">
                  <h1 style="color: #5a2b14;">%s</h1>
                  %s
                  <hr style="border: none; border-top: 1px solid #eadfd5; margin: 24px 0;">
                  <p style="font-size: 12px; color: #6f625b;">Este e um e-mail transacional do Bebidas Scan.</p>
                </div>
                """.formatted(HtmlUtils.htmlEscape(title), content);
    }

    private static String button(String link, String text) {
        return """
                <p><a href="%s" style="background: #111111; color: #ffffff; display: inline-block; padding: 12px 18px; border-radius: 10px; text-decoration: none;">%s</a></p>
                """.formatted(HtmlUtils.htmlEscape(link), HtmlUtils.htmlEscape(text));
    }

    public record EmailMessage(String to, String subject, String html) {
    }
}
