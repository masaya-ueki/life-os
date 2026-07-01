"""certification 領域のスモークテスト。

要件由来の重要ケース:
- 選択肢シャッフルが時刻ミリ秒シードで決定的、かつ正解位置が特定位置（B/D）に偏らない。
- 出題モード3種の選択、単一/複数選択の採点、認証、問題集フィルタ。
"""

from __future__ import annotations

from collections import Counter

import pytest

from certification.adapters.repository import (
    EnvUserRepository,
    InMemoryAttemptRepository,
    JsonContentRepository,
)
from certification.adapters.security import hash_password, verify_password
from certification.application import question_bank, quiz_service
from certification.application.auth import AuthError, authenticate
from certification.domain import quiz, scoring
from certification.domain.models import (
    Choice,
    Question,
    QuestionFormat,
    QuizMode,
)

CERT_ID = "snowpro-core"


def _q(qid: str, genre: str, correct_index: int, fmt=QuestionFormat.SINGLE) -> Question:
    choices = tuple(
        Choice(id=chr(ord("a") + i), text=f"choice-{i}", is_correct=(i == correct_index),
               ng_reason="" if i == correct_index else f"ng-{i}")
        for i in range(4)
    )
    return Question(
        id=qid, certification_id=CERT_ID, genre_id=genre, text=f"q-{qid}",
        format=fmt, choices=choices, source_url="https://example.com", explanation="",
    )


# ---- シャッフル: 決定性と正解位置の非偏り ----------------------------------


def test_shuffle_is_deterministic_by_seed():
    q = _q("x", "g", correct_index=0)
    a = quiz.shuffle_choices(q, 1234567890123)
    b = quiz.shuffle_choices(q, 1234567890123)
    assert [c[0] for c in a.choices] == [c[0] for c in b.choices]
    # 正解情報は提示に含まれない（choice は (id, text) のみ）。
    assert all(len(c) == 2 for c in a.choices)


def test_correct_answer_position_not_biased_to_b_or_d():
    """ミリ秒シードのシャッフルで正解位置が各位置ほぼ一様（B/D 偏りなし）。"""
    q = _q("x", "g", correct_index=0)  # 元は先頭が正解
    positions = Counter()
    for seed in range(100000, 100000 + 4000):
        presented = quiz.shuffle_choices(q, seed)
        pos = [cid for cid, _ in presented.choices].index("a")  # 正解 id="a" の位置
        positions[pos] += 1
    # 4 位置に分散し、どの位置も極端に偏らない（理想は各25%）。
    assert set(positions) == {0, 1, 2, 3}
    for pos in range(4):
        share = positions[pos] / 4000
        assert 0.20 < share < 0.30, f"位置 {pos} の割合が偏っている: {share:.3f}"


# ---- 出題モード ------------------------------------------------------------


def test_select_questions_modes():
    pool = [_q(f"a{i}", "architecture", 0) for i in range(6)] + [
        _q(f"s{i}", "security", 0) for i in range(6)
    ]
    seed = 42

    genre = quiz.select_questions(pool, QuizMode.GENRE_RANDOM, seed, genre_id="security")
    assert all(q.genre_id == "security" for q in genre)

    full = quiz.select_questions(pool, QuizMode.FULL_EXAM, seed)
    assert len(full) == 10  # QUESTIONS_PER_QUIZ

    wrong = quiz.select_questions(
        pool, QuizMode.WRONG_ONLY, seed, wrong_question_ids=frozenset({"a0", "s1"})
    )
    assert {q.id for q in wrong} == {"a0", "s1"}


def test_genre_random_requires_genre_id():
    with pytest.raises(ValueError):
        quiz.select_questions([_q("a", "g", 0)], QuizMode.GENRE_RANDOM, 1)


# ---- 採点 ------------------------------------------------------------------


def test_grade_single_choice():
    q = _q("x", "g", correct_index=2, fmt=QuestionFormat.SINGLE)
    ok = scoring.grade(q, ["c"])
    assert ok.is_correct
    ng = scoring.grade(q, ["a"])
    assert not ng.is_correct
    # 各選択肢に NG 理由と出題元リンクが載る。
    assert any(f.ng_reason for f in ng.feedback)
    assert ng.source_url == "https://example.com"


def test_grade_multiple_choice_requires_exact_set():
    choices = (
        Choice("a", "a", True, ""),
        Choice("b", "b", True, ""),
        Choice("c", "c", False, "ng"),
        Choice("d", "d", False, "ng"),
    )
    q = Question("m", CERT_ID, "g", "q", QuestionFormat.MULTIPLE, choices)
    assert scoring.grade(q, ["a", "b"]).is_correct
    assert not scoring.grade(q, ["a"]).is_correct
    assert not scoring.grade(q, ["a", "b", "c"]).is_correct


# ---- 認証 ------------------------------------------------------------------


def test_password_hash_roundtrip():
    stored = hash_password("s3cret!")
    assert verify_password("s3cret!", stored)
    assert not verify_password("wrong", stored)
    assert "s3cret!" not in stored  # 平文は保存されない


def test_authenticate_success_and_failure():
    users = EnvUserRepository(
        {"CERT_USER_EMAIL": "me@example.com", "CERT_USER_PASSWORD": "pw12345"}
    )
    user = authenticate(users, "me@example.com", "pw12345")
    assert user.email == "me@example.com"
    with pytest.raises(AuthError):
        authenticate(users, "me@example.com", "bad")
    with pytest.raises(AuthError):
        authenticate(users, "nobody@example.com", "pw12345")


# ---- リポジトリ + 問題集フィルタ（実データ） -------------------------------


def test_json_repository_loads_seed_data():
    content = JsonContentRepository()
    certs = content.list_certifications()
    assert any(c.id == CERT_ID for c in certs)
    assert len(content.list_genres(CERT_ID)) >= 3
    assert len(content.list_questions(CERT_ID)) >= 10


def test_quiz_start_and_bank_filters_with_real_data():
    content = JsonContentRepository()
    attempts = InMemoryAttemptRepository()
    email = "me@example.com"

    started = quiz_service.start_quiz(
        content, attempts, email=email, certification_id=CERT_ID,
        mode=QuizMode.FULL_EXAM, seed_ms=1700000000000,
    )
    assert len(started.questions) == 10

    # 1問採点 → 出題済み/正誤フラグが反映される。
    first = started.questions[0]
    quiz_service.grade_answer(
        content, attempts, email=email, question_id=first.id,
        selected_choice_ids=[first.choices[0][0]], answered_at_ms=1700000000001,
    )

    answered = question_bank.list_bank(
        content, attempts, email=email, certification_id=CERT_ID, answered=True
    )
    assert [it.question_id for it in answered] == [first.id]

    unanswered = question_bank.list_bank(
        content, attempts, email=email, certification_id=CERT_ID, answered=False
    )
    assert first.id not in {it.question_id for it in unanswered}
