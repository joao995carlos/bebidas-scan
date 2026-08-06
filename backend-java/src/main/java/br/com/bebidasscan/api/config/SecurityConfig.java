package br.com.bebidasscan.api.config;

import br.com.bebidasscan.api.security.JwtAuthenticationFilter;
import br.com.bebidasscan.api.security.AuthenticatedUserService;
import br.com.bebidasscan.api.security.JwtService;
import java.util.Arrays;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.argon2.Argon2PasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    SecurityFilterChain securityFilterChain(
            HttpSecurity http,
            JwtAuthenticationFilter jwtAuthenticationFilter
    ) throws Exception {
        http.csrf(AbstractHttpConfigurer::disable);
        http.cors(Customizer.withDefaults());
        http.sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS));
        http.authorizeHttpRequests(auth -> auth
                .requestMatchers("/", "/health", "/actuator/health").permitAll()
                .requestMatchers(HttpMethod.GET, "/privacidade/**", "/resetar-senha", "/web/resetar-senha").permitAll()
                .requestMatchers(HttpMethod.POST, "/auth/registrar", "/auth/login", "/auth/refresh",
                        "/auth/solicitar-reset-senha", "/auth/confirmar-reset-senha", "/resetar-senha").permitAll()
                .requestMatchers("/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
        );
        http.addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);
        return http.build();
    }

    @Bean
    PasswordEncoder passwordEncoder() {
        return Argon2PasswordEncoder.defaultsForSpringSecurity_v5_8();
    }

    @Bean
    JwtAuthenticationFilter jwtAuthenticationFilter(
            JwtService jwtService,
            AuthenticatedUserService authenticatedUserService
    ) {
        return new JwtAuthenticationFilter(jwtService, authenticatedUserService);
    }

    @Bean
    CorsConfigurationSource corsConfigurationSource(BebidasScanProperties properties) {
        CorsConfiguration configuration = new CorsConfiguration();
        if (properties.corsOrigins() != null && !properties.corsOrigins().isBlank()) {
            configuration.setAllowedOrigins(Arrays.stream(properties.corsOrigins().split(","))
                    .map(String::trim)
                    .filter(origin -> !origin.isBlank())
                    .toList());
        }
        configuration.setAllowedMethods(Arrays.asList("GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"));
        configuration.setAllowedHeaders(Arrays.asList("Authorization", "Content-Type", "X-Request-ID"));
        configuration.setExposedHeaders(Arrays.asList("X-Request-ID"));
        configuration.setAllowCredentials(true);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }
}
