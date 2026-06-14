"""travel の整形・検索・自動化（スケルトン）。"""

from __future__ import annotations

from travel.models import Destination


def wishlist(destinations: list[Destination]) -> list[Destination]:
    """未訪問の行先（行きたいリスト）を返す（スケルトン）。"""
    return [d for d in destinations if not d.visited]
