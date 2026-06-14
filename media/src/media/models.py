"""media のデータスキーマ（スケルトン）。

データが主役の領域。ここでは資産のメタ情報の形だけ定義する。
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Asset:
    """メディア資産のメタ情報（スケルトン）。"""

    id: str
    path: str
    tags: list[str] = field(default_factory=list)
