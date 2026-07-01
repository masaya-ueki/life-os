"""出題ドメインサービス — 選択肢シャッフルと出題選択。

要件:
- 選択肢の表示順は「時刻ミリ秒」をシードに導出する（毎回ランダム）。
- 正解が特定位置（B/D 等）に偏らないこと。ミリ秒シードの Fisher-Yates で
  正解位置は各位置に一様分布するため、偏りは生じない。
- 各モードとも 10 問ずつ出題する。
"""

from __future__ import annotations

import random

from .models import (
    PresentedQuestion,
    Question,
    QuizMode,
)

QUESTIONS_PER_QUIZ = 10


def shuffle_choices(question: Question, seed_ms: int) -> PresentedQuestion:
    """選択肢を時刻ミリ秒シードでシャッフルし、提示用の問題に変換する。

    同じ ``seed_ms`` なら決定的（テスト可能）。正解情報は含めない。
    """
    rng = random.Random(seed_ms)
    order = list(question.choices)
    rng.shuffle(order)
    return PresentedQuestion(
        id=question.id,
        genre_id=question.genre_id,
        text=question.text,
        format=question.format,
        choices=[(c.id, c.text) for c in order],
    )


def select_questions(
    pool: list[Question],
    mode: QuizMode,
    seed_ms: int,
    *,
    genre_id: str | None = None,
    wrong_question_ids: frozenset[str] | None = None,
    limit: int = QUESTIONS_PER_QUIZ,
) -> list[Question]:
    """モードに応じて出題対象を選ぶ。

    - GENRE_RANDOM: ``genre_id`` で絞り、ランダムに ``limit`` 問。
    - FULL_EXAM:    資格全体からランダムに ``limit`` 問。
    - WRONG_ONLY:   過去に間違えた問題（``wrong_question_ids``）からランダムに ``limit`` 問。

    プール数が ``limit`` 未満なら、ある分だけ返す。
    """
    if mode is QuizMode.GENRE_RANDOM:
        if genre_id is None:
            raise ValueError("GENRE_RANDOM には genre_id が必要です")
        candidates = [q for q in pool if q.genre_id == genre_id]
    elif mode is QuizMode.FULL_EXAM:
        candidates = list(pool)
    elif mode is QuizMode.WRONG_ONLY:
        wrong = wrong_question_ids or frozenset()
        candidates = [q for q in pool if q.id in wrong]
    else:  # pragma: no cover - Enum 網羅
        raise ValueError(f"未知の出題モード: {mode}")

    rng = random.Random(seed_ms)
    rng.shuffle(candidates)
    return candidates[:limit]
