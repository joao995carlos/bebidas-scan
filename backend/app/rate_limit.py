import os
import hashlib
from collections import defaultdict, deque
from time import monotonic

from fastapi import HTTPException, Request

from .logging_config import log_event, security_logger

AUTH_RATE_LIMIT_MAX_ATTEMPTS = int(os.getenv("AUTH_RATE_LIMIT_MAX_ATTEMPTS", "10"))
AUTH_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("AUTH_RATE_LIMIT_WINDOW_SECONDS", "60"))
AUTH_RATE_LIMIT_IDENTITY_MAX_ATTEMPTS = int(
    os.getenv("AUTH_RATE_LIMIT_IDENTITY_MAX_ATTEMPTS", "5")
)
AUTH_RATE_LIMIT_IDENTITY_WINDOW_SECONDS = int(
    os.getenv("AUTH_RATE_LIMIT_IDENTITY_WINDOW_SECONDS", "300")
)
AUTH_LOCKOUT_SECONDS = int(os.getenv("AUTH_LOCKOUT_SECONDS", "900"))
TRUST_PROXY_HEADERS = os.getenv("TRUST_PROXY_HEADERS", "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "sim",
}

_attempts: dict[str, deque[float]] = defaultdict(deque)
_blocked_until: dict[str, float] = {}


def _client_host(request: Request) -> str:
    if TRUST_PROXY_HEADERS:
        cloudflare_ip = request.headers.get("cf-connecting-ip")
        if cloudflare_ip:
            return cloudflare_ip.strip()

        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",", 1)[0].strip()

    return request.client.host if request.client else "unknown"


def _normalizar_identidade(identity: str | None) -> str | None:
    if identity is None:
        return None
    identity = identity.strip().lower()
    return identity or None


def _identity_log(identity: str | None) -> str:
    if not identity:
        return "-"
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12]


def _key_log(key: str) -> str:
    if ":identity:" not in key:
        return key
    prefix, identity = key.rsplit(":identity:", 1)
    return f"{prefix}:identity:{_identity_log(identity)}"


def _limpar_janela(entries: deque[float], window_seconds: int, now: float) -> None:
    window_start = now - window_seconds
    while entries and entries[0] < window_start:
        entries.popleft()


def _bloqueado(key: str, now: float) -> bool:
    blocked_until = _blocked_until.get(key)
    if not blocked_until:
        return False
    if blocked_until <= now:
        _blocked_until.pop(key, None)
        return False
    return True


def _bloquear(key: str, now: float) -> None:
    _blocked_until[key] = now + AUTH_LOCKOUT_SECONDS


def limitar_auth(request: Request, action: str, identity: str | None = None) -> None:
    client_host = _client_host(request)
    identity = _normalizar_identidade(identity)
    ip_key = f"{action}:ip:{client_host}"
    identity_key = f"{action}:identity:{identity}" if identity else None
    now = monotonic()

    keys = [ip_key]
    if identity_key:
        keys.append(identity_key)

    for key in keys:
        if _bloqueado(key, now):
            log_event(
                security_logger,
                30,
                "auth_lockout",
                "Autenticação bloqueada por lockout",
                action=action,
                client=client_host,
                identityHash=_identity_log(identity),
                key=_key_log(key),
            )
            raise HTTPException(
                status_code=429,
                detail="Muitas tentativas. Aguarde um pouco e tente novamente.",
            )

    ip_entries = _attempts[ip_key]
    _limpar_janela(ip_entries, AUTH_RATE_LIMIT_WINDOW_SECONDS, now)
    if len(ip_entries) >= AUTH_RATE_LIMIT_MAX_ATTEMPTS:
        _bloquear(ip_key, now)
        _raise_rate_limit(action, client_host, identity, ip_key, len(ip_entries))

    if identity_key:
        identity_entries = _attempts[identity_key]
        _limpar_janela(identity_entries, AUTH_RATE_LIMIT_IDENTITY_WINDOW_SECONDS, now)
        if len(identity_entries) >= AUTH_RATE_LIMIT_IDENTITY_MAX_ATTEMPTS:
            _bloquear(identity_key, now)
            _raise_rate_limit(
                action,
                client_host,
                identity,
                identity_key,
                len(identity_entries),
            )
        identity_entries.append(now)

    ip_entries.append(now)


def registrar_auth_sucesso(request: Request, action: str, identity: str | None = None) -> None:
    client_host = _client_host(request)
    identity = _normalizar_identidade(identity)
    keys = [f"{action}:ip:{client_host}"]
    if identity:
        keys.append(f"{action}:identity:{identity}")
    for key in keys:
        _attempts.pop(key, None)
        _blocked_until.pop(key, None)


def _raise_rate_limit(
    action: str,
    client_host: str,
    identity: str | None,
    key: str,
    attempts: int,
) -> None:
    log_event(
        security_logger,
        30,
        "rate_limit",
        "Rate limit acionado",
        action=action,
        client=client_host,
        identityHash=_identity_log(identity),
        key=_key_log(key),
        attempts=attempts,
        lockoutSeconds=AUTH_LOCKOUT_SECONDS,
    )
    raise HTTPException(
        status_code=429,
        detail="Muitas tentativas. Aguarde um pouco e tente novamente.",
    )
