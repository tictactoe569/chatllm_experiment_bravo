const { useState } = React;

function Auth({ onAuthSuccess }) {
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    const cleanedEmail = email.trim();
    const cleanedPassword = password.trim();
    if (!cleanedEmail || !cleanedPassword || busy) return;

    setError("");
    setBusy(true);

    try {
      let data;
      if (mode === "register") {
        data = await registerUser(cleanedEmail, cleanedPassword);
      } else {
        data = await loginUser(cleanedEmail, cleanedPassword);
      }
      localStorage.setItem("access_token", data.access_token);
      onAuthSuccess();
    } catch (err) {
      setError(err.message || "Erro inesperado");
    } finally {
      setBusy(false);
    }
  };

  const toggleMode = () => {
    setMode((prev) => (prev === "login" ? "register" : "login"));
    setError("");
  };

  return (
    <main className="auth-shell">
      <div className="auth-card">
        <h1 className="auth-title">ChatLLM Lab</h1>
        <h2 className="auth-subtitle">
          {mode === "login" ? "Entrar" : "Criar conta"}
        </h2>

        {error && <div className="auth-error">{error}</div>}

        <form className="auth-form" onSubmit={handleSubmit}>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="Seu email"
            maxLength={255}
            disabled={busy}
            autoFocus
            required
          />
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Sua senha"
            maxLength={128}
            disabled={busy}
            required
          />
          {mode === "register" && (
            <div className="auth-hint">Mínimo de 6 caracteres (*)</div>
          )}
          <button type="submit" disabled={busy || !email.trim() || !password.trim()}>
            {busy ? "Aguarde..." : mode === "login" ? "Entrar" : "Cadastrar"}
          </button>
        </form>

        <p className="auth-toggle">
          {mode === "login" ? (
            <>
              Não tem conta?{" "}
              <button className="link-btn" onClick={toggleMode} type="button">
                Cadastre-se
              </button>
            </>
          ) : (
            <>
              Já tem conta?{" "}
              <button className="link-btn" onClick={toggleMode} type="button">
                Fazer login
              </button>
            </>
          )}
        </p>
      </div>
    </main>
  );
}