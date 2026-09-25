function Sidebar({ sessions, activeSessionKey, onSelectSession, onNewSession, onDeleteSession, onToggle, isOpen }) {
  const [loading, setLoading] = useState(false);

  const handleNew = async () => {
    setLoading(true);
    try {
      await onNewSession();
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = (e, sessionKey) => {
    e.stopPropagation();
    if (window.confirm("Deletar esta conversa?")) {
      onDeleteSession(sessionKey);
    }
  };

  return (
    <aside className={`sidebar ${isOpen ? "open" : "closed"}`}>
      <div className="sidebar-header">
        <button className="sidebar-toggle" onClick={onToggle} type="button" title="Fechar sidebar">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="15 18 9 12 15 6" />
          </svg>
        </button>
        <button className="sidebar-brand" onClick={handleNew} disabled={loading} type="button" title="Novo chat">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          <span>Novo chat</span>
        </button>
      </div>

      <nav className="session-list">
        {sessions.length === 0 && (
          <div className="session-empty">Nenhuma conversa ainda</div>
        )}
        {sessions.map((session) => (
          <div
            key={session.session_key}
            className={`session-item ${session.session_key === activeSessionKey ? "active" : ""}`}
            onClick={() => onSelectSession(session.session_key)}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => { if (e.key === "Enter") onSelectSession(session.session_key); }}
          >
            <span className="session-title" title={session.title || "Nova conversa"}>
              {session.title || "Nova conversa"}
            </span>
            <button
              className="session-delete"
              onClick={(e) => handleDelete(e, session.session_key)}
              type="button"
              title="Deletar conversa"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="3 6 5 6 21 6" />
                <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
              </svg>
            </button>
          </div>
        ))}
      </nav>
    </aside>
  );
}