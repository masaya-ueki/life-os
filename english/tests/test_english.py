"""english のスモークテスト（スケルトン）。"""

from english.index import search_expressions, search_vocabulary
from english.models import ExpressionEntry, VocabularyEntry


def test_search_vocabulary_matches_term_or_meaning():
    entries = [
        VocabularyEntry(
            term="inevitable", meaning="避けられない", example="War seemed inevitable."
        ),
        VocabularyEntry(
            term="break the ice",
            meaning="緊張をほぐす",
            example="He told a joke to break the ice.",
            kind="idiom",
        ),
    ]
    assert [e.term for e in search_vocabulary(entries, "ice")] == ["break the ice"]
    assert [e.term for e in search_vocabulary(entries, "避けられない")] == ["inevitable"]


def test_search_expressions_matches_expression_or_meaning():
    entries = [
        ExpressionEntry(
            expression="It goes without saying that ...",
            meaning="〜は言うまでもない",
            example="It goes without saying that health is important.",
        ),
    ]
    assert len(search_expressions(entries, "言うまでもない")) == 1
    assert search_expressions(entries, "存在しない") == []
