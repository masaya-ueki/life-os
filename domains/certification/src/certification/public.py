"""certification の公開契約（Public API）。

★他領域が certification を参照してよい唯一の窓口（ADR-0002）。
内部（domain / application / adapters）への直接 import は import-linter で禁止される。

現状は他領域連携の予定がないため、最小の資格サマリのみ公開する。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CertificationSummary:
    """他領域向けに公開する資格の最小表現。"""

    id: str
    code: str
    name: str


__all__ = ["CertificationSummary"]
