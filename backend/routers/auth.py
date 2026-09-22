from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User
from backend.schemas.auth import TokenResponse, UserCreate, UserLogin, UserOut
from backend.services.auth import (
    create_token,
    get_current_user,
    hash_password,
    verify_password,
)


router = APIRouter(tags=["auth"])


@router.post("/api/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> TokenResponse:
    """Cadastra um novo usuário e retorna token de acesso."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email já cadastrado",
        )

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_token(user.id)
    return TokenResponse(access_token=token)


@router.post("/api/auth/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    """Autentica um usuário e retorna token de acesso."""
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos",
        )

    token = create_token(user.id)
    return TokenResponse(access_token=token)


@router.post("/api/auth/logout", status_code=status.HTTP_200_OK)
def logout(current_user: User = Depends(get_current_user)) -> dict:
    """Invalida a sessão do lado do cliente (stateless — o token é descartado pelo frontend)."""
    return {"message": "Logout realizado com sucesso"}


@router.get("/api/auth/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> User:
    """Retorna os dados do usuário autenticado."""
    return current_user