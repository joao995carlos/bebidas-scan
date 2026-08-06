package br.com.bebidasscan.api.common.dto;

import java.time.OffsetDateTime;

public record ErrorResponse(
        String detail,
        String path,
        String requestId,
        OffsetDateTime timestamp
) {
}
