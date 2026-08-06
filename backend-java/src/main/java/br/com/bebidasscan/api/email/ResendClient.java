package br.com.bebidasscan.api.email;

import br.com.bebidasscan.api.config.BebidasScanProperties;
import java.util.List;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

@Service
public class ResendClient {

    private static final String RESEND_API_URL = "https://api.resend.com/emails";

    private final BebidasScanProperties properties;
    private final RestClient restClient;

    public ResendClient(BebidasScanProperties properties, RestClient.Builder restClientBuilder) {
        this.properties = properties;
        this.restClient = restClientBuilder.build();
    }

    public void send(EmailTemplateService.EmailMessage message) {
        if (properties.resendApiKey() == null || properties.resendApiKey().isBlank()) {
            throw new EmailNotConfiguredException("RESEND_API_KEY nao configurada");
        }
        restClient.post()
                .uri(RESEND_API_URL)
                .header("Authorization", "Bearer " + properties.resendApiKey())
                .body(Map.of(
                        "from", properties.emailFrom(),
                        "to", List.of(message.to()),
                        "subject", message.subject(),
                        "html", message.html()
                ))
                .retrieve()
                .toBodilessEntity();
    }
}
