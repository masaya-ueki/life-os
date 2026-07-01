import { useEffect, useState } from "react";

// 画面2: 取得したい資格を選択
export default function CertificationSelect({ api, onSelect }) {
  const [certs, setCerts] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .certifications()
      .then(setCerts)
      .catch((e) => setError(e.message));
  }, [api]);

  return (
    <div>
      <h1>取得したい資格を選択</h1>
      {error && <div className="error">{error}</div>}
      {certs === null && !error && <div className="muted">読み込み中…</div>}
      {certs &&
        certs.map((c) => (
          <div key={c.id} className="card" onClick={() => onSelect(c)}>
            <div className="title">{c.name}</div>
            <div className="sub">{c.code}</div>
          </div>
        ))}
      {certs && certs.length === 0 && (
        <div className="muted">資格が登録されていません。</div>
      )}
    </div>
  );
}
