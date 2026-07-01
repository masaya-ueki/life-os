"""問題集ユースケース — ジャンル別一覧とフィルタ（出題済みフラグ / 正誤フラグ）。"""

from __future__ import annotations

from dataclasses import dataclass

from .ports import AttemptRepository, ContentRepository


@dataclass(frozen=True)
class QuestionBankItem:
    question_id: str
    genre_id: str
    genre_name: str
    text: str
    format: str
    answered: bool  # 出題済みフラグ
    last_correct: bool | None  # 正誤フラグ（未出題は None）


def list_bank(
    content: ContentRepository,
    attempts: AttemptRepository,
    *,
    email: str,
    certification_id: str,
    genre_id: str | None = None,
    answered: bool | None = None,
    correct: bool | None = None,
) -> list[QuestionBankItem]:
    """問題集を返す。``genre_id`` / ``answered`` / ``correct`` で絞り込む。

    - ``answered=True/False``: 出題済み/未出題で絞る（None は絞らない）。
    - ``correct=True/False``: 直近正答/誤答で絞る（None は絞らない）。未出題は correct フィルタで除外。
    """
    genre_names = {g.id: g.name for g in content.list_genres(certification_id)}

    latest: dict[str, bool] = {}
    for a in attempts.list_for(email):
        latest[a.question_id] = a.is_correct

    items: list[QuestionBankItem] = []
    for q in content.list_questions(certification_id):
        if genre_id is not None and q.genre_id != genre_id:
            continue
        is_answered = q.id in latest
        last_correct = latest.get(q.id)

        if answered is not None and is_answered != answered:
            continue
        if correct is not None and last_correct != correct:
            continue

        items.append(
            QuestionBankItem(
                question_id=q.id,
                genre_id=q.genre_id,
                genre_name=genre_names.get(q.genre_id, q.genre_id),
                text=q.text,
                format=q.format.value,
                answered=is_answered,
                last_correct=last_correct,
            )
        )
    return items
