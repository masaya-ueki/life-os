"""認証ユースケース — 単一ユーザーのメール+パスワード認証。"""

from __future__ import annotations

from ..adapters import security
from ..domain.models import User
from .ports import UserRepository


class AuthError(Exception):
    """認証失敗。"""


def authenticate(users: UserRepository, email: str, password: str) -> User:
    """メール+パスワードで認証する。失敗時は AuthError。

    ユーザー不在でもパスワード検証を通し、応答時間差による列挙を避ける。
    """
    user = users.find_user(email)
    # ダミーハッシュ（存在しないメールでも比較コストを一定に保つ）。
    stored = user.password_hash if user else security.hash_password("__no_user__")
    if not security.verify_password(password, stored) or user is None:
        raise AuthError("メールアドレスまたはパスワードが正しくありません")
    return user
