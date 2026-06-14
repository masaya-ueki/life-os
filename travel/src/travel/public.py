"""travel の公開契約（Public API）。

★他領域が travel を参照してよい唯一の窓口（ADR-0002）。
内部（models / index）への直接 import は import-linter で禁止される。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DestinationRef:
    """他領域向けに公開する行先の最小参照（スケルトン）。"""

    id: str
    name: str


__all__ = ["DestinationRef"]
