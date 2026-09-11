const { useEffect, useMemo, useRef, useState, useCallback } = React;

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

function AuthScreen({ onAuthSuccess }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setAuthError("");
    setLoading(true);
    try {
      if (mode === "register") {
        await register(email, password);
      } else {
        await login(email, password);
      }
      const user = await getMe();
      if (user) onAuthSuccess(user);
    } catch (err) {
      setAuthError(err.message || "Erro inesperado.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="brand">ChatLLM Lab</div>
      </header>
      <div style={{
        flex: 1, display: "flex", alignItems: "center", justifyContent: "center",
        padding: "24px",
      }}>
        <form onSubmit={handleSubmit} style={{
          width: "100%", maxWidth: 360, display: "flex", flexDirection: "column", gap: 16,
        }}>
          <h2 style={{ margin: 0, textAlign: "center", fontWeight: 600 }}>
            {mode === "login" ? "Entrar" : "Cadastrar"}
          </h2>

          {authError && (
            <div style={{
              padding: "10px 14px", background: "#fff5f5", color: "#c0392b",
              borderRadius: 8, fontSize: "0.9rem", border: "1px solid #fed7d7",
            }}>{authError}</div>
          )}

          <input
            type="email" placeholder="Email" required
            value={email} onChange={(e) => setEmail(e.target.value)}
            style={{
              padding: "12px 14px", borderRadius: 8, border: "1px solid var(--composer-border)",
              fontSize: "1rem", outline: "none",
            }}
          />
          <input
            type="password" placeholder="Senha (min. 8 caracteres)" required minLength={8}
            value={password} onChange={(e) => setPassword(e.target.value)}
            style={{
              padding: "12px 14px", borderRadius: 8, border: "1px solid var(--composer-border)",
              fontSize: "1rem", outline: "none",
            }}
          />

          <button type="submit" disabled={loading} style={{
            padding: "12px", borderRadius: 8, border: "none",
            background: "var(--accent)", color: "#fff", fontSize: "1rem",
            fontWeight: 600, cursor: loading ? "not-allowed" : "pointer", opacity: loading ? 0.7 : 1,
          }}>
            {loading ? "Aguarde..." : mode === "login" ? "Entrar" : "Cadastrar"}
          </button>

          <button type="button" onClick={() => { setMode(mode === "login" ? "register" : "login"); setAuthError(""); }}
            style={{
              padding: "8px", border: "none", background: "none", color: "var(--muted)",
              fontSize: "0.9rem", cursor: "pointer", textDecoration: "underline",
            }}>
            {mode === "login" ? "Não tem conta? Cadastre-se" : "Já tem conta? Faça login"}
          </button>
        </form>
      </div>
    </main>
  );
}

function App() {
  const [user, setUser] = useState(null);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const messagesRef = useRef(null);
  const abortControllerRef = useRef(null);

  const chatHistory = useMemo(
    () => messages.filter((msg) => msg.role === "user" || msg.role === "assistant"),
    [messages]
  );

  // Carrega sessões do usuário
  const loadSessions = useCallback(async () => {
    try {
      const list = await listSessions();
      setSessions(list);
      if (list.length > 0 && !activeSessionId) {
        setActiveSessionId(list[0].id);
      }
    } catch {
      // ignora
    }
  }, [activeSessionId]);

  // Carrega mensagens de uma sessão
  const loadMessages = useCallback(async (sessionId) => {
    // Por enquanto, mensagens são carregadas via history do chat
    // O backend retorna o histórico inline nas chamadas de chat
    setMessages([]);
  }, []);

  useEffect(() => {
    getMe().then((u) => {
      if (u) {
        setUser(u);
        return listSessions().then((list) => {
          setSessions(list);
          if (list.length > 0) {
            setActiveSessionId(list[0].id);
          }
        });
      }
    }).finally(() => setCheckingAuth(false));
  }, []);

  useEffect(() => {
    const el = messagesRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  const handleLogout = async () => {
    await logout();
    setUser(null);
    setSessions([]);
    setActiveSessionId(null);
    setMessages([]);
  };

  const handleSelectSession = async (sessionId) => {
    if (busy) return;
    setActiveSessionId(sessionId);
    setError("");
    try {
      const msgs = await getSessionMessages(sessionId);
      setMessages(msgs.map((m) => ({
        id: createMessageId(),
        role: m.role,
        content: m.content,
      })));
    } catch (err) {
      setMessages([]);
      setError(err.message);
    }
  };

  const handleCreateSession = async () => {
    if (busy) return;
    try {
      const session = await createSession();
      setSessions((prev) => [session, ...prev]);
      setActiveSessionId(session.id);
      setMessages([]);
      setError("");
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDeleteSession = async (sessionId) => {
    if (busy) return;
    try {
      await deleteSession(sessionId);
      const updated = sessions.filter((s) => s.id !== sessionId);
      setSessions(updated);
      if (activeSessionId === sessionId) {
        if (updated.length > 0) {
          setActiveSessionId(updated[0].id);
        } else {
          setActiveSessionId(null);
          setMessages([]);
        }
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const onStop = () => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setBusy(false);
  };

  const onSubmit = async (event, inputRef) => {
    event.preventDefault();
    const cleaned = text.trim();
    if (!cleaned || busy) return;

    // Garante que existe uma sessão ativa
    let sid = activeSessionId;
    if (!sid) {
      try {
        const session = await createSession();
        setSessions((prev) => [session, ...prev]);
        sid = session.id;
        setActiveSessionId(sid);
      } catch (err) {
        setError(err.message);
        return;
      }
    }

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
        sessionId: sid,
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

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId && !msg.content.trim()
            ? { ...msg, content: "Nao foi possivel obter resposta do modelo agora." }
            : msg
        )
      );

      // Recarrega sessões para pegar título atualizado
      const list = await listSessions();
      setSessions(list);
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

  if (checkingAuth) {
    return (
      <main className="app-shell">
        <header className="app-header">
          <div className="brand">ChatLLM Lab</div>
        </header>
        <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--muted)" }}>
          Carregando...
        </div>
      </main>
    );
  }

  if (!user) {
    return <AuthScreen onAuthSuccess={(u) => setUser(u)} />;
  }

  return (
    <main className="app-shell app-shell--with-sidebar">
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onCreateSession={handleCreateSession}
        onDeleteSession={handleDeleteSession}
      />

      <div className="app-main">
        <header className="app-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div className="brand">ChatLLM Lab</div>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ fontSize: "0.85rem", color: "var(--muted)" }}>{user.email}</span>
            <button onClick={handleLogout} style={{
              padding: "6px 14px", borderRadius: 6, border: "1px solid var(--border)",
              background: "none", color: "var(--text)", fontSize: "0.85rem",
              cursor: "pointer",
            }}>Sair</button>
          </div>
        </header>

        <section className="messages" aria-live="polite" ref={messagesRef}>
          <div className="messages-inner">
            {messages.length === 0 && (
              <div className="bubble assistant" style={{ textAlign: "center", color: "var(--muted)", padding: "40px 0" }}>
                Selecione uma sessão ou crie uma nova para começar.
              </div>
            )}
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
      </div>
    </main>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

