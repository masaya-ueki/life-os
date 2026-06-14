"""media の公開契約（Public API）。

★他領域が media を参照してよい唯一の窓口（ADR-0002）。
内部（models / index）への直接 import は import-linter で禁止される。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AssetRef:
    """他領域向けに公開するメディア資産の最小参照（スケルトン）。"""

    id: str
    path: str


__all__ = ["AssetRef"]
