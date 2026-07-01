"""FastAPI HTTP アダプタ — フロント（React）向けの REST API。

オプション依存 ``api``（fastapi / uvicorn）が必要:
    uv run --extra api uvicorn certification.adapters.api:app --reload

ドメイン/アプリ層のユースケースを HTTP に接続するだけの薄い層に保つ。
"""

from __future__ import annotations

import secrets
import time

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..application import question_bank, quiz_service
from ..application.auth import AuthError, authenticate
from ..application.quiz_service import QuizError
from ..domain.models import QuizMode
from .repository import (
    EnvUserRepository,
    InMemoryAttemptRepository,
    JsonContentRepository,
)

app = FastAPI(title="certification 資格学習 API")

# ローカル開発では Vite(5173) から呼ぶため CORS を許可。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 単一プロセス内の依存（MVP）。P5 で DynamoDB 実装へ差し替える。
_content = JsonContentRepository()
_attempts = InMemoryAttemptRepository()
_users = EnvUserRepository()
_sessions: dict[str, str] = {}  # token -> email


def now_ms() -> int:
    return int(time.time() * 1000)


def current_email(authorization: str = Header(default="")) -> str:
    """Bearer トークンからログイン中メールを解決する。"""
    token = authorization.removeprefix("Bearer ").strip()
    email = _sessions.get(token)
    if not email:
        raise HTTPException(status_code=401, detail="未認証です")
    return email


# ---- スキーマ -------------------------------------------------------------


class LoginRequest(BaseModel):
    email: str
    password: str


class StartQuizRequest(BaseModel):
    certification_id: str
    mode: QuizMode
    genre_id: str | None = None


class GradeRequest(BaseModel):
    question_id: str
    selected_choice_ids: list[str]


# ---- エンドポイント -------------------------------------------------------


@app.post("/api/login")
def login(req: LoginRequest) -> dict:
    try:
        user = authenticate(_users, req.email, req.password)
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e)) from e
    token = secrets.token_urlsafe(24)
    _sessions[token] = user.email
    return {"token": token, "email": user.email}


@app.get("/api/certifications")
def list_certifications(_: str = Depends(current_email)) -> list[dict]:
    return [
        {"id": c.id, "code": c.code, "name": c.name}
        for c in _content.list_certifications()
    ]


@app.get("/api/certifications/{certification_id}/genres")
def list_genres(
    certification_id: str, _: str = Depends(current_email)
) -> list[dict]:
    return [
        {"id": g.id, "name": g.name}
        for g in _content.list_genres(certification_id)
    ]


@app.post("/api/quiz/start")
def start_quiz(
    req: StartQuizRequest, email: str = Depends(current_email)
) -> dict:
    try:
        result = quiz_service.start_quiz(
            _content,
            _attempts,
            email=email,
            certification_id=req.certification_id,
            mode=req.mode,
            seed_ms=now_ms(),
            genre_id=req.genre_id,
        )
    except QuizError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {
        "mode": result.mode.value,
        "questions": [
            {
                "id": q.id,
                "genre_id": q.genre_id,
                "text": q.text,
                "format": q.format.value,
                "choices": [{"id": cid, "text": text} for cid, text in q.choices],
            }
            for q in result.questions
        ],
    }


@app.post("/api/quiz/grade")
def grade(req: GradeRequest, email: str = Depends(current_email)) -> dict:
    try:
        result = quiz_service.grade_answer(
            _content,
            _attempts,
            email=email,
            question_id=req.question_id,
            selected_choice_ids=req.selected_choice_ids,
            answered_at_ms=now_ms(),
        )
    except QuizError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return {
        "question_id": result.question_id,
        "is_correct": result.is_correct,
        "correct_choice_ids": sorted(result.correct_choice_ids),
        "selected_choice_ids": sorted(result.selected_choice_ids),
        "source_url": result.source_url,
        "explanation": result.explanation,
        "feedback": [
            {
                "choice_id": f.choice_id,
                "text": f.text,
                "is_correct": f.is_correct,
                "selected": f.selected,
                "ng_reason": f.ng_reason,
            }
            for f in result.feedback
        ],
    }


@app.get("/api/certifications/{certification_id}/bank")
def bank(
    certification_id: str,
    genre_id: str | None = None,
    answered: bool | None = None,
    correct: bool | None = None,
    email: str = Depends(current_email),
) -> list[dict]:
    items = question_bank.list_bank(
        _content,
        _attempts,
        email=email,
        certification_id=certification_id,
        genre_id=genre_id,
        answered=answered,
        correct=correct,
    )
    return [
        {
            "question_id": it.question_id,
            "genre_id": it.genre_id,
            "genre_name": it.genre_name,
            "text": it.text,
            "format": it.format,
            "answered": it.answered,
            "last_correct": it.last_correct,
        }
        for it in items
    ]
