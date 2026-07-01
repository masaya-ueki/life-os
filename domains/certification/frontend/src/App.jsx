import { useState } from "react";
import { api, setToken } from "./api.js";
import Login from "./components/Login.jsx";
import CertificationSelect from "./components/CertificationSelect.jsx";
import ModeSelect from "./components/ModeSelect.jsx";
import Quiz from "./components/Quiz.jsx";
import QuestionBank from "./components/QuestionBank.jsx";

// 画面遷移: login → certs → mode →(出題)→ quiz / (問題集)→ bank
export default function App() {
  const [view, setView] = useState("login");
  const [email, setEmail] = useState(null);
  const [cert, setCert] = useState(null); // {id, code, name}
  const [quizConfig, setQuizConfig] = useState(null); // {mode, genre_id}

  function onLoggedIn(session) {
    setToken(session.token);
    setEmail(session.email);
    setView("certs");
  }

  function logout() {
    setToken(null);
    setEmail(null);
    setCert(null);
    setView("login");
  }

  return (
    <div className="app">
      {view !== "login" && (
        <div className="topbar">
          <div className="brand">📘 資格学習</div>
          <div className="row">
            <span className="muted">{email}</span>
            <button className="btn" onClick={logout}>
              ログアウト
            </button>
          </div>
        </div>
      )}

      {view === "login" && <Login api={api} onLoggedIn={onLoggedIn} />}

      {view === "certs" && (
        <CertificationSelect
          api={api}
          onSelect={(c) => {
            setCert(c);
            setView("mode");
          }}
        />
      )}

      {view === "mode" && cert && (
        <ModeSelect
          api={api}
          cert={cert}
          onBack={() => setView("certs")}
          onStartQuiz={(config) => {
            setQuizConfig(config);
            setView("quiz");
          }}
          onOpenBank={() => setView("bank")}
        />
      )}

      {view === "quiz" && cert && quizConfig && (
        <Quiz
          api={api}
          cert={cert}
          config={quizConfig}
          onBack={() => setView("mode")}
        />
      )}

      {view === "bank" && cert && (
        <QuestionBank api={api} cert={cert} onBack={() => setView("mode")} />
      )}
    </div>
  );
}
