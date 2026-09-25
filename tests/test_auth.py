from __future__ import annotations

from fastapi.testclient import TestClient

from backend.auth_utils import hash_password, verify_password


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "minhaSenha123"
        hashed = hash_password(password)
        assert hashed != password
        assert ":" in hashed
        assert verify_password(password, hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("senhaCorreta")
        assert verify_password("senhaErrada", hashed) is False

    def test_invalid_hash_format(self):
        assert verify_password("qualquer", "formato_invalido") is False


class TestRegisterEndpoint:
    def test_register_success(self, client: TestClient):
        response = client.post(
            "/api/auth/register",
            json={"email": "novo@exemplo.com", "password": "minhaSenha123"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_email(self, client: TestClient):
        client.post(
            "/api/auth/register",
            json={"email": "duplicado@exemplo.com", "password": "senha123456"},
        )
        response = client.post(
            "/api/auth/register",
            json={"email": "duplicado@exemplo.com", "password": "outraSenha456"},
        )
        assert response.status_code == 409
        assert "já está cadastrado" in response.json()["detail"]

    def test_register_weak_password(self, client: TestClient):
        response = client.post(
            "/api/auth/register",
            json={"email": "fraca@exemplo.com", "password": "123"},
        )
        assert response.status_code == 422

    def test_register_invalid_email(self, client: TestClient):
        response = client.post(
            "/api/auth/register",
            json={"email": "invalido", "password": "senha123456"},
        )
        assert response.status_code == 422


class TestLoginEndpoint:
    def test_login_success(self, client: TestClient):
        client.post(
            "/api/auth/register",
            json={"email": "login@exemplo.com", "password": "minhaSenha123"},
        )
        response = client.post(
            "/api/auth/login",
            json={"email": "login@exemplo.com", "password": "minhaSenha123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient):
        response = client.post(
            "/api/auth/login",
            json={"email": "teste@exemplo.com", "password": "senhaErrada"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_email(self, client: TestClient):
        response = client.post(
            "/api/auth/login",
            json={"email": "inexistente@exemplo.com", "password": "senha123"},
        )
        assert response.status_code == 401


class TestMeEndpoint:
    def test_me_authenticated(self, client: TestClient, auth_headers):
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "teste@exemplo.com"
        assert "id" in data
        assert "created_at" in data

    def test_me_no_token(self, unauth_client: TestClient):
        """HTTPBearer retorna 403 quando o header Authorization esta ausente."""
        response = unauth_client.get("/api/auth/me")
        assert response.status_code == 403

    def test_me_invalid_token(self, unauth_client: TestClient):
        response = unauth_client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer token_invalido_aqui"},
        )
        assert response.status_code == 401

    def test_me_malformed_header(self, unauth_client: TestClient):
        """HTTPBearer retorna 403 quando o formato do header esta incorreto."""
        response = unauth_client.get(
            "/api/auth/me",
            headers={"Authorization": "InvalidFormat"},
        )
        assert response.status_code == 403