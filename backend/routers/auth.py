from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from backend.services.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


router = APIRouter()
security_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Dependência que extrai e valida o usuário a partir do token JWT."""
    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: int | None = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: user_id ausente.",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado.",
        )

    return user


@router.post("/api/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Cadastra um novo usuário e retorna um token JWT."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email já cadastrado.",
        )

    hashed = hash_password(payload.password)
    user = User(email=payload.email, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(email=user.email, user_id=user.id)
    return TokenResponse(access_token=token)


@router.post("/api/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Autentica um usuário e retorna um token JWT."""
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos.",
        )

    token = create_access_token(email=user.email, user_id=user.id)
    return TokenResponse(access_token=token)


@router.post("/api/logout")
def logout() -> dict[str, str]:
    """Logout: como o token é stateless (JWT), o frontend apenas descarta o token localmente."""
    return {"message": "Logout realizado com sucesso."}


@router.get("/api/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Retorna os dados do usuário autenticado."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        created_at=current_user.created_at.isoformat(),
    )