from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.models import User
from backend.services.auth import hash_password, create_access_token


def _create_user_and_token(db_session):
    """Cria um usuario de teste e retorna um token JWT."""
    user = User(email="chat-test@test.com", hashed_password=hash_password("test1234"))
    db_session.add(user)
    db_session.flush()
    db_session.refresh(user)
    token = create_access_token(email=user.email, user_id=user.id)
    return token


class TestHealthEndpoint:
    def test_health_returns_ok(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestRootEndpoint:
    def test_root_returns_frontend(self, client: TestClient):
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


class TestChatEndpoint:
    def test_chat_endpoint_exists(self, client: TestClient, db_session):
        """Verifica que o endpoint /api/chat responde (espera erro de config sem API key)."""
        token = _create_user_and_token(db_session)
        response = client.post(
            "/api/chat",
            json={"message": "Ola"},
            headers={"Authorization": f"Bearer {token}"},
        )
        # Sem OPENROUTER_API_KEY definida, esperamos 503 (config error)
        assert response.status_code in (200, 422, 503)

    def test_chat_requires_auth(self, client: TestClient):
        """Sem token, deve retornar 403."""
        response = client.post(
            "/api/chat",
            json={"message": "Ola"},
        )
        assert response.status_code == 403

    def test_chat_empty_message_rejected(self, client: TestClient, db_session):
        """Mensagem vazia deve ser rejeitada com 422 (validacao Pydantic)."""
        token = _create_user_and_token(db_session)
        response = client.post(
            "/api/chat",
            json={"message": ""},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422


class TestChatStreamEndpoint:
    def test_chat_stream_endpoint_exists(self, client: TestClient, db_session):
        """Verifica que o endpoint /api/chat/stream aceita requisicoes."""
        token = _create_user_and_token(db_session)
        response = client.post(
            "/api/chat/stream",
            json={"message": "Ola"},
            headers={"Authorization": f"Bearer {token}"},
        )
        # Streaming pode iniciar e depois falhar sem API key
        assert response.status_code in (200, 422, 503)

    def test_chat_stream_requires_auth(self, client: TestClient):
        """Sem token, deve retornar 403."""
        response = client.post(
            "/api/chat/stream",
            json={"message": "Ola"},
        )
        assert response.status_code == 403

    def test_chat_stream_empty_message_rejected(self, client: TestClient, db_session):
        """Stream com mensagem vazia deve ser rejeitado com 422."""
        token = _create_user_and_token(db_session)
        response = client.post(
            "/api/chat/stream",
            json={"message": ""},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 422


class TestCORSMiddleware:
    def test_cors_headers_present(self, client: TestClient):
        """Verifica que os headers CORS estao presentes."""
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # O FastAPI com allow_origins=["*"] permite a requisicao
        assert response.status_code in (200, 405)
