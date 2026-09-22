from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from collections.abc import Generator
from datetime import datetime, timezone

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.config import JWT_ALGORITHM, JWT_EXPIRY_HOURS, JWT_SECRET_KEY
from backend.database import get_db
from backend.models import User

# ── Password hashing (bcrypt direto, sem passlib) ────────────────────────────


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ── JWT (stdlib HMAC-SHA256, sem dependências de terceiros) ──────────────────


def _b64url(data: bytes) -> str:
    """Base64url sem padding, como especifica o JWT."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _decode_b64url(s: str) -> bytes:
    """Decodifica base64url com padding restaurado."""
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def create_token(user_id: int) -> str:
    """Gera um JWT assinado com HMAC-SHA256 usando apenas a stdlib."""
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    now = int(time.time())
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + JWT_EXPIRY_HOURS * 3600,
    }

    header_b64 = _b64url(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url(json.dumps(payload, separators=(",", ":")).encode("utf-8"))

    message = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(
        JWT_SECRET_KEY.encode("utf-8"), message, hashlib.sha256
    ).digest()
    sig_b64 = _b64url(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_token(token: str) -> dict:
    """Decodifica e verifica a assinatura de um JWT. Retorna o payload ou levanta exceção."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Token JWT mal formatado")

    header_b64, payload_b64, sig_b64 = parts

    # Verificar assinatura
    message = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(
        JWT_SECRET_KEY.encode("utf-8"), message, hashlib.sha256
    ).digest()
    actual_sig = _decode_b64url(sig_b64)

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Assinatura JWT inválida")

    payload = json.loads(_decode_b64url(payload_b64))

    # Verificar expiração
    exp = payload.get("exp", 0)
    if time.time() > exp:
        raise ValueError("Token JWT expirado")

    return payload


# ── Dependência FastAPI ──────────────────────────────────────────────────────

security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Extrai e valida o token Bearer, retorna o usuário autenticado."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido",
        )

    try:
        payload = decode_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: sem subject",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
        )

    return user