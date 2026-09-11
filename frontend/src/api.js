const API_BASE = window.location.origin;

// ─── Auth ────────────────────────────────────────────────────────────────

function getToken() {
  return localStorage.getItem("access_token");
}

function setToken(token) {
  localStorage.setItem("access_token", token);
}

function clearToken() {
  localStorage.removeItem("access_token");
}

async function register(email, password) {
  const response = await fetch(`${API_BASE}/api/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const body = await response.json();
  if (!response.ok) {
    const msg = Array.isArray(body.detail) ? body.detail.map((e) => e.msg).join("; ") : body.detail || "Erro ao cadastrar.";
    throw new Error(msg);
  }
  setToken(body.access_token);
  return body;
}

async function login(email, password) {
  const response = await fetch(`${API_BASE}/api/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const body = await response.json();
  if (!response.ok) {
    const msg = Array.isArray(body.detail) ? body.detail.map((e) => e.msg).join("; ") : body.detail || "Erro ao fazer login.";
    throw new Error(msg);
  }
  setToken(body.access_token);
  return body;
}

async function logout() {
  clearToken();
  await fetch(`${API_BASE}/api/logout`, { method: "POST" }).catch(() => {});
}

async function getMe() {
  const token = getToken();
  if (!token) return null;
  const response = await fetch(`${API_BASE}/api/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    clearToken();
    return null;
  }
  return response.json();
}

// ─── Chat ────────────────────────────────────────────────────────────────

async function sendMessageStream({ message, history, sessionId, onDelta, signal }) {
  const token = getToken();
  const response = await fetch(`${API_BASE}/api/chat/stream${sessionId ? `?session_id=${sessionId}` : ""}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: JSON.stringify({ message, history }),
    signal,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body?.detail || "Erro ao enviar mensagem para o servidor.";
    throw new Error(detail);
  }

  if (!response.body) {
    throw new Error("Streaming nao suportado no ambiente atual.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() || "";

    for (const rawEvent of events) {
      const line = rawEvent
        .split("\n")
        .find((part) => part.startsWith("data:"));
      if (!line) continue;

      const payloadText = line.slice(5).trim();
      if (!payloadText) continue;

      let payload;
      try {
        payload = JSON.parse(payloadText);
      } catch {
        continue;
      }

      if (payload.error) {
        throw new Error(payload.error);
      }

      if (payload.delta) {
        onDelta(payload.delta);
      }
    }
  }
}

// ─── Sessions ────────────────────────────────────────────────────────────

async function listSessions() {
  const token = getToken();
  const response = await fetch(`${API_BASE}/api/sessions`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error("Erro ao listar sessoes.");
  return response.json();
}

async function createSession() {
  const token = getToken();
  const response = await fetch(`${API_BASE}/api/sessions`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: "{}",
  });
  if (!response.ok) throw new Error("Erro ao criar sessao.");
  return response.json();
}

async function deleteSession(sessionId) {
  const token = getToken();
  const response = await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error("Erro ao excluir sessao.");
}

async function getSessionMessages(sessionId) {
  const token = getToken();
  const response = await fetch(`${API_BASE}/api/sessions/${sessionId}/messages`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error("Erro ao carregar mensagens.");
  return response.json();
}
