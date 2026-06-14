"""領域横断で使う戻り値・エラーの基盤型。

ドメイン固有の成功/失敗の中身は各領域で定義する。ここは器だけ。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


class DomainError(Exception):
    """各領域のドメインエラーの基底。領域側で継承して使う。"""


@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T


@dataclass(frozen=True)
class Err:
    error: DomainError


# 成功 or 失敗を表す軽量な Result。例外で表現してもよいが、
# 期待される失敗（バリデーション等）は Result で返すと扱いやすい。
Result = Ok[T] | Err
