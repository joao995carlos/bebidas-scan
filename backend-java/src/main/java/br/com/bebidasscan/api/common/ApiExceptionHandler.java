package br.com.bebidasscan.api.common;

import br.com.bebidasscan.api.common.dto.ErrorResponse;
import br.com.bebidasscan.api.observability.LogSanitizer;
import br.com.bebidasscan.api.observability.MdcKeys;
import jakarta.persistence.EntityNotFoundException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.ConstraintViolationException;
import java.time.OffsetDateTime;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.server.ResponseStatusException;

@RestControllerAdvice
public class ApiExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(ApiExceptionHandler.class);

    private final LogSanitizer logSanitizer = new LogSanitizer();

    @ExceptionHandler(ApiException.class)
    public ResponseEntity<ErrorResponse> handleApiException(ApiException exception, HttpServletRequest request) {
        HttpStatus status = exception.getStatus() == null ? HttpStatus.BAD_REQUEST : exception.getStatus();
        if (status.is5xxServerError()) {
            log.error("api_exception status={} path={} detail={}", status.value(), request.getRequestURI(),
                    logSanitizer.sanitizeText(exception.getMessage()), exception);
        } else {
            log.warn("api_exception status={} path={} detail={}", status.value(), request.getRequestURI(),
                    logSanitizer.sanitizeText(exception.getMessage()));
        }
        return ResponseEntity.status(status).body(error(exception.getMessage(), request));
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidation(
            MethodArgumentNotValidException exception,
            HttpServletRequest request
    ) {
        String detail = exception.getBindingResult().getFieldErrors().stream()
                .map(error -> error.getField() + ": " + error.getDefaultMessage())
                .collect(Collectors.joining("; "));
        return ResponseEntity.status(HttpStatus.UNPROCESSABLE_ENTITY)
                .body(error(detail.isBlank() ? "Dados invalidos" : detail, request));
    }

    @ExceptionHandler(ConstraintViolationException.class)
    public ResponseEntity<ErrorResponse> handleConstraintViolation(
            ConstraintViolationException exception,
            HttpServletRequest request
    ) {
        String detail = exception.getConstraintViolations().stream()
                .map(violation -> violation.getPropertyPath() + ": " + violation.getMessage())
                .collect(Collectors.joining("; "));
        return ResponseEntity.status(HttpStatus.UNPROCESSABLE_ENTITY)
                .body(error(detail.isBlank() ? "Dados invalidos" : detail, request));
    }

    @ExceptionHandler(ResponseStatusException.class)
    public ResponseEntity<ErrorResponse> handleResponseStatusException(
            ResponseStatusException exception,
            HttpServletRequest request
    ) {
        String detail = exception.getReason() == null || exception.getReason().isBlank()
                ? "Requisicao invalida"
                : exception.getReason();
        return ResponseEntity.status(exception.getStatusCode())
                .headers(exception.getHeaders())
                .body(error(detail, request));
    }

    @ExceptionHandler(EntityNotFoundException.class)
    public ResponseEntity<ErrorResponse> handleEntityNotFound(EntityNotFoundException exception, HttpServletRequest request) {
        return ResponseEntity.status(HttpStatus.NOT_FOUND).body(error("Registro nao encontrado", request));
    }

    @ExceptionHandler(RuntimeException.class)
    public ResponseEntity<ErrorResponse> handleRuntime(RuntimeException exception, HttpServletRequest request) {
        log.error("unhandled_exception path={}", request.getRequestURI(), exception);
        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(error("Erro interno do servidor", request));
    }

    private static ErrorResponse error(String detail, HttpServletRequest request) {
        return new ErrorResponse(
                detail,
                request.getRequestURI(),
                MDC.get(MdcKeys.REQUEST_ID),
                OffsetDateTime.now()
        );
    }
}
