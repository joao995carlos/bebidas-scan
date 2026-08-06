package br.com.bebidasscan.api.config;

import br.com.bebidasscan.api.observability.ClientIpResolver;
import br.com.bebidasscan.api.observability.LogSanitizer;
import br.com.bebidasscan.api.observability.RequestBodySizeFilter;
import br.com.bebidasscan.api.observability.StructuredRequestLoggingFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class ObservabilityConfig {

    @Bean
    LogSanitizer logSanitizer() {
        return new LogSanitizer();
    }

    @Bean
    ClientIpResolver clientIpResolver(BebidasScanProperties properties) {
        return new ClientIpResolver(properties);
    }

    @Bean
    RequestBodySizeFilter requestBodySizeFilter(
            BebidasScanProperties properties,
            ClientIpResolver clientIpResolver
    ) {
        return new RequestBodySizeFilter(properties, clientIpResolver);
    }

    @Bean
    StructuredRequestLoggingFilter structuredRequestLoggingFilter(
            ClientIpResolver clientIpResolver,
            LogSanitizer logSanitizer
    ) {
        return new StructuredRequestLoggingFilter(clientIpResolver, logSanitizer);
    }
}
