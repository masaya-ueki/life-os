"""task アプリケーション層 — ユースケース（サービス）。

ドメインを組み合わせて 1 つの操作を実現する。永続化は adapters の
リポジトリ実装に委譲する（ここでは抽象に依存する）。
"""

from __future__ import annotations

from task.domain import Task


def create_task(title: str) -> Task:
    """タスクを作成するユースケース（スケルトン）。"""
    return Task.create(title)
