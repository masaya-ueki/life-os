import { useState } from "react";

// 画面1: ログイン（メールアドレス + パスワード）
export default function Login({ api, onLoggedIn }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const session = await api.login(email, password);
      onLoggedIn(session);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div style={{ maxWidth: 380, margin: "56px auto 0" }}>
      <div className="brand" style={{ fontSize: 22, marginBottom: 4 }}>
        📘 資格学習
      </div>
      <h1 style={{ fontSize: 20 }}>ログイン</h1>
      <form onSubmit={submit}>
        <div className="field">
          <label>メールアドレス</label>
          <input
            type="email"
            value={email}
            autoComplete="username"
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
          />
        </div>
        <div className="field">
          <label>パスワード</label>
          <input
            type="password"
            value={password}
            autoComplete="current-password"
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        {error && <div className="error">{error}</div>}
        <button className="btn primary" type="submit" disabled={busy}>
          {busy ? "認証中…" : "ログイン"}
        </button>
      </form>
    </div>
  );
}
