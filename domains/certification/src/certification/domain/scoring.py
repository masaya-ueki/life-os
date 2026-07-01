"""採点ドメインサービス — 正誤判定と選択肢ごとのフィードバック生成。

要件:
- ✓ / ✗ で正誤判定する。
- 各選択肢に対して NG の理由（誤答理由）を提示する。
- 出題元のドキュメントリンクを提示する。
"""

from __future__ import annotations

from collections.abc import Iterable

from .models import ChoiceFeedback, GradedAnswer, Question


def grade(question: Question, selected_choice_ids: Iterable[str]) -> GradedAnswer:
    """選択された選択肢群を採点する。

    単一選択・複数選択のいずれも「正解集合と選択集合が完全一致」で正解とする。
    """
    selected = frozenset(selected_choice_ids)
    correct = question.correct_choice_ids
    is_correct = selected == correct

    feedback = tuple(
        ChoiceFeedback(
            choice_id=c.id,
            text=c.text,
            is_correct=c.is_correct,
            selected=c.id in selected,
            ng_reason=c.ng_reason,
        )
        for c in question.choices
    )

    return GradedAnswer(
        question_id=question.id,
        is_correct=is_correct,
        correct_choice_ids=correct,
        selected_choice_ids=selected,
        feedback=feedback,
        source_url=question.source_url,
        explanation=question.explanation,
    )
