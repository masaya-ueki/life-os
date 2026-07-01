"""リポジトリ実装 — JSON ファイル（問題）＋ インメモリ（出題履歴）＋ 単一ユーザー。

- 問題/ジャンル/資格: ``data/*.json`` から読み込む（読み取り専用）。
- 出題履歴: プロセス内メモリに保持（MVP）。P5 で DynamoDB 実装に差し替える。
- ユーザー: 環境変数から単一ユーザーを構成する（平文パスワードは扱わない）。

環境変数:
- ``CERT_USER_EMAIL``          … ログインメールアドレス
- ``CERT_USER_PASSWORD_HASH``  … security.hash_password が生成した保存ハッシュ
- ``CERT_USER_PASSWORD``       … （開発用）平文。指定時は起動時にハッシュ化する。
                                  本番では PASSWORD_HASH を使い、平文は渡さないこと。
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from ..domain.models import (
    AttemptRecord,
    Certification,
    Choice,
    Genre,
    Question,
    QuestionFormat,
    User,
)
from . import security

# data/ の既定パス（このファイルからの相対）。
_DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data"


class JsonContentRepository:
    """``data/`` 配下の JSON から資格・ジャンル・問題を読み込む ContentRepository。"""

    def __init__(self, data_dir: Path | None = None) -> None:
        # 明示指定 > 環境変数 CERT_DATA_DIR（Lambda 等の配置用） > 既定（リポジトリの data/）
        if data_dir is None:
            env_dir = os.environ.get("CERT_DATA_DIR")
            data_dir = Path(env_dir) if env_dir else _DEFAULT_DATA_DIR
        self._data_dir = data_dir
        self._certifications: list[Certification] = []
        self._genres: list[Genre] = []
        self._questions: list[Question] = []
        self._load()

    def _load(self) -> None:
        for path in sorted(self._data_dir.glob("*.json")):
            raw = json.loads(path.read_text(encoding="utf-8"))
            cert = raw["certification"]
            self._certifications.append(
                Certification(id=cert["id"], code=cert["code"], name=cert["name"])
            )
            for g in raw.get("genres", []):
                self._genres.append(
                    Genre(id=g["id"], certification_id=cert["id"], name=g["name"])
                )
            for q in raw.get("questions", []):
                self._questions.append(
                    Question(
                        id=q["id"],
                        certification_id=cert["id"],
                        genre_id=q["genre_id"],
                        text=q["text"],
                        format=QuestionFormat(q["format"]),
                        choices=tuple(
                            Choice(
                                id=c["id"],
                                text=c["text"],
                                is_correct=c["is_correct"],
                                ng_reason=c.get("ng_reason", ""),
                            )
                            for c in q["choices"]
                        ),
                        source_url=q.get("source_url", ""),
                        explanation=q.get("explanation", ""),
                    )
                )

    def list_certifications(self) -> list[Certification]:
        return list(self._certifications)

    def list_genres(self, certification_id: str) -> list[Genre]:
        return [g for g in self._genres if g.certification_id == certification_id]

    def list_questions(self, certification_id: str) -> list[Question]:
        return [q for q in self._questions if q.certification_id == certification_id]

    def get_question(self, question_id: str) -> Question | None:
        return next((q for q in self._questions if q.id == question_id), None)


class InMemoryAttemptRepository:
    """出題履歴をプロセス内に保持する AttemptRepository（MVP 用）。"""

    def __init__(self) -> None:
        self._attempts: list[AttemptRecord] = []

    def record(self, attempt: AttemptRecord) -> None:
        self._attempts.append(attempt)

    def list_for(self, email: str) -> list[AttemptRecord]:
        return [a for a in self._attempts if a.email == email]


class EnvUserRepository:
    """環境変数から単一ユーザーを構成する UserRepository。"""

    def __init__(self, env: dict[str, str] | None = None) -> None:
        source = env if env is not None else dict(os.environ)
        self._user = self._build(source)

    @staticmethod
    def _build(env: dict[str, str]) -> User | None:
        email = env.get("CERT_USER_EMAIL")
        if not email:
            return None
        password_hash = env.get("CERT_USER_PASSWORD_HASH")
        if not password_hash:
            plaintext = env.get("CERT_USER_PASSWORD")
            if not plaintext:
                return None
            password_hash = security.hash_password(plaintext)
        return User(email=email, password_hash=password_hash)

    def find_user(self, email: str) -> User | None:
        if self._user is not None and self._user.email == email:
            return self._user
        return None
