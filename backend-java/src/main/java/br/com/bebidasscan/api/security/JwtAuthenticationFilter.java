package br.com.bebidasscan.api.security;

import br.com.bebidasscan.api.observability.MdcKeys;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.List;
import org.slf4j.MDC;
import org.springframework.http.HttpHeaders;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.filter.OncePerRequestFilter;

public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtService jwtService;
    private final AuthenticatedUserService authenticatedUserService;

    public JwtAuthenticationFilter(
            JwtService jwtService,
            AuthenticatedUserService authenticatedUserService
    ) {
        this.jwtService = jwtService;
        this.authenticatedUserService = authenticatedUserService;
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {
        String authorization = request.getHeader(HttpHeaders.AUTHORIZATION);
        if (authorization == null || authorization.isBlank()) {
            filterChain.doFilter(request, response);
            return;
        }

        if (!authorization.regionMatches(true, 0, "Bearer ", 0, 7)) {
            writeUnauthorized(response);
            return;
        }

        String token = authorization.substring(7).trim();
        JwtClaims claims = jwtService.verifyAccessToken(token).orElse(null);
        if (claims == null) {
            writeUnauthorized(response);
            return;
        }

        AuthenticatedUser user = authenticatedUserService.findActiveUser(claims.userId()).orElse(null);
        if (user == null) {
            writeUnauthorized(response);
            return;
        }

        List<SimpleGrantedAuthority> authorities = user.isAdmin()
                ? List.of(new SimpleGrantedAuthority("ROLE_ADMIN"), new SimpleGrantedAuthority("ROLE_USER"))
                : List.of(new SimpleGrantedAuthority("ROLE_USER"));

        UsernamePasswordAuthenticationToken authentication =
                new UsernamePasswordAuthenticationToken(user, null, authorities);
        SecurityContextHolder.getContext().setAuthentication(authentication);
        MDC.put(MdcKeys.USER_ID, String.valueOf(user.idUsuario()));

        try {
            filterChain.doFilter(request, response);
        } finally {
            SecurityContextHolder.clearContext();
            MDC.remove(MdcKeys.USER_ID);
        }
    }

    private void writeUnauthorized(HttpServletResponse response) throws IOException {
        SecurityContextHolder.clearContext();
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setContentType("application/json;charset=UTF-8");
        response.getWriter().write("{\"detail\":\"Token invalido ou expirado\"}");
    }
}
