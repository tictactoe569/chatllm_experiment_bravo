from __future__ import annotations

from datetime import datetime, timezone

from backend.models import ChatMessage, User


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
        """Deve criar uma mensagem com valores padrao para session_key, model e created_at."""
        user = self._create_test_user(db_session, "defaults")
        msg = ChatMessage(
            user_id=user.id,
            role="user",
            content="Ola, mundo!",
        )
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
        """Deve criar uma mensagem com session_key customizada."""
        user = self._create_test_user(db_session, "session")
        msg = ChatMessage(
            user_id=user.id,
            session_key="session-abc",
            role="assistant",
            content="Resposta do assistente.",
        )
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)

        assert msg.session_key == "session-abc"
        assert msg.role == "assistant"

    def test_create_message_custom_model(self, db_session):
        """Deve criar uma mensagem com modelo customizado."""
        user = self._create_test_user(db_session, "model")
        msg = ChatMessage(
            user_id=user.id,
            role="user",
            content="Teste",
            model="openai/gpt-4o",
        )
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)

        assert msg.model == "openai/gpt-4o"

    def test_query_by_session_key(self, db_session):
        """Deve filtrar mensagens por session_key."""
        user = self._create_test_user(db_session, "query")
        msg1 = ChatMessage(user_id=user.id, session_key="s1", role="user", content="a")
        msg2 = ChatMessage(user_id=user.id, session_key="s2", role="user", content="b")
        db_session.add_all([msg1, msg2])
        db_session.commit()

        results = (
            db_session.query(ChatMessage)
            .filter(ChatMessage.session_key == "s1")
            .all()
        )
        assert len(results) == 1
        assert results[0].content == "a"

    def test_query_by_role(self, db_session):
        """Deve filtrar mensagens pelo campo role."""
        user = self._create_test_user(db_session, "role")
        msg1 = ChatMessage(user_id=user.id, role="user", content="pergunta")
        msg2 = ChatMessage(user_id=user.id, role="assistant", content="resposta")
        db_session.add_all([msg1, msg2])
        db_session.commit()

        users = (
            db_session.query(ChatMessage)
            .filter(ChatMessage.role == "user")
            .all()
        )
        assistants = (
            db_session.query(ChatMessage)
            .filter(ChatMessage.role == "assistant")
            .all()
        )
        assert len(users) == 1
        assert len(assistants) == 1