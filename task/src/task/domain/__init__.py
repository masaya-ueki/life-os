"""task ドメイン層 — Entity / 値オブジェクト / 集約 + 純粋ロジック。

外部 I/O を持たない。永続化や CLI は adapters 層に置く。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import NewType

from shared.ids import new_id

TaskId = NewType("TaskId", str)


class Status(str, Enum):
    TODO = "todo"
    DOING = "doing"
    DONE = "done"


@dataclass
class Task:
    """タスク集約（スケルトン）。"""

    id: TaskId
    title: str
    status: Status = Status.TODO

    @classmethod
    def create(cls, title: str) -> "Task":
        return cls(id=TaskId(new_id()), title=title, status=Status.TODO)

    def complete(self) -> None:
        self.status = Status.DONE
