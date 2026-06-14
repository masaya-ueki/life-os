"""media の整形・検索・自動化（スケルトン）。

data/ のメタデータを読み込み、索引付け・検索する処理を置く。
"""

from __future__ import annotations

from media.models import Asset


def find_by_tag(assets: list[Asset], tag: str) -> list[Asset]:
    """タグでメディア資産を絞り込む（スケルトン）。"""
    return [a for a in assets if tag in a.tags]
