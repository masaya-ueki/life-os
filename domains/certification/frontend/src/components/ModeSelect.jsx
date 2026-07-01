import { useEffect, useState } from "react";

// 画面2-1 / 2-1-1: 出題開始と出題パターン（モード）の選択
export default function ModeSelect({ api, cert, onBack, onStartQuiz, onOpenBank }) {
  const [genres, setGenres] = useState([]);
  const [genreId, setGenreId] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .genres(cert.id)
      .then((g) => {
        setGenres(g);
        if (g.length) setGenreId(g[0].id);
      })
      .catch((e) => setError(e.message));
  }, [api, cert.id]);

  return (
    <div>
      <div className="crumbs">
        <button onClick={onBack}>資格選択</button> ／ {cert.name}
      </div>
      <h1>{cert.name}</h1>
      {error && <div className="error">{error}</div>}

      <h2>出題を開始（10問ずつ）</h2>

      <div className="card" style={{ cursor: "default" }}>
        <div className="title">ジャンル選択 &gt; ランダム</div>
        <div className="row" style={{ marginTop: 8 }}>
          <select
            value={genreId}
            onChange={(e) => setGenreId(e.target.value)}
            style={{ padding: "6px 10px", borderRadius: 6, border: "1px solid var(--line)" }}
          >
            {genres.map((g) => (
              <option key={g.id} value={g.id}>
                {g.name}
              </option>
            ))}
          </select>
          <button
            className="btn primary"
            disabled={!genreId}
            onClick={() => onStartQuiz({ mode: "genre_random", genre_id: genreId })}
          >
            開始
          </button>
        </div>
      </div>

      <div className="card" onClick={() => onStartQuiz({ mode: "full_exam" })}>
        <div className="title">全体試験</div>
        <div className="sub">資格全体からランダムに10問</div>
      </div>

      <div className="card" onClick={() => onStartQuiz({ mode: "wrong_only" })}>
        <div className="title">間違えた問題のみ</div>
        <div className="sub">直近で誤答した問題から10問</div>
      </div>

      <h2>問題集</h2>
      <div className="card" onClick={onOpenBank}>
        <div className="title">問題集を見る</div>
        <div className="sub">ジャンル別・出題済み/正誤でフィルタ</div>
      </div>
    </div>
  );
}
