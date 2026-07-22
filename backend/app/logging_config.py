import contextvars
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any


request_id_ctx: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id",
    default=None,
)
user_id_ctx: contextvars.ContextVar[int | None] = contextvars.ContextVar(
    "user_id",
    default=None,
)

SENSITIVE_KEYS = {
    "authorization",
    "access_token",
    "refresh_token",
    "token",
    "token_hash",
    "jwt",
    "senha",
    "senha_hash",
    "password",
    "secret",
    "csrf_token",
    "web_access_token",
    "web_refresh_token",
    "cookie",
    "set-cookie",
    "email",
    "identity",
    "cpf",
    "telefone",
    "data_nascimento",
}
SENSITIVE_RE = re.compile(
    r"(?i)(bearer\s+)[a-z0-9._\-~+/=]+|"
    r"((access|refresh)?_?token|password|senha|secret|cpf|email)=([^&\s]+)|"
    r'("(?:access|refresh)?_?token"|"password"|"senha"|"secret"|"cpf"|"email")\s*:\s*"[^"]*"'
)
STANDARD_LOG_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
}


def set_request_id(request_id: str | None) -> contextvars.Token[str | None]:
    return request_id_ctx.set(request_id)


def reset_request_id(token: contextvars.Token[str | None]) -> None:
    request_id_ctx.reset(token)


def set_log_user_id(user_id: int | None) -> contextvars.Token[int | None]:
    return user_id_ctx.set(user_id)


def reset_log_user_id(token: contextvars.Token[int | None]) -> None:
    user_id_ctx.reset(token)


def _is_sensitive_key(key: str) -> bool:
    key_lower = key.lower()
    return any(sensitive in key_lower for sensitive in SENSITIVE_KEYS)


def sanitize(value: Any, key: str | None = None) -> Any:
    if key and _is_sensitive_key(key):
        return "***MASKED***"
    if isinstance(value, dict):
        return {str(k): sanitize(v, str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [sanitize(item) for item in value]
    if isinstance(value, str):
        def _mask(match: re.Match[str]) -> str:
            if match.group(1):
                return f"{match.group(1)}***MASKED***"
            if match.group(2):
                return f"{match.group(2)}***MASKED***"
            if match.group(5):
                return f"{match.group(5)}:\"***MASKED***\""
            return "***MASKED***"

        return SENSITIVE_RE.sub(_mask, value)
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": sanitize(record.getMessage()),
            "requestId": request_id_ctx.get(),
            "userId": user_id_ctx.get(),
        }

        for key, value in record.__dict__.items():
            if key in STANDARD_LOG_ATTRS or key.startswith("_"):
                continue
            data[key] = sanitize(value, key)

        if record.exc_info:
            data["exception"] = sanitize(self.formatException(record.exc_info))

        return json.dumps(data, ensure_ascii=False, default=str)


def configurar_logging() -> None:
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, level, logging.INFO))

    logging.getLogger("uvicorn.access").setLevel(os.getenv("UVICORN_ACCESS_LOG_LEVEL", "WARNING"))


def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    message: str,
    **context: Any,
) -> None:
    exc_info = context.pop("exc_info", None)
    logger.log(
        level,
        message,
        extra={"event": event, **sanitize(context)},
        exc_info=exc_info,
    )


app_logger = logging.getLogger("bebidas_scan.app")
security_logger = logging.getLogger("bebidas_scan.security")
audit_logger = logging.getLogger("bebidas_scan.audit")
