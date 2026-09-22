from __future__ import annotations

from datetime import datetime, timezone

from backend.models import ChatMessage, ChatSession, User
from backend.services.auth import hash_password


class TestChatSession:
    def test_create_session(self, db_session):
        """Deve criar uma sessao vinculada a um usuario."""
        user = User(email="sess@test.com", hashed_password=hash_password("x"))
        db_session.add(user)
        db_session.commit()

        session = ChatSession(user_id=user.id)
        db_session.add(session)
        db_session.commit()
        db_session.refresh(session)

        assert session.id is not None
        assert session.user_id == user.id
        assert session.title is None
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)

    def test_session_title_auto(self, db_session):
        """Deve aceitar titulo nulo ate ser definido."""
        user = User(email="sess2@test.com", hashed_password=hash_password("x"))
        db_session.add(user)
        db_session.commit()

        session = ChatSession(user_id=user.id)
        db_session.add(session)
        db_session.commit()

        assert session.title is None

        session.title = "Meu titulo"
        db_session.commit()
        assert session.title == "Meu titulo"

    def test_session_cascade_delete(self, db_session):
        """Deletar sessao deve deletar mensagens associadas."""
        user = User(email="sess3@test.com", hashed_password=hash_password("x"))
        db_session.add(user)
        db_session.commit()

        session = ChatSession(user_id=user.id)
        db_session.add(session)
        db_session.commit()

        msg = ChatMessage(session_id=session.id, role="user", content="teste")
        db_session.add(msg)
        db_session.commit()

        db_session.delete(session)
        db_session.commit()

        remaining = db_session.query(ChatMessage).filter(ChatMessage.session_id == session.id).all()
        assert len(remaining) == 0


class TestChatMessage:
    def test_create_message_defaults(self, db_session):
        """Deve criar uma mensagem com valores padrao."""
        user = User(email="msg@test.com", hashed_password=hash_password("x"))
        db_session.add(user)
        db_session.commit()

        session = ChatSession(user_id=user.id)
        db_session.add(session)
        db_session.commit()

        msg = ChatMessage(
            session_id=session.id,
            role="user",
            content="Ola, mundo!",
        )
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)

        assert msg.id is not None
        assert msg.session_id == session.id
        assert msg.role == "user"
        assert msg.content == "Ola, mundo!"
        assert msg.model == "google/gemma-4-31b-it"
        assert isinstance(msg.created_at, datetime)

    def test_create_message_custom_model(self, db_session):
        """Deve criar uma mensagem com modelo customizado."""
        user = User(email="msg2@test.com", hashed_password=hash_password("x"))
        db_session.add(user)
        db_session.commit()

        session = ChatSession(user_id=user.id)
        db_session.add(session)
        db_session.commit()

        msg = ChatMessage(
            session_id=session.id,
            role="user",
            content="Teste",
            model="openai/gpt-4o",
        )
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)

        assert msg.model == "openai/gpt-4o"

    def test_query_by_session(self, db_session):
        """Deve filtrar mensagens por session_id."""
        user = User(email="msg3@test.com", hashed_password=hash_password("x"))
        db_session.add(user)
        db_session.commit()

        s1 = ChatSession(user_id=user.id)
        s2 = ChatSession(user_id=user.id)
        db_session.add_all([s1, s2])
        db_session.commit()

        msg1 = ChatMessage(session_id=s1.id, role="user", content="a")
        msg2 = ChatMessage(session_id=s2.id, role="user", content="b")
        db_session.add_all([msg1, msg2])
        db_session.commit()

        results = (
            db_session.query(ChatMessage)
            .filter(ChatMessage.session_id == s1.id)
            .all()
        )
        assert len(results) == 1
        assert results[0].content == "a"

    def test_query_by_role(self, db_session):
        """Deve filtrar mensagens pelo campo role."""
        user = User(email="msg4@test.com", hashed_password=hash_password("x"))
        db_session.add(user)
        db_session.commit()

        session = ChatSession(user_id=user.id)
        db_session.add(session)
        db_session.commit()

        msg1 = ChatMessage(session_id=session.id, role="user", content="pergunta")
        msg2 = ChatMessage(session_id=session.id, role="assistant", content="resposta")
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
        assert users[0].content == "pergunta"
        assert assistants[0].content == "resposta"

    def test_created_at_auto_set(self, db_session):
        """O campo created_at deve ser preenchido automaticamente com UTC now."""
        user = User(email="msg5@test.com", hashed_password=hash_password("x"))
        db_session.add(user)
        db_session.commit()

        session = ChatSession(user_id=user.id)
        db_session.add(session)
        db_session.commit()

        before = datetime.now(timezone.utc).replace(tzinfo=None)
        msg = ChatMessage(session_id=session.id, role="user", content="timestamp test")
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)
        after = datetime.now(timezone.utc).replace(tzinfo=None)

        assert before <= msg.created_at <= after

    def test_content_persists_long_text(self, db_session):
        """Deve persistir conteudos longos corretamente."""
        user = User(email="long@test.com", hashed_password=hash_password("x"))
        db_session.add(user)
        db_session.commit()
        session = ChatSession(user_id=user.id)
        db_session.add(session)
        db_session.commit()

        long_text = "Lorem ipsum " * 200
        msg = ChatMessage(session_id=session.id, role="user", content=long_text)
        db_session.add(msg)
        db_session.commit()
        db_session.refresh(msg)

        assert msg.content == long_text
