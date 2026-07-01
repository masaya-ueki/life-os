"""DynamoDB 版の出題履歴リポジトリ（P5）。

``application.ports.AttemptRepository`` を満たし、`InMemoryAttemptRepository` の
差し替えとして使う。テーブルは PK=email / SK=question_id（infra/main.tf と対応）。

boto3 は import を遅延させ、テストや境界検査（boto3 未導入のイメージ）で
モジュールを読み込めるようにする。テストは ``table`` を注入して boto3 なしで検証する。
"""

from __future__ import annotations

import os

from ..domain.models import AttemptRecord


class DynamoAttemptRepository:
    """DynamoDB テーブルに出題履歴を put/query する AttemptRepository。"""

    def __init__(self, table_name: str | None = None, *, table=None) -> None:
        if table is None:
            import boto3  # 遅延 import（Lambda/実行時のみ必要）

            name = table_name or os.environ["ATTEMPTS_TABLE"]
            table = boto3.resource("dynamodb").Table(name)
        self._table = table

    def record(self, attempt: AttemptRecord) -> None:
        self._table.put_item(
            Item={
                "email": attempt.email,
                "question_id": attempt.question_id,
                "is_correct": attempt.is_correct,
                "answered_at_ms": attempt.answered_at_ms,
            }
        )

    def list_for(self, email: str) -> list[AttemptRecord]:
        from boto3.dynamodb.conditions import Key  # 遅延 import

        resp = self._table.query(KeyConditionExpression=Key("email").eq(email))
        return [
            AttemptRecord(
                email=item["email"],
                question_id=item["question_id"],
                is_correct=bool(item["is_correct"]),
                answered_at_ms=int(item["answered_at_ms"]),
            )
            for item in resp.get("Items", [])
        ]
