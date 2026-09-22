const { useState } = React;

function Sidebar({ sessions, activeSessionId, onSelectSession, onNewSession, onDeleteSession }) {
  const [deletingId, setDeletingId] = useState(null);

  const handleDelete = async (event, sessionId) => {
    event.stopPropagation();
    if (deletingId) return;
    setDeletingId(sessionId);
    try {
      await onDeleteSession(sessionId);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <button className="new-chat-btn" onClick={onNewSession} type="button">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
            <line x1="8" y1="2" x2="8" y2="14" />
            <line x1="2" y1="8" x2="14" y2="8" />
          </svg>
          Nova conversa
        </button>
      </div>

      <div className="sidebar-list">
        {sessions.length === 0 && (
          <div className="sidebar-empty">Nenhuma conversa ainda</div>
        )}

        {sessions.map((session) => (
          <div
            key={session.id}
            className={`sidebar-item ${session.id === activeSessionId ? "active" : ""}`}
            onClick={() => onSelectSession(session.id)}
          >
            <span className="sidebar-item-title">
              {session.title || "Nova conversa"}
            </span>
            <button
              className="sidebar-delete-btn"
              onClick={(e) => handleDelete(e, session.id)}
              title="Deletar conversa"
              type="button"
            >
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" aria-hidden="true">
                <line x1="3" y1="3" x2="11" y2="11" />
                <line x1="11" y1="3" x2="3" y2="11" />
              </svg>
            </button>
          </div>
        ))}
      </div>
    </aside>
  );
}