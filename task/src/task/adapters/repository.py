"""task の永続化アダプタ — data/ への読み書き（スケルトン）。

ドメインは永続化の詳細を知らない。ここで JSON/ファイル等の具体を扱う。
"""

from __future__ import annotations

from task.domain import Task


class TaskRepository:
    """タスクの保存・取得（スケルトン）。"""

    def save(self, task: Task) -> None:
        raise NotImplementedError

    def get(self, task_id: str) -> Task | None:
        raise NotImplementedError
