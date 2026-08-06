package br.com.bebidasscan.api.observability;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.web.filter.OncePerRequestFilter;

@Order(Ordered.LOWEST_PRECEDENCE)
public class StructuredRequestLoggingFilter extends OncePerRequestFilter {

    private static final Logger APP_LOGGER = LoggerFactory.getLogger("bebidas_scan.app");

    private final ClientIpResolver clientIpResolver;
    private final LogSanitizer logSanitizer;

    public StructuredRequestLoggingFilter(ClientIpResolver clientIpResolver, LogSanitizer logSanitizer) {
        this.clientIpResolver = clientIpResolver;
        this.logSanitizer = logSanitizer;
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {
        long startedAt = System.nanoTime();
        int statusCode = HttpServletResponse.SC_INTERNAL_SERVER_ERROR;

        try {
            filterChain.doFilter(request, response);
            statusCode = response.getStatus();
        } catch (Exception ex) {
            APP_LOGGER.error("Erro nao tratado durante requisicao HTTP action=http_request method={} path={} client={}",
                    request.getMethod(),
                    logSanitizer.sanitizeText(request.getRequestURI()),
                    clientIpResolver.resolve(request),
                    ex);
            throw ex;
        } finally {
            long durationMs = Math.round((System.nanoTime() - startedAt) / 1_000_000.0);
            String path = logSanitizer.sanitizeText(request.getRequestURI());
            if (statusCode >= 400) {
                APP_LOGGER.warn("Requisicao HTTP concluida action=http_request method={} path={} statusCode={} durationMs={} client={}",
                        request.getMethod(), path, statusCode, durationMs, clientIpResolver.resolve(request));
            } else {
                APP_LOGGER.info("Requisicao HTTP concluida action=http_request method={} path={} statusCode={} durationMs={} client={}",
                        request.getMethod(), path, statusCode, durationMs, clientIpResolver.resolve(request));
            }
        }
    }
}
