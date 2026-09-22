const { useEffect, useMemo, useRef, useState, useCallback } = React;

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

const WELCOME_MESSAGE = {
  id: createMessageId(),
  role: "assistant",
  content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?",
};

function App() {
  const [user, setUser] = useState(null);
  const [authReady, setAuthReady] = useState(false);
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const messagesRef = useRef(null);
  const abortControllerRef = useRef(null);

  // ── Verificar token salvo ao montar ──────────────────────────────────────
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      setAuthReady(true);
      return;
    }
    fetchUser()
      .then((u) => {
        if (u) {
          setUser(u);
          return listSessions().then(setSessions);
        }
        localStorage.removeItem("access_token");
      })
      .catch(() => localStorage.removeItem("access_token"))
      .finally(() => setAuthReady(true));
  }, []);

  const chatHistory = useMemo(
    () => messages.filter((msg) => msg.role === "user" || msg.role === "assistant"),
    [messages]
  );

  useEffect(() => {
    const el = messagesRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  const onStop = () => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setBusy(false);
  };

  const onSubmit = async (event, inputRef) => {
    event.preventDefault();
    const cleaned = text.trim();
    if (!cleaned || busy) return;

    setError("");
    const userMessage = { id: createMessageId(), role: "user", content: cleaned };
    const assistantMessageId = createMessageId();

    setMessages((prev) => [
      ...prev,
      userMessage,
      { id: assistantMessageId, role: "assistant", content: "" },
    ]);
    setText("");
    setBusy(true);
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      await sendMessageStream({
        message: cleaned,
        history: chatHistory,
        sessionId: activeSessionId,
        signal: abortController.signal,
        onDelta: (delta) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, content: `${msg.content}${delta}` }
                : msg
            )
          );
        },
      });

      // Recarregar sessoes para atualizar titulo automatico
      listSessions().then(setSessions);

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId && !msg.content.trim()
            ? { ...msg, content: "Nao foi possivel obter resposta do modelo agora." }
            : msg
        )
      );
    } catch (err) {
      const aborted = err?.name === "AbortError";
      if (!aborted) {
        setError(err.message || "Falha inesperada ao gerar resposta.");
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? { ...msg, content: msg.content.trim() ? msg.content : "Nao foi possivel obter resposta do modelo agora." }
              : msg
          )
        );
      } else {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId && !msg.content.trim()
              ? { ...msg, content: "Resposta interrompida." }
              : msg
          )
        );
      }
    } finally {
      abortControllerRef.current = null;
      setBusy(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logoutUser();
    } catch {}
    localStorage.removeItem("access_token");
    setUser(null);
    setSessions([]);
    setActiveSessionId(null);
    setMessages([WELCOME_MESSAGE]);
  };

  const handleNewSession = async () => {
    try {
      const session = await createSession();
      setSessions((prev) => [session, ...prev]);
      setActiveSessionId(session.id);
      setMessages([WELCOME_MESSAGE]);
      setError("");
    } catch (err) {
      setError(err.message);
    }
  };

  const handleSelectSession = async (sessionId) => {
    if (sessionId === activeSessionId) return;
    setActiveSessionId(sessionId);
    setError("");
    try {
      const msgs = await fetchSessionMessages(sessionId);
      if (msgs.length === 0) {
        setMessages([WELCOME_MESSAGE]);
      } else {
        setMessages(
          msgs.map((m) => ({
            id: createMessageId(),
            role: m.role,
            content: m.content,
          }))
        );
      }
    } catch {
      setMessages([WELCOME_MESSAGE]);
    }
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await deleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (activeSessionId === sessionId) {
        setActiveSessionId(null);
        setMessages([WELCOME_MESSAGE]);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  // ── Tela de carregamento inicial ──────────────────────────────────────────
  if (!authReady) {
    return (
      <main className="app-shell">
        <div className="auth-loading">Carregando...</div>
      </main>
    );
  }

  // ── Tela de autenticação ──────────────────────────────────────────────────
  if (!user) {
    return <Auth onAuthSuccess={() => fetchUser().then(setUser).then(() => listSessions().then(setSessions))} />;
  }

  // ── Chat autenticado com sidebar ──────────────────────────────────────────
  return (
    <div className="app-layout">
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewSession={handleNewSession}
        onDeleteSession={handleDeleteSession}
      />

      <main className="app-shell">
        <header className="app-header">
          <div className="brand">ChatLLM Lab</div>
          <div className="header-right">
            <span className="user-email">{user.email}</span>
            <button className="logout-btn" onClick={handleLogout} type="button">
              Sair
            </button>
          </div>
        </header>

        <section className="messages" aria-live="polite" ref={messagesRef}>
          <div className="messages-inner">
            {messages.map((msg) => (
              <article key={msg.id} className={`bubble ${msg.role}`}>
                <MessageContent content={msg.content} />
              </article>
            ))}
          </div>
        </section>

        <Composer
          text={text}
          busy={busy}
          error={error}
          onChangeText={setText}
          onSubmit={onSubmit}
          onStop={onStop}
        />

        <div className="warning-banner">Lembre-se, você precisa focar no experimento!!!</div>
      </main>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

