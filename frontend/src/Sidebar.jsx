const { useState } = React;

function Sidebar({ sessions, activeSessionId, onSelectSession, onCreateSession, onDeleteSession }) {
  const [collapsed, setCollapsed] = useState(false);

  if (collapsed) {
    return (
      <div className="sidebar sidebar--collapsed">
        <button className="sidebar-toggle" onClick={() => setCollapsed(false)} title="Expandir sidebar">
          ☰
        </button>
      </div>
    );
  }

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <span className="sidebar-title">Sessões</span>
        <button className="sidebar-toggle" onClick={() => setCollapsed(true)} title="Recolher sidebar">
          ◀
        </button>
      </div>

      <button className="sidebar-new-btn" onClick={onCreateSession}>
        + Nova sessão
      </button>

      <div className="sidebar-list">
        {sessions.map((s) => (
          <div
            key={s.id}
            className={`sidebar-item ${s.id === activeSessionId ? "sidebar-item--active" : ""}`}
            onClick={() => onSelectSession(s.id)}
          >
            <span className="sidebar-item-title">
              {s.title || "Nova sessão"}
            </span>
            <button
              className="sidebar-item-delete"
              onClick={(e) => { e.stopPropagation(); onDeleteSession(s.id); }}
              title="Excluir sessão"
            >
              ✕
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}