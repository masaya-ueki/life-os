"""問題データ（`data/*.json`）の整合性ゲート。

`JsonContentRepository` でロードした実データに対し、出題品質の前提
（id 一意・genre 整合・選択肢構造・正解数・NG 理由・公式出典）を機械的に検査する。
問題作成スキル／サブエージェント（#97）が守るべき不変条件をここで強制し、
`docker compose run --rm test` を登録時の検証ゲートにする。

ローダー（`adapters/repository.py`）は必須キーの有無と `format` enum しか見ないため、
データレベルの整合性は本ファイルが唯一の防波堤。
"""

from __future__ import annotations

from collections import Counter

import pytest

from certification.adapters.repository import JsonContentRepository
from certification.domain.models import QuestionFormat

CERT_ID = "snowpro-core"

OFFICIAL_DOCS_PREFIX = "https://docs.snowflake.com/"


@pytest.fixture(scope="module")
def content() -> JsonContentRepository:
    return JsonContentRepository()


@pytest.fixture(scope="module")
def questions(content: JsonContentRepository):
    return content.list_questions(CERT_ID)


@pytest.fixture(scope="module")
def genre_ids(content: JsonContentRepository) -> set[str]:
    return {g.id for g in content.list_genres(CERT_ID)}


def test_question_ids_are_unique(questions):
    dups = [qid for qid, n in Counter(q.id for q in questions).items() if n > 1]
    assert not dups, f"重複した問題 id: {dups}"


def test_genre_ids_reference_defined_genres(questions, genre_ids):
    dangling = sorted({q.genre_id for q in questions} - genre_ids)
    assert not dangling, f"未定義の genre_id を参照している: {dangling}"


def test_every_genre_has_at_least_one_question(questions, genre_ids):
    used = {q.genre_id for q in questions}
    empty = sorted(genre_ids - used)
    assert not empty, f"問題が 0 件のジャンル: {empty}"


def test_each_question_has_four_labeled_choices(questions):
    for q in questions:
        ids = [c.id for c in q.choices]
        assert ids == ["a", "b", "c", "d"], f"{q.id}: 選択肢 id が a–d の4件でない: {ids}"


def test_correct_choice_count_matches_format(questions):
    for q in questions:
        n = sum(1 for c in q.choices if c.is_correct)
        if q.format is QuestionFormat.SINGLE:
            assert n == 1, f"{q.id}: single は正解ちょうど1件のはず（実際 {n} 件）"
        else:
            assert n >= 2, f"{q.id}: multiple は正解2件以上のはず（実際 {n} 件）"


def test_every_choice_has_ng_reason(questions):
    """誤答理由（正解肢も解説文）は全選択肢に必須。学習フィードバックの根拠。"""
    for q in questions:
        for c in q.choices:
            assert c.ng_reason.strip(), f"{q.id}/{c.id}: ng_reason が空"


def test_source_url_points_to_official_docs(questions):
    for q in questions:
        assert q.source_url.startswith(OFFICIAL_DOCS_PREFIX), (
            f"{q.id}: source_url が公式ドキュメント（{OFFICIAL_DOCS_PREFIX}）でない: {q.source_url!r}"
        )


def test_text_and_explanation_are_present(questions):
    for q in questions:
        assert q.text.strip(), f"{q.id}: text が空"
        assert q.explanation.strip(), f"{q.id}: explanation が空"
