from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.auth_utils import hash_password
from backend.database import Base, get_db
from backend.dependencies import create_access_token, get_current_user
from backend.main import app
from backend.models import User


@pytest.fixture(scope="session")
def engine():
    """Cria um engine SQLite em memoria para os testes."""
    return create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


@pytest.fixture(scope="session")
def tables(engine):
    """Cria todas as tabelas antes dos testes e as remove ao final."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(engine, tables):
    """Retorna uma sessao de banco limpa para cada teste.

    Usa transacao aninhada (SAVEPOINT) para isolar cada teste.
    Ao final do teste, o rollback desfaz todas as alteracoes.
    """
    connection = engine.connect()
    transaction = connection.begin()

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def test_user(db_session):
    """Cria um usuario de teste no banco e retorna o modelo."""
    user = User(
        email="teste@exemplo.com",
        hashed_password=hash_password("senha123"),
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user):
    """Gera um token JWT valido para o usuario de teste."""
    return create_access_token(test_user.id)


@pytest.fixture
def auth_headers(auth_token):
    """Retorna headers de autorizacao com token JWT."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def client(db_session, test_user):
    """Retorna um TestClient do FastAPI com o banco de testes e auth injetados."""

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    def _override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def unauth_client(db_session):
    """Retorna um TestClient do FastAPI SEM override do get_current_user.

    Util para testar endpoints sem autenticacao.
    """

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
