"""ポート（抽象インターフェース）— アプリ層が依存する外部境界。

具体実装は adapters 層に置く（file / in-memory は adapters.repository、
将来の DynamoDB もここを満たす）。依存方向を internal → 抽象に保つ（DDD）。
"""

from __future__ import annotations

from typing import Protocol

from ..domain.models import (
    AttemptRecord,
    Certification,
    Genre,
    Question,
    User,
)


class UserRepository(Protocol):
    def find_user(self, email: str) -> User | None: ...


class ContentRepository(Protocol):
    def list_certifications(self) -> list[Certification]: ...

    def list_genres(self, certification_id: str) -> list[Genre]: ...

    def list_questions(self, certification_id: str) -> list[Question]: ...

    def get_question(self, question_id: str) -> Question | None: ...


class AttemptRepository(Protocol):
    def record(self, attempt: AttemptRecord) -> None: ...

    def list_for(self, email: str) -> list[AttemptRecord]: ...
