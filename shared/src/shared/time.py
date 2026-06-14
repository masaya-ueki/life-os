"""領域横断で使う日付・時刻ユーティリティ。

タイムゾーンを明示した now() を 1 箇所に集約し、各領域が直接
``datetime.now()`` を散らさないようにする。
"""

from __future__ import annotations

from datetime import datetime, timezone


def now_utc() -> datetime:
    """タイムゾーン付き（UTC）の現在時刻を返す。"""
    return datetime.now(timezone.utc)
