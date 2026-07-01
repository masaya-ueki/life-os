"""ドメインモデル — 資格学習の中心概念（エンティティ・値オブジェクト）。

外部ライブラリに依存しない純粋な dataclass / Enum のみで表現する。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class QuestionFormat(str, Enum):
    """出題形式区分。"""

    SINGLE = "single"  # 4択の択一（正解1つ）
    MULTIPLE = "multiple"  # 4択の複数選択（正解1つ以上）


class QuizMode(str, Enum):
    """出題モード。いずれも 10 問ずつ出題する。"""

    GENRE_RANDOM = "genre_random"  # ジャンル選択 > ランダム
    FULL_EXAM = "full_exam"  # 全体試験
    WRONG_ONLY = "wrong_only"  # 間違えた問題のみ


@dataclass(frozen=True)
class Choice:
    """選択肢。正解可否と、誤答の場合の NG 理由を持つ。"""

    id: str
    text: str
    is_correct: bool
    # なぜこの選択肢が不正解なのか（正解選択肢では正解の根拠を書いてよい）。
    ng_reason: str = ""


@dataclass(frozen=True)
class Question:
    """1 問。選択肢・出題形式・出題元リンクを持つ。"""

    id: str
    certification_id: str
    genre_id: str
    text: str
    format: QuestionFormat
    choices: tuple[Choice, ...]
    # 出題元のドキュメントリンク（正誤表示時に提示する）。
    source_url: str = ""
    # 解説（任意）。
    explanation: str = ""

    @property
    def correct_choice_ids(self) -> frozenset[str]:
        return frozenset(c.id for c in self.choices if c.is_correct)


@dataclass(frozen=True)
class Genre:
    """資格内のジャンル。"""

    id: str
    certification_id: str
    name: str


@dataclass(frozen=True)
class Certification:
    """資格。初期コンテンツは Snowflake SnowPro Core を想定。"""

    id: str
    code: str
    name: str


@dataclass(frozen=True)
class User:
    """利用者（本人1名前提）。パスワードはハッシュのみを保持し、平文は扱わない。"""

    email: str
    password_hash: str


@dataclass(frozen=True)
class ChoiceFeedback:
    """採点結果における選択肢ごとのフィードバック。"""

    choice_id: str
    text: str
    is_correct: bool
    selected: bool
    ng_reason: str


@dataclass(frozen=True)
class GradedAnswer:
    """1 問の採点結果。✓/✗、各選択肢の NG 理由、出題元リンクを含む。"""

    question_id: str
    is_correct: bool  # ✓ / ✗
    correct_choice_ids: frozenset[str]
    selected_choice_ids: frozenset[str]
    feedback: tuple[ChoiceFeedback, ...]
    source_url: str
    explanation: str


@dataclass(frozen=True)
class AttemptRecord:
    """出題履歴の 1 レコード（出題済み・正誤フラグの根拠）。"""

    email: str
    question_id: str
    is_correct: bool
    answered_at_ms: int


@dataclass
class PresentedQuestion:
    """利用者に提示する 1 問（選択肢はシャッフル済み・正解情報は含めない）。"""

    id: str
    genre_id: str
    text: str
    format: QuestionFormat
    # (choice_id, text) の表示順（シャッフル済み）。正解可否は伏せる。
    choices: list[tuple[str, str]] = field(default_factory=list)
