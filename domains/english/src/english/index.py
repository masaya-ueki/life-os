"""english の整形・検索・自動化（スケルトン）。"""

from __future__ import annotations

from english.models import ExpressionEntry, VocabularyEntry


def search_vocabulary(
    entries: list[VocabularyEntry], keyword: str
) -> list[VocabularyEntry]:
    """``term`` または ``meaning`` に ``keyword`` を含む語彙を返す（スケルトン）。"""
    needle = keyword.lower()
    return [e for e in entries if needle in e.term.lower() or needle in e.meaning.lower()]


def search_expressions(
    entries: list[ExpressionEntry], keyword: str
) -> list[ExpressionEntry]:
    """``expression`` または ``meaning`` に ``keyword`` を含む表現を返す（スケルトン）。"""
    needle = keyword.lower()
    return [
        e
        for e in entries
        if needle in e.expression.lower() or needle in e.meaning.lower()
    ]
