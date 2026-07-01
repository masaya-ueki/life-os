"""出題・採点ユースケース。

- ``start_quiz``: モード（ジャンルランダム / 全体 / 間違いのみ）で 10 問を選び、
  選択肢を時刻ミリ秒シードでシャッフルして提示する。
- ``grade_answer``: 1 問を採点し、履歴に記録して結果（✓/✗・NG理由・出題元）を返す。
"""

from __future__ import annotations

from dataclasses import dataclass

from ..domain import quiz, scoring
from ..domain.models import (
    AttemptRecord,
    GradedAnswer,
    PresentedQuestion,
    QuizMode,
)
from .ports import AttemptRepository, ContentRepository


class QuizError(Exception):
    """出題・採点にまつわる業務エラー。"""


@dataclass(frozen=True)
class QuizStart:
    mode: QuizMode
    questions: list[PresentedQuestion]


def _wrong_question_ids(attempts: AttemptRepository, email: str) -> frozenset[str]:
    """直近の正誤で「最後に間違えたまま」の問題 ID 集合を求める。"""
    latest: dict[str, bool] = {}
    for a in attempts.list_for(email):
        latest[a.question_id] = a.is_correct
    return frozenset(qid for qid, ok in latest.items() if not ok)


def start_quiz(
    content: ContentRepository,
    attempts: AttemptRepository,
    *,
    email: str,
    certification_id: str,
    mode: QuizMode,
    seed_ms: int,
    genre_id: str | None = None,
) -> QuizStart:
    """出題を開始する。選択肢は seed_ms（時刻ミリ秒）でシャッフルする。"""
    pool = content.list_questions(certification_id)
    if not pool:
        raise QuizError("この資格には問題が登録されていません")

    selected = quiz.select_questions(
        pool,
        mode,
        seed_ms,
        genre_id=genre_id,
        wrong_question_ids=_wrong_question_ids(attempts, email),
    )
    if not selected:
        raise QuizError("出題できる問題がありません（条件に合致する問題が0件）")

    # 各問の選択肢シャッフルは、問題ごとに seed をずらして相関を避ける。
    presented = [
        quiz.shuffle_choices(q, seed_ms + i) for i, q in enumerate(selected)
    ]
    return QuizStart(mode=mode, questions=presented)


def grade_answer(
    content: ContentRepository,
    attempts: AttemptRepository,
    *,
    email: str,
    question_id: str,
    selected_choice_ids: list[str],
    answered_at_ms: int,
) -> GradedAnswer:
    """1 問を採点し、出題履歴に記録して結果を返す。"""
    question = content.get_question(question_id)
    if question is None:
        raise QuizError(f"問題が見つかりません: {question_id}")

    result = scoring.grade(question, selected_choice_ids)
    attempts.record(
        AttemptRecord(
            email=email,
            question_id=question_id,
            is_correct=result.is_correct,
            answered_at_ms=answered_at_ms,
        )
    )
    return result
