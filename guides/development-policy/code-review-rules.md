# コードレビュー運用ルール

> **適用対象**: life-os の全 PR レビュー
>
> **設計根拠**: [ADR-0004 PRレビューをエージェント＋観点別スキルで運用する](../../docs/adr/0004-pr-review-agent.md)

このドキュメントはレビュー運用の**単一の真実**。レビュー観点の実体は `.claude/skills/code-review-*` に、進行（自動レビュー〜マージ）は `.claude/agents/pr-reviewer.md` にある。本ファイルはその全体像と方針を定める（[Issue 運用ルール](./issue-operation-rules.md) と同じ位置づけ）。

---

## 目次

1. [全体像](#1-全体像)
2. [レビュー観点の構成（観点軸＋領域早見表）](#2-レビュー観点の構成観点軸領域早見表)
3. [指摘の記載（severity 語彙）](#3-指摘の記載severity-語彙)
4. [修正点があるとき（修正PRを作成）](#4-修正点があるとき修正prを作成)
5. [問題がないとき（検証付き自動マージ）](#5-問題がないとき検証付き自動マージ)
6. [レビューの大原則](#6-レビューの大原則)
7. [参照](#7-参照)

---

## 1. 全体像

```
PR
 └─ pr-reviewer エージェント
      ① 内容確認（領域・言語・境界を判定）
      ② レビュー（code-review-general 必須 + python / architecture を選択）
      ③ 指摘記載（[must]/[imo]/[nits]/[ask]/[fyi]）
      ④ 分岐
         ├─ [must] あり → 修正して「新規PR」を作成（元PRはマージしない）
         └─ [must] なし → pytest ∧ lint-imports pass なら マージ → main pull
```

- **スコープはレビューとマージ**（＋修正点があれば修正PRの作成）。
- ブランチ戦略は GitHub Flow（`main` のみ、PR は `Closes #N`）。詳細は [Issue 運用ルール](./issue-operation-rules.md)・README「Git 戦略」。

---

## 2. レビュー観点の構成（観点軸＋領域早見表）

観点は**観点軸**で 3 スキルに分割し、**領域差は早見表**で表現する（領域ごとに別スキルは作らない）。

| スキル | 軸 | 適用条件 |
|--------|----|---------|
| [`code-review-general`](../../.claude/skills/code-review-general/SKILL.md) | 言語非依存（索引・大原則・severity） | **常に適用** |
| [`code-review-python`](../../.claude/skills/code-review-python/SKILL.md) | 言語（Python 3.12+） | `.py` を含む変更 |
| [`code-review-architecture`](../../.claude/skills/code-review-architecture/SKILL.md) | 境界・構造（life-os 固有） | `.importlinter` / `pyproject.toml` / `*/public.py` / 新トップレベルdir / `docs/adr` を含む変更 |

領域ごとの重点観点（アーキタイプA/B・content領域・shared）は [`code-review-general/references/domain-checklist.md`](../../.claude/skills/code-review-general/references/domain-checklist.md) の早見表で引く。

> 領域が増えても**早見表に行を足すだけ**で対応する（スキルは増やさない）。これは `slide-expression` の「索引＋references」と同じ設計（[ADR-0004](../../docs/adr/0004-pr-review-agent.md)）。

---

## 3. 指摘の記載（severity 語彙）

接頭辞は [`.github/pull_request_template.md`](../../.github/pull_request_template.md) で定義済みのものと**完全に一致**させる。独自に増やさない。

| 接頭辞 | 意味 | マージへの影響 |
|--------|------|--------------|
| `[must]` | 必ず変更してほしい | **ブロッキング**（正確性・明示要件・セキュリティ・競合・境界違反） |
| `[imo]` | 意見だが必須ではない | 非ブロッキング |
| `[nits]` | ささいな指摘 | 非ブロッキング |
| `[ask]` | 質問 | 非ブロッキング |
| `[fyi]` | 参考情報 | 非ブロッキング |

- 記法: `[severity] path:line — 何が問題か（なぜ）。提案: ...`
- レビューコメント末尾に **severity 別件数サマリ**を付ける。
- **`[must]` の有無**が ④ の分岐（修正PR or マージ）を決める。

---

## 4. 修正点があるとき（修正PRを作成）

`[must]` の指摘がある場合、pr-reviewer は次を行う。

1. 元PRのブランチを起点に修正ブランチを切る。
2. `[must]` の解消に絞って修正する（余計な変更を混ぜない。規模が大きければ subagent に委譲）。
3. `uv run pytest` / `uv run lint-imports` で検証する。
4. **新規PRを作成**する（base=元PRのブランチ、本文に元PR参照・対応指摘・検証結果）。
5. **元PRはマージしない。** 修正PRは人/別エージェントのレビューを経て取り込む。

> 「指摘を出して終わり」ではなく**修正点があればPRまで作成する**のがこのリポジトリの方針。ただし修正を未レビューでマージはしない（fresh-context の原則）。

---

## 5. 問題がないとき（検証付き自動マージ）

`[must]` が 0 件の場合、pr-reviewer は**検証ゲート**を通してからマージする。

- ゲート: `uv run pytest` **pass** ∧ `uv run lint-imports` **pass** ∧ `[must]` = 0
- ゲート通過 → `gh pr merge`（マージコミット方式・`Closes #N` で Issue 自動クローズ）→ `git switch main && git pull`
- いずれか不成立 → **マージせず**、失敗内容（テスト/lint 出力）を報告

> GitHub Actions の CI は未設置のため、検証は**ローカル実行**（`uv run ...`）で行う。CI を導入したら、このゲートを CI の結果に置き換える（ADR-0004 のトレードオフ参照）。

### スコープゲート（自動マージしてよい範囲の判定）

検証ゲートを通る前に、**変更ファイルパスから「自動マージ（auto）/ 人間レビュー必須（human）」を決定的に判定する**。判定の実体（決定木・パス表）は [`review-and-merge-pr`](../../.claude/skills/review-and-merge-pr/SKILL.md) スキルが単一の真実。

| 判定 | 条件（上から順に評価） | 扱い |
|------|----------------------|------|
| human | 方針・境界・契約パスを含む（`**/public.py` / `.importlinter` / `pyproject.toml` / `docs/adr` / `guides` / `rule` / `.claude` / `.github` / ルート `CLAUDE.md`・`README.md` 等） | マージしない |
| human | `shared/**` を含む（基盤・全領域波及） | マージしない |
| human | Bounded Context（`task`/`content-sales`/`media`/`travel`/`english`）を2つ以上含む（領域横断） | マージしない |
| auto | 上記いずれにも非該当（単一領域内 or content のみ） | 検証ゲートへ |

> **auto のみ**が上記の検証ゲートに進み、通過すれば無人マージされる。**human はマージせず人間レビューに委ねる**。設計根拠は [ADR-0008](../../docs/adr/0008-pr-auto-merge-scope-gate.md)。

---

## 6. レビューの大原則

`.claude/skills/code-review-general` と共通。出典は Anthropic「Best practices for Claude Code」＋ Google Engineering Practices。

1. **過剰指摘をしない**: 正確性・明示要件・セキュリティに効くものだけ `[must]`。健全なら指摘ゼロで承認してよい。
2. **証拠主義**: 主張でなくテスト/コマンド出力で確認。検証できないものは通さない。
3. **fresh-context**: 差分と判定基準だけで評価する。
4. **code health で承認**: 完璧でなく、全体の健全性が向上すれば前進を優先する。

---

## 7. 参照

- エージェント: [`.claude/agents/pr-reviewer.md`](../../.claude/agents/pr-reviewer.md)
- スキル: [`code-review-general`](../../.claude/skills/code-review-general/SKILL.md) / [`code-review-python`](../../.claude/skills/code-review-python/SKILL.md) / [`code-review-architecture`](../../.claude/skills/code-review-architecture/SKILL.md)
- スコープゲート（自動マージ判定）: [`review-and-merge-pr`](../../.claude/skills/review-and-merge-pr/SKILL.md) / [ADR-0008](../../docs/adr/0008-pr-auto-merge-scope-gate.md)
- 領域早見表: [`domain-checklist.md`](../../.claude/skills/code-review-general/references/domain-checklist.md)
- 接頭辞の定義: [`.github/pull_request_template.md`](../../.github/pull_request_template.md)
- 設計決定: [ADR-0004](../../docs/adr/0004-pr-review-agent.md)
- 関連: [Issue 運用ルール](./issue-operation-rules.md) / [ADR-0002（領域境界）](../../docs/adr/0002-modular-monolith-bounded-context.md)
