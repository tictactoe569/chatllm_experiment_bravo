const { useEffect, useMemo, useRef, useState } = React;

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

const WELCOME_MESSAGE = {
  id: createMessageId(),
  role: "assistant",
  content: "Bem-vindo ao ChatLLM Lab. Como posso ajudar voce hoje?",
};

function App() {
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(!!token);
  const [sessions, setSessions] = useState([]);
  const [activeSessionKey, setActiveSessionKey] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const messagesRef = useRef(null);
  const abortControllerRef = useRef(null);
  const sessionsLoadedRef = useRef(false);
  const activeKeyRef = useRef(null);

  const setActiveKey = (key) => {
    setActiveSessionKey(key);
    activeKeyRef.current = key;
  };

  // Validar token existente ao montar
  useEffect(() => {
    if (token) {
      getMe(token)
        .then((userData) => setUser(userData))
        .catch(() => {
          localStorage.removeItem("token");
          setToken(null);
          setUser(null);
        })
        .finally(() => setAuthLoading(false));
    } else {
      setAuthLoading(false);
    }
  }, []);

  // Carregar sessoes apos autenticacao
  useEffect(() => {
    if (!token || sessionsLoadedRef.current) return;
    sessionsLoadedRef.current = true;

    (async () => {
      try {
        const data = await listSessions(token);
        setSessions(data);
        if (data && data.length > 0) {
          setActiveKey(data[0].session_key);
          const msgs = await getSessionMessages(token, data[0].session_key);
          setMessages(
            msgs.length === 0
              ? [WELCOME_MESSAGE]
              : msgs.map((m) => ({ id: createMessageId(), role: m.role, content: m.content }))
          );
        } else {
          const res = await createSession(token);
          const newSession = {
            session_key: res.session_key,
            title: null,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          };
          setSessions([newSession]);
          setActiveKey(res.session_key);
        }
      } catch (e) {
        // Silently handle init errors
      }
    })();
  }, [token]);

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
    const currentKey = activeKeyRef.current;

    try {
      const returnedKey = await sendMessageStream({
        message: cleaned,
        history: chatHistory,
        sessionKey: currentKey,
        token,
        signal: abortController.signal,
        onDelta: (delta) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, content: msg.content + delta }
                : msg
            )
          );
        },
      });

      // Reload sessions to get auto-title
      try {
        const data = await listSessions(token);
        setSessions(data);
      } catch (e) {}

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

  const handleAuth = (newToken) => {
    setToken(newToken);
    getMe(newToken).then((userData) => setUser(userData)).catch(() => {});
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
    setSessions([]);
    setActiveKey(null);
    sessionsLoadedRef.current = false;
    setMessages([{ ...WELCOME_MESSAGE, id: createMessageId() }]);
  };

  const handleNewSession = async () => {
    try {
      const res = await createSession(token);
      const newSession = {
        session_key: res.session_key,
        title: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      setSessions((prev) => [newSession, ...prev]);
      setActiveKey(res.session_key);
      setMessages([{ ...WELCOME_MESSAGE, id: createMessageId() }]);
      setSidebarOpen(true);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleSelectSession = async (sessionKey) => {
    if (sessionKey === activeSessionKey) return;
    setActiveKey(sessionKey);
    setMessages([{ ...WELCOME_MESSAGE, id: createMessageId() }]);
    try {
      const msgs = await getSessionMessages(token, sessionKey);
      if (msgs && msgs.length > 0) {
        setMessages(msgs.map((m) => ({ id: createMessageId(), role: m.role, content: m.content })));
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteSession = async (sessionKey) => {
    const previous = sessions.slice();
    const wasActive = sessionKey === activeSessionKey;
    setSessions((prev) => prev.filter((s) => s.session_key !== sessionKey));
    try {
      await deleteSession(token, sessionKey);
      if (wasActive) {
        const remaining = sessions.filter((s) => s.session_key !== sessionKey);
        if (remaining.length > 0) {
          handleSelectSession(remaining[0].session_key);
        } else {
          handleNewSession();
        }
      }
    } catch (err) {
      setSessions(previous);
      setError(err.message);
    }
  };

  // Tela de loading
  if (authLoading) {
    return (
      <main className="app-shell">
        <div className="auth-loading">Verificando autenticação...</div>
      </main>
    );
  }

  // Se nao autenticado, mostra modal
  if (!token) {
    return <AuthModal onAuth={handleAuth} />;
  }

  // Autenticado — renderiza o chat com sidebar
  return (
    <div className="app-layout">
      <Sidebar
        sessions={sessions}
        activeSessionKey={activeSessionKey}
        onSelectSession={handleSelectSession}
        onNewSession={handleNewSession}
        onDeleteSession={handleDeleteSession}
        onToggle={() => setSidebarOpen((p) => !p)}
        isOpen={sidebarOpen}
      />

      {!sidebarOpen && (
        <button
          className="sidebar-floating-toggle"
          onClick={() => setSidebarOpen(true)}
          type="button"
          title="Abrir sidebar"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </button>
      )}

      <main className="app-shell">
        <header className="app-header">
          <div className="brand">ChatLLM Lab</div>
          <div className="auth-info">
            <span className="user-email">{user?.email}</span>
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

        <div className="warning-banner">Lembre-se, voce precisa focar no experimento!!!</div>
      </main>
    </div>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);