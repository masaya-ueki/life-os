import { useEffect, useState } from "react";

// 画面2-2: 問題集（ジャンル別・フィルタ: 出題済みフラグ / 正誤フラグ）
export default function QuestionBank({ api, cert, onBack }) {
  const [genres, setGenres] = useState([]);
  const [genreId, setGenreId] = useState("");
  const [answered, setAnswered] = useState(""); // "", "true", "false"
  const [correct, setCorrect] = useState("");
  const [items, setItems] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.genres(cert.id).then(setGenres).catch((e) => setError(e.message));
  }, [api, cert.id]);

  useEffect(() => {
    setError("");
    const params = {};
    if (genreId) params.genre_id = genreId;
    if (answered) params.answered = answered;
    if (correct) params.correct = correct;
    api
      .bank(cert.id, params)
      .then(setItems)
      .catch((e) => setError(e.message));
  }, [api, cert.id, genreId, answered, correct]);

  return (
    <div>
      <div className="crumbs">
        <button onClick={onBack}>モード選択</button> ／ {cert.name} ／ 問題集
      </div>
      <h1>問題集</h1>

      <div className="filters">
        <select value={genreId} onChange={(e) => setGenreId(e.target.value)}>
          <option value="">全ジャンル</option>
          {genres.map((g) => (
            <option key={g.id} value={g.id}>
              {g.name}
            </option>
          ))}
        </select>
        <select value={answered} onChange={(e) => setAnswered(e.target.value)}>
          <option value="">出題状況（すべて）</option>
          <option value="true">出題済み</option>
          <option value="false">未出題</option>
        </select>
        <select value={correct} onChange={(e) => setCorrect(e.target.value)}>
          <option value="">正誤（すべて）</option>
          <option value="true">正解</option>
          <option value="false">不正解</option>
        </select>
      </div>

      {error && <div className="error">{error}</div>}
      {items === null && !error && <div className="muted">読み込み中…</div>}
      {items && items.length === 0 && <div className="muted">該当する問題がありません。</div>}

      {items &&
        items.map((it) => (
          <div key={it.question_id} className="card" style={{ cursor: "default" }}>
            <div className="title">{it.text}</div>
            <div className="sub">
              {it.genre_name}
              <span className="pill">{it.format === "multiple" ? "複数選択" : "択一"}</span>
              {it.answered ? (
                <span className={`pill ${it.last_correct ? "ok" : "ng"}`}>
                  {it.last_correct ? "✓ 正解" : "✗ 不正解"}
                </span>
              ) : (
                <span className="pill">未出題</span>
              )}
            </div>
          </div>
        ))}
    </div>
  );
}
