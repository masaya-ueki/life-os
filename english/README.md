# english — 英語学習

> **構成根拠**: [ADR-0002 複数領域を Modular Monolith × Bounded Context で共存させる](../docs/adr/0002-modular-monolith-bounded-context.md)

英語学習で得た語彙・表現を蓄積し、再利用できるようにする Bounded Context。
データ（学習メタ情報）が主役のため **アーキタイプB（薄い構成）** を採る。

## ユビキタス言語（この領域の用語）

| 用語 | 意味 | 備考 |
|------|------|------|
| Vocabulary | 単語・イディオム1件（中学生以上） | `data/vocabulary.md` の1行 |
| Expression | 重要な表現（言い回し・構文）1件 | `data/expressions.md` の1行 |
| 学習ログ | 学習内容を蓄積する Markdown テーブル | `data/` 配下。保存兼一覧 |

## 内部構成

```
src/english/
├── models.py   # スキーマ（VocabularyEntry / ExpressionEntry）
├── index.py    # 検索・整形（search_vocabulary / search_expressions）
└── public.py   # ★他領域に公開する唯一の契約（EnglishItemRef）
data/           # ★主役: 学習した内容（Markdown テーブル）
├── vocabulary.md   # 単語・イディオム一覧
└── expressions.md  # 重要な表現一覧
tests/
```

## 学習スキル

翻訳しながら語彙・表現を抽出して `data/` に蓄積する最初のスキルは
[`.claude/skills/english-translate/`](../.claude/skills/english-translate/SKILL.md)。
英語 or 日本語の文章を渡すと、もう一方の言語へ翻訳し、中学生以上の英単語・重要な表現を
意味・用例つきで出力し、新規分を学習ログへ追記する。

## 境界（Context Map メモ）

- 他領域からは `from english.public import ...` のみ許可。
- 現状、他領域への依存は無し。
