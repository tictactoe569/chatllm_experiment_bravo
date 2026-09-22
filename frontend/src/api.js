const API_BASE = window.location.origin;

// ── Chat ────────────────────────────────────────────────────────────────────

async function sendMessageStream({ message, history, sessionId, onDelta, signal }) {
  const response = await fetch(`${API_BASE}/api/chat/stream`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
    body: JSON.stringify({ message, history, session_id: sessionId }),
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

// ── Auth ────────────────────────────────────────────────────────────────────

function getAuthHeaders() {
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function registerUser(email, password) {
  const response = await fetch(`${API_BASE}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(extractError(data));
  return data;
}

async function loginUser(email, password) {
  const response = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(extractError(data));
  return data;
}

async function logoutUser() {
  const response = await fetch(`${API_BASE}/api/auth/logout`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(extractError(data));
  }
}

function extractError(data) {
  // FastAPI validation errors: detail is an array of {msg, loc, type}
  if (Array.isArray(data?.detail)) {
    return data.detail.map((e) => translateError(e.msg)).join("; ");
  }
  // Normal string detail
  if (typeof data?.detail === "string") return data.detail;
  // Fallback
  return "Erro inesperado";
}

// Função responsável por traduzir mensagens de erro de inglês para português
function translateError(msg) {
  const map = {
    "String should have at least 6 characters": "A senha deve ter no mínimo 6 caracteres",
    "String should have at least 1 characters": "A senha deve ter no mínimo 1 caractere",
    "String should have at least": "deve ter no mínimo",
    "String should have at most": "excede o limite de",
    "Value error, String should have at least": "deve ter no mínimo",
    "value_error.any_str.min_length": "deve ter no mínimo",
    "value_error.any_str.max_length": "excede o limite de",
    "value_error.string.pattern_mismatch": "Formato inválido",
  };
  // Try exact match first, then partial
  for (const [en, pt] of Object.entries(map)) {
    if (msg.includes(en)) return msg.replace(en, pt);
  }
  // Generic cleanup: replace remaining English words
  msg = msg.replace(/\bcharacters\b/g, "caracteres");
  msg = msg.replace(/\bString\b/g, "Campo");
  return msg;
}

async function fetchUser() {
  const response = await fetch(`${API_BASE}/api/auth/me`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) return null;
  return response.json();
}

// ── Sessions ────────────────────────────────────────────────────────────────

async function listSessions() {
  const response = await fetch(`${API_BASE}/api/sessions`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) return [];
  return response.json();
}

async function createSession() {
  const response = await fetch(`${API_BASE}/api/sessions`, {
    method: "POST",
    headers: { ...getAuthHeaders(), "Content-Type": "application/json" },
  });
  const data = await response.json();
  if (!response.ok) throw new Error(extractError(data));
  return data;
}

async function deleteSession(sessionId) {
  const response = await fetch(`${API_BASE}/api/sessions/${sessionId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(extractError(data));
  }
}

async function fetchSessionMessages(sessionId) {
  const response = await fetch(`${API_BASE}/api/sessions/${sessionId}/messages`, {
    headers: getAuthHeaders(),
  });
  if (!response.ok) return [];
  return response.json();
}
