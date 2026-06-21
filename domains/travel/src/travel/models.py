"""travel のデータスキーマ（スケルトン）。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Destination:
    """行きたい/行った場所（スケルトン）。"""

    id: str
    name: str
    visited: bool = False
