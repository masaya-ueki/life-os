import { useEffect, useState } from "react";

// 画面2-1-1: 出題・回答・正誤判定（✓/✗・各選択肢のNG理由・出題元リンク）
export default function Quiz({ api, cert, config, onBack }) {
  const [questions, setQuestions] = useState(null);
  const [idx, setIdx] = useState(0);
  const [selected, setSelected] = useState([]); // choice ids
  const [graded, setGraded] = useState(null); // 採点結果
  const [error, setError] = useState("");
  const [score, setScore] = useState(0);

  useEffect(() => {
    setError("");
    api
      .startQuiz({ certification_id: cert.id, mode: config.mode, genre_id: config.genre_id || null })
      .then((res) => setQuestions(res.questions))
      .catch((e) => setError(e.message));
  }, [api, cert.id, config]);

  if (error)
    return (
      <div>
        <div className="crumbs">
          <button onClick={onBack}>戻る</button>
        </div>
        <div className="error">{error}</div>
      </div>
    );

  if (questions === null) return <div className="muted">出題を準備中…</div>;
  if (questions.length === 0) return <div className="muted">出題できる問題がありません。</div>;

  // 全問終了
  if (idx >= questions.length) {
    return (
      <div>
        <h1>結果</h1>
        <p className="verdict ok">
          {questions.length} 問中 {score} 問正解
        </p>
        <button className="btn primary" onClick={onBack}>
          モード選択へ戻る
        </button>
      </div>
    );
  }

  const q = questions[idx];
  const isMultiple = q.format === "multiple";

  function toggle(cid) {
    if (graded) return;
    if (isMultiple) {
      setSelected((s) => (s.includes(cid) ? s.filter((x) => x !== cid) : [...s, cid]));
    } else {
      setSelected([cid]);
    }
  }

  async function submit() {
    setError("");
    try {
      const result = await api.grade({ question_id: q.id, selected_choice_ids: selected });
      setGraded(result);
      if (result.is_correct) setScore((s) => s + 1);
    } catch (e) {
      setError(e.message);
    }
  }

  function next() {
    setGraded(null);
    setSelected([]);
    setIdx((i) => i + 1);
  }

  // 採点後の選択肢クラス
  function choiceClass(cid) {
    if (!graded) return selected.includes(cid) ? "choice selected" : "choice";
    const fb = graded.feedback.find((f) => f.choice_id === cid);
    if (fb && fb.is_correct) return "choice correct";
    if (fb && fb.selected && !fb.is_correct) return "choice wrong";
    return "choice";
  }

  return (
    <div>
      <div className="crumbs">
        <button onClick={onBack}>モード選択</button> ／ {cert.name}
      </div>
      <div className="muted" style={{ marginBottom: 8 }}>
        第 {idx + 1} / {questions.length} 問　{isMultiple ? "（複数選択）" : "（択一）"}
      </div>
      <h1 style={{ fontSize: 20 }}>{q.text}</h1>

      {q.choices.map((c) => {
        const fb = graded && graded.feedback.find((f) => f.choice_id === c.id);
        return (
          <div key={c.id} className={choiceClass(c.id)} onClick={() => toggle(c.id)}>
            <span className="mark">
              {graded ? (fb.is_correct ? "✓" : fb.selected ? "✗" : "・") : selected.includes(c.id) ? "●" : "○"}
            </span>
            <span>
              {c.text}
              {graded && fb.ng_reason && <div className="ng">NG理由: {fb.ng_reason}</div>}
            </span>
          </div>
        );
      })}

      {error && <div className="error">{error}</div>}

      {!graded ? (
        <button className="btn primary" disabled={selected.length === 0} onClick={submit}>
          回答する
        </button>
      ) : (
        <div>
          <p className={`verdict ${graded.is_correct ? "ok" : "ng"}`}>
            {graded.is_correct ? "✓ 正解" : "✗ 不正解"}
          </p>
          {graded.explanation && <p className="muted">{graded.explanation}</p>}
          {graded.source_url && (
            <p>
              出題元:{" "}
              <a href={graded.source_url} target="_blank" rel="noreferrer">
                {graded.source_url}
              </a>
            </p>
          )}
          <button className="btn primary" onClick={next}>
            {idx + 1 < questions.length ? "次の問題へ" : "結果を見る"}
          </button>
        </div>
      )}
    </div>
  );
}
