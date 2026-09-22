from __future__ import annotations

from backend.models import User
from backend.services.auth import create_token, decode_token, hash_password, verify_password


class TestUserModel:
    def test_create_user(self, db_session):
        """Deve criar um usuário com email e senha hash."""
        user = User(
            email="teste@example.com",
            hashed_password=hash_password("minha-senha"),
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        assert user.id is not None
        assert user.email == "teste@example.com"
        assert user.hashed_password != "minha-senha"  # deve estar hash
        assert verify_password("minha-senha", user.hashed_password)

    def test_email_unique(self, db_session):
        """Email deve ser único no banco."""
        user1 = User(email="dup@example.com", hashed_password=hash_password("a"))
        db_session.add(user1)
        db_session.commit()

        user2 = User(email="dup@example.com", hashed_password=hash_password("b"))
        db_session.add(user2)

        import pytest
        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_query_by_email(self, db_session):
        """Deve buscar usuário por email."""
        user = User(email="busca@example.com", hashed_password=hash_password("x"))
        db_session.add(user)
        db_session.commit()

        found = db_session.query(User).filter(User.email == "busca@example.com").first()
        assert found is not None
        assert found.email == "busca@example.com"


class TestPasswordHashing:
    def test_hash_and_verify(self):
        """Hash deve ser verificável com a senha original."""
        hashed = hash_password("senha-segura-123")
        assert hashed != "senha-segura-123"
        assert verify_password("senha-segura-123", hashed)

    def test_wrong_password_fails(self):
        """Senha errada não deve passar na verificação."""
        hashed = hash_password("correta")
        assert not verify_password("errada", hashed)

    def test_different_hashes(self):
        """Mesma senha deve produzir hashes diferentes (salt)."""
        h1 = hash_password("mesma")
        h2 = hash_password("mesma")
        assert h1 != h2


class TestJWT:
    def test_create_and_decode(self):
        """Deve criar e decodificar um token JWT válido."""
        token = create_token(user_id=42)
        payload = decode_token(token)
        assert payload["sub"] == 42
        assert "exp" in payload
        assert "iat" in payload

    def test_expired_token(self):
        """Token expirado deve ser rejeitado."""
        import time

        # Criar token manualmente com exp passada
        from backend.services.auth import _b64url, _decode_b64url, hmac, hashlib, json
        from backend.config import JWT_SECRET_KEY

        header = {"alg": "HS256", "typ": "JWT"}
        payload = {"sub": 1, "iat": 0, "exp": 0}  # expirado em 1970

        h = _b64url(json.dumps(header, separators=(",", ":")).encode())
        p = _b64url(json.dumps(payload, separators=(",", ":")).encode())
        msg = f"{h}.{p}".encode()
        sig = _b64url(hmac.new(JWT_SECRET_KEY.encode(), msg, hashlib.sha256).digest())
        expired_token = f"{h}.{p}.{sig}"

        import pytest
        with pytest.raises(ValueError, match="Token JWT expirado"):
            decode_token(expired_token)

    def test_tampered_token(self):
        """Token com payload alterado deve ser rejeitado."""
        token = create_token(user_id=7)
        parts = token.split(".")
        # Alterar payload
        parts[1] = "eyJzdWIiOiI5OTkifQ"  # base64url de {"sub":999}
        tampered = ".".join(parts)

        import pytest
        with pytest.raises(ValueError, match="Assinatura JWT inválida"):
            decode_token(tampered)

    def test_malformed_token(self):
        """Token mal formatado deve ser rejeitado."""
        import pytest
        with pytest.raises(ValueError, match="Token JWT mal formatado"):
            decode_token("invalido")