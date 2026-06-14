"""content_sales の公開契約（Public API）。

★他領域が content_sales を参照してよい唯一の窓口（ADR-0002）。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProductSummary:
    """他領域向けに公開する販売物の最小表現（スケルトン）。"""

    id: str
    name: str


__all__ = ["ProductSummary"]
