from __future__ import annotations

from fastapi.testclient import TestClient


class TestSessionsAPI:
    def test_list_sessions_empty(self, client: TestClient, auth_headers: dict):
        """Usuario sem sessoes deve receber lista vazia."""
        response = client.get("/api/sessions", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_create_session(self, client: TestClient, auth_headers: dict):
        """Criar sessao deve retornar 201 com dados da sessao."""
        response = client.post("/api/sessions", headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["title"] is None

    def test_list_sessions_after_create(self, client: TestClient, auth_headers: dict):
        """Apos criar, a sessao deve aparecer na lista."""
        client.post("/api/sessions", headers=auth_headers)
        response = client.get("/api/sessions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] is None

    def test_delete_session(self, client: TestClient, auth_headers: dict):
        """Deletar sessao deve retornar 200."""
        create_resp = client.post("/api/sessions", headers=auth_headers)
        session_id = create_resp.json()["id"]

        response = client.delete(f"/api/sessions/{session_id}", headers=auth_headers)
        assert response.status_code == 200

        # Lista deve estar vazia
        list_resp = client.get("/api/sessions", headers=auth_headers)
        assert list_resp.json() == []

    def test_delete_session_not_found(self, client: TestClient, auth_headers: dict):
        """Deletar sessao inexistente deve retornar 404."""
        response = client.delete("/api/sessions/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_session_other_user(self, client: TestClient, auth_headers: dict, db_session):
        """Deletar sessao de outro usuario deve retornar 403."""
        from backend.models import ChatSession, User
        from backend.services.auth import hash_password

        other = User(email="other@test.com", hashed_password=hash_password("x"))
        db_session.add(other)
        db_session.commit()

        session = ChatSession(user_id=other.id)
        db_session.add(session)
        db_session.commit()

        response = client.delete(f"/api/sessions/{session.id}", headers=auth_headers)
        assert response.status_code == 403

    def test_get_session_messages_empty(self, client: TestClient, auth_headers: dict):
        """Sessao sem mensagens deve retornar lista vazia."""
        create_resp = client.post("/api/sessions", headers=auth_headers)
        session_id = create_resp.json()["id"]

        response = client.get(f"/api/sessions/{session_id}/messages", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_get_session_messages_other_user(self, client: TestClient, auth_headers: dict, db_session):
        """Acessar mensagens de sessao de outro usuario deve retornar 403."""
        from backend.models import ChatSession, User
        from backend.services.auth import hash_password

        other = User(email="other2@test.com", hashed_password=hash_password("x"))
        db_session.add(other)
        db_session.commit()

        session = ChatSession(user_id=other.id)
        db_session.add(session)
        db_session.commit()

        response = client.get(f"/api/sessions/{session.id}/messages", headers=auth_headers)
        assert response.status_code == 403

    def test_sessions_require_auth(self, client: TestClient):
        """Todas as rotas de sessao devem exigir autenticacao."""
        assert client.get("/api/sessions").status_code == 401
        assert client.post("/api/sessions").status_code == 401
        assert client.delete("/api/sessions/1").status_code == 401
        assert client.get("/api/sessions/1/messages").status_code == 401