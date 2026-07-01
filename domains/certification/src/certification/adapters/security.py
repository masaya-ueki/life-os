"""パスワードハッシュ — stdlib（hashlib.pbkdf2_hmac）のみで実装。

平文パスワードは保存・記録しない。保存形式: ``pbkdf2_sha256$<iters>$<salt_hex>$<hash_hex>``。
外部依存（passlib/bcrypt）を避け、テストイメージを軽量に保つ。
"""

from __future__ import annotations

import hashlib
import hmac
import os

_ALGO = "pbkdf2_sha256"
_ITERATIONS = 200_000


def hash_password(password: str, *, salt: bytes | None = None) -> str:
    """平文パスワードを PBKDF2-HMAC-SHA256 でハッシュ化した保存文字列を返す。"""
    if salt is None:
        salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _ITERATIONS)
    return f"{_ALGO}${_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """平文パスワードが保存ハッシュに一致するかを定数時間比較で判定する。"""
    try:
        algo, iters_s, salt_hex, hash_hex = stored.split("$")
        if algo != _ALGO:
            return False
        iterations = int(iters_s)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except (ValueError, AttributeError):
        return False
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(digest, expected)
