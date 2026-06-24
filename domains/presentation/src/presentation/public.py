"""presentation の公開契約（Public API）。

★他領域が presentation を参照してよい唯一の窓口（ADR-0002）。
内部（models / index）への直接 import は import-linter で禁止される。
"""

from __future__ import annotations

__all__: list[str] = []
