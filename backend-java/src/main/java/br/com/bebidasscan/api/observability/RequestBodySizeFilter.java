package br.com.bebidasscan.api.observability;

import br.com.bebidasscan.api.config.BebidasScanProperties;
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

@Order(Ordered.HIGHEST_PRECEDENCE + 1)
public class RequestBodySizeFilter extends OncePerRequestFilter {

    private static final Logger SECURITY_LOGGER = LoggerFactory.getLogger("bebidas_scan.security");

    private final BebidasScanProperties properties;
    private final ClientIpResolver clientIpResolver;

    public RequestBodySizeFilter(BebidasScanProperties properties, ClientIpResolver clientIpResolver) {
        this.properties = properties;
        this.clientIpResolver = clientIpResolver;
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {
        long contentLength = request.getContentLengthLong();
        if (contentLength > properties.maxRequestBodyBytes()) {
            SECURITY_LOGGER.warn("Requisicao bloqueada por tamanho excessivo action=http_request path={} size={} client={}",
                    request.getRequestURI(), contentLength, clientIpResolver.resolve(request));
            response.setStatus(HttpServletResponse.SC_REQUEST_ENTITY_TOO_LARGE);
            response.setContentType("application/json;charset=UTF-8");
            response.getWriter().write("{\"detail\":\"Requisicao muito grande\"}");
            return;
        }
        filterChain.doFilter(request, response);
    }
}
