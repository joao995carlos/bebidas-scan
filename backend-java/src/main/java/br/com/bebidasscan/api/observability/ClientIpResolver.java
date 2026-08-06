package br.com.bebidasscan.api.observability;

import br.com.bebidasscan.api.config.BebidasScanProperties;
import jakarta.servlet.http.HttpServletRequest;

public class ClientIpResolver {

    private final BebidasScanProperties properties;

    public ClientIpResolver(BebidasScanProperties properties) {
        this.properties = properties;
    }

    public String resolve(HttpServletRequest request) {
        if (properties.trustProxyHeaders()) {
            String cloudflareIp = request.getHeader("cf-connecting-ip");
            if (cloudflareIp != null && !cloudflareIp.isBlank()) {
                return cloudflareIp.trim();
            }

            String forwardedFor = request.getHeader("x-forwarded-for");
            if (forwardedFor != null && !forwardedFor.isBlank()) {
                return forwardedFor.split(",", 2)[0].trim();
            }
        }

        return request.getRemoteAddr() == null ? "unknown" : request.getRemoteAddr();
    }
}
