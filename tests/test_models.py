from __future__ import annotations

from datetime import datetime, timezone

from backend.models import ChatMessage, Session, User


class TestUser:
    def test_create_user(self, db_session):
        user = User(email="teste@teste.com", hashed_password="hash_teste")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        assert user.id is not None
        assert user.email == "teste@teste.com"
        assert isinstance(user.created_at, datetime)


class TestChatMessage:
    def _create_test_user(self, db_session, suffix=""):
        user = User(
            email=f"user_{suffix}@teste.com",
            hashed_password="hash_teste",
        )
        db_session.add(user)
        db_session.flush()
        return user

    def test_create_message_defaults(self, db_session):
        user = self._create_test_user(db_session, "defaults")
        msg = ChatMessage(user_id=user.id, role="user", content="Ola, mundo!")
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)
        assert msg.id is not None
        assert msg.session_key == "default"
        assert msg.role == "user"
        assert msg.content == "Ola, mundo!"
        assert msg.model == "google/gemma-4-31b-it"
        assert isinstance(msg.created_at, datetime)

    def test_create_message_custom_session(self, db_session):
        user = self._create_test_user(db_session, "session")
        msg = ChatMessage(
            user_id=user.id,
            session_key="session-abc",
            role="assistant",
            content="Resposta.",
        )
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)
        assert msg.session_key == "session-abc"

    def test_query_by_session_key(self, db_session):
        user = self._create_test_user(db_session, "query")
        msg1 = ChatMessage(user_id=user.id, session_key="s1", role="user", content="a")
        msg2 = ChatMessage(user_id=user.id, session_key="s2", role="user", content="b")
        db_session.add_all([msg1, msg2])
        db_session.commit()
        results = db_session.query(ChatMessage).filter(ChatMessage.session_key == "s1").all()
        assert len(results) == 1


class TestSession:
    def test_create_session(self, db_session):
        user = User(email="sess@teste.com", hashed_password="hash")
        db_session.add(user)
        db_session.flush()
        session = Session(user_id=user.id, session_key="abc-123")
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        assert session.id is not None
        assert session.session_key == "abc-123"
        assert session.title is None
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)

    def test_session_with_title(self, db_session):
        user = User(email="sess2@teste.com", hashed_password="hash")
        db_session.add(user)
        db_session.flush()
        session = Session(user_id=user.id, session_key="key-456", title="Primeiras cinco palavras")
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)
        assert session.title == "Primeiras cinco palavras"

    def test_session_belongs_to_user(self, db_session):
        user = User(email="sess3@teste.com", hashed_password="hash")
        db_session.add(user)
        db_session.flush()
        session = Session(user_id=user.id, session_key="key-789")
        db_session.add(session)
        db_session.commit()
        assert session.user_id == user.id
        assert session.user.email == "sess3@teste.com"

    def test_session_unique_key(self, db_session):
        user = User(email="sess4@teste.com", hashed_password="hash")
        db_session.add(user)
        db_session.flush()
        db_session.add(Session(user_id=user.id, session_key="unique-key"))
        db_session.commit()
        # Second session with same key should fail
        import pytest
        from sqlalchemy.exc import IntegrityError
        db_session.add(Session(user_id=user.id, session_key="unique-key"))
        with pytest.raises(IntegrityError):
            db_session.commit()