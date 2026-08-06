package br.com.bebidasscan.api.email;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class TransactionalEmailService {

    private static final Logger LOGGER = LoggerFactory.getLogger(TransactionalEmailService.class);

    private final EmailTemplateService templates;
    private final ResendClient resendClient;

    public TransactionalEmailService(EmailTemplateService templates, ResendClient resendClient) {
        this.templates = templates;
        this.resendClient = resendClient;
    }

    public void sendWelcomeSafely(String email, String name, Integer userId) {
        sendSafely("boas_vindas", templates.welcome(email, name), userId);
    }

    public void sendPasswordReset(String email, String token) {
        resendClient.send(templates.passwordReset(email, token));
    }

    public void sendPasswordChangedSafely(String email, String name, Integer userId) {
        sendSafely("senha_alterada", templates.passwordChanged(email, name), userId);
    }

    public void sendPasswordRedefinedSafely(String email, String name, Integer userId) {
        sendSafely("senha_redefinida", templates.passwordRedefined(email, name), userId);
    }

    private void sendSafely(String type, EmailTemplateService.EmailMessage message, Integer userId) {
        try {
            resendClient.send(message);
        } catch (EmailNotConfiguredException exception) {
            LOGGER.warn("email_{}_nao_configurado userId={}", type, userId);
        } catch (RuntimeException exception) {
            LOGGER.error("email_{}_falhou userId={} errorType={}", type, userId, exception.getClass().getSimpleName());
        }
    }
}
