"""english のデータスキーマ（スケルトン）。

学習ログ（``data/vocabulary.md`` ・ ``data/expressions.md``）の各行に対応する。
Markdown テーブルが保存兼一覧の単一の真実だが、列の意味はここを定義源とする。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

#: 語彙エントリの種別（単語 / イディオム）。
VocabularyKind = Literal["word", "idiom"]


@dataclass
class VocabularyEntry:
    """単語・イディオム1件（``data/vocabulary.md`` の1行）。"""

    term: str
    meaning: str
    example: str
    kind: VocabularyKind = "word"


@dataclass
class ExpressionEntry:
    """重要な表現1件（``data/expressions.md`` の1行）。"""

    expression: str
    meaning: str
    example: str
