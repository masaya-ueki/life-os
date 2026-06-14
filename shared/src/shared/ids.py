"""領域横断で使う ID 型の基盤。

各領域は自分の ID 型をここの ``new_id`` で生成してよいが、
ID の「意味」は各領域側（例: TaskId）で型を付けて表現する。
"""

from __future__ import annotations

import uuid
from typing import NewType

# 不透明な ID 文字列。領域側で NewType を被せて意味を与える。
Id = NewType("Id", str)


def new_id() -> Id:
    """新しい一意な ID を生成する。"""
    return Id(uuid.uuid4().hex)
