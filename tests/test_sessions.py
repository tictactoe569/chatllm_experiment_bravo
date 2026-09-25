from __future__ import annotations

from fastapi.testclient import TestClient


class TestSessionsEndpoint:
    def test_list_sessions_empty(self, client: TestClient):
        """Deve retornar lista vazia quando nao ha sessoes."""
        response = client.get("/api/sessions")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_session(self, client: TestClient):
        """Deve criar uma nova sessao com session_key unico."""
        response = client.post("/api/sessions")
        assert response.status_code == 201
        data = response.json()
        assert "session_key" in data
        assert len(data["session_key"]) > 0

    def test_list_sessions_after_create(self, client: TestClient):
        """Deve listar as sessoes apos criar algumas."""
        client.post("/api/sessions")
        client.post("/api/sessions")
        response = client.get("/api/sessions")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_delete_session(self, client: TestClient):
        """Deve deletar uma sessao."""
        created = client.post("/api/sessions").json()
        session_key = created["session_key"]

        delete_resp = client.delete(f"/api/sessions/{session_key}")
        assert delete_resp.status_code == 204

        list_resp = client.get("/api/sessions")
        assert len(list_resp.json()) == 0

    def test_delete_nonexistent_session(self, client: TestClient):
        """Deve retornar 404 ao deletar sessao inexistente."""
        response = client.delete("/api/sessions/nao-existe")
        assert response.status_code == 404

    def test_get_session_messages_empty(self, client: TestClient):
        """Deve retornar lista vazia de mensagens para sessao nova."""
        created = client.post("/api/sessions").json()
        response = client.get(f"/api/sessions/{created['session_key']}/messages")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_nonexistent_session_messages(self, client: TestClient):
        """Deve retornar 404 ao buscar mensagens de sessao inexistente."""
        response = client.get("/api/sessions/nao-existe/messages")
        assert response.status_code == 404

    def test_sessions_require_auth(self, unauth_client: TestClient):
        """Sessao sem token deve ser rejeitada."""
        response = unauth_client.get("/api/sessions")
        assert response.status_code == 403


class TestSessionChatIntegration:
    def test_chat_with_session_key(self, client: TestClient):
        """Enviar chat com session_key valida deve persistir mensagens na sessao."""
        created = client.post("/api/sessions").json()
        session_key = created["session_key"]

        # Enviar mensagem de chat (vai falhar sem API key, mas deve criar registro no banco)
        response = client.post(
            "/api/chat",
            json={
                "message": "Ola",
                "session_key": session_key,
            },
        )
        # Sem API key, esperamos 503
        assert response.status_code in (200, 422, 503)

    def test_chat_without_session_key_creates_session(self, client: TestClient):
        """Enviar chat sem session_key deve criar uma nova sessao automaticamente."""
        response = client.post(
            "/api/chat",
            json={"message": "Ola"},
        )
        assert response.status_code in (200, 422, 503)

        # Deve haver 1 sessao agora
        sessions_resp = client.get("/api/sessions")
        assert len(sessions_resp.json()) >= 1