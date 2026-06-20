"""task の公開契約（Public API）。

★他領域が task を参照してよい唯一の窓口。
内部（domain / application / adapters）への直接 import は import-linter で禁止される。

ここには「他領域に見せてよい最小限」だけを再公開する。
内部構造を変えても、この契約が保たれれば他領域に影響しない（ADR-0002）。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TaskSummary:
    """他領域向けに公開するタスクの最小表現（スケルトン）。"""

    id: str
    title: str
    status: str


# 例: 将来 `from task.public import TaskSummary, get_task_summary` のように使う。
__all__ = ["TaskSummary"]
