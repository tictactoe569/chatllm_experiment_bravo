from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.services.auth import create_token


class TestAuthRegister:
    def test_register_success(self, client: TestClient):
        """Cadastro com dados válidos deve retornar 201 e token."""
        response = client.post(
            "/api/auth/register",
            json={"email": "novo@teste.com", "password": "senha123"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_email(self, client: TestClient):
        """Email duplicado deve retornar 409."""
        client.post(
            "/api/auth/register",
            json={"email": "dup@teste.com", "password": "senha123"},
        )
        response = client.post(
            "/api/auth/register",
            json={"email": "dup@teste.com", "password": "outrasenha"},
        )
        assert response.status_code == 409
        assert "já cadastrado" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client: TestClient):
        """Email inválido deve retornar 422."""
        response = client.post(
            "/api/auth/register",
            json={"email": "invalido", "password": "senha123"},
        )
        assert response.status_code == 422

    def test_register_short_password(self, client: TestClient):
        """Senha muito curta deve retornar 422."""
        response = client.post(
            "/api/auth/register",
            json={"email": "valido@teste.com", "password": "12"},
        )
        assert response.status_code == 422


class TestAuthLogin:
    def test_login_success(self, client: TestClient):
        """Login com credenciais corretas deve retornar token."""
        client.post(
            "/api/auth/register",
            json={"email": "login@teste.com", "password": "senha123"},
        )
        response = client.post(
            "/api/auth/login",
            json={"email": "login@teste.com", "password": "senha123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_login_wrong_password(self, client: TestClient):
        """Senha errada deve retornar 401."""
        client.post(
            "/api/auth/register",
            json={"email": "wrong@teste.com", "password": "senha123"},
        )
        response = client.post(
            "/api/auth/login",
            json={"email": "wrong@teste.com", "password": "errada"},
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        """Email não cadastrado deve retornar 401."""
        response = client.post(
            "/api/auth/login",
            json={"email": "naoexiste@teste.com", "password": "senha123"},
        )
        assert response.status_code == 401


class TestAuthMe:
    def test_me_authenticated(self, client: TestClient):
        """GET /me com token válido deve retornar dados do usuário."""
        client.post(
            "/api/auth/register",
            json={"email": "me@teste.com", "password": "senha123"},
        )
        login_resp = client.post(
            "/api/auth/login",
            json={"email": "me@teste.com", "password": "senha123"},
        )
        token = login_resp.json()["access_token"]

        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@teste.com"
        assert "id" in data
        assert "created_at" in data

    def test_me_no_token(self, client: TestClient):
        """GET /me sem token deve retornar 401."""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_me_invalid_token(self, client: TestClient):
        """GET /me com token inválido deve retornar 401."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer token-invalido"},
        )
        assert response.status_code == 401


class TestAuthLogout:
    def test_logout_authenticated(self, client: TestClient):
        """Logout com token válido deve retornar 200."""
        client.post(
            "/api/auth/register",
            json={"email": "logout@teste.com", "password": "senha123"},
        )
        login_resp = client.post(
            "/api/auth/login",
            json={"email": "logout@teste.com", "password": "senha123"},
        )
        token = login_resp.json()["access_token"]

        response = client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    def test_logout_no_token(self, client: TestClient):
        """Logout sem token deve retornar 401."""
        response = client.post("/api/auth/logout")
        assert response.status_code == 401