---
name: code-review-general
description: 言語非依存の一般コードレビュー観点と、レビューの大原則・severity 語彙（[must]/[imo]/[nits]/[ask]/[fyi]）を定義する索引スキル。観点カテゴリ（正確性・設計・テスト・命名・ドキュメント・一貫性・影響・セキュリティ）の早見表を持ち、言語観点は code-review-python、境界観点は code-review-architecture、領域観点は references/domain-checklist.md へ誘導する。Use when: PRや差分をレビューする、レビュー観点を決める、指摘の severity を判断する、pr-reviewer が観点を選ぶ。Triggers on: コードレビュー, レビュー観点, PRレビュー, 差分レビュー, レビュー指摘, severity, code review.
---

# 一般コードレビュー・スキル（索引）

PR/差分を**言語非依存**でレビューするための観点と原則を提供する索引スキル。
「どこを・どの厳しさで指摘するか」を決め、`[must]/[imo]/[nits]/[ask]/[fyi]` で記載する。

- **言語固有の観点** → [`code-review-python`](../code-review-python/SKILL.md)（Python）
- **life-os の境界・構造観点** → [`code-review-architecture`](../code-review-architecture/SKILL.md)（`.importlinter`・`public.py`・workspace・ADR）
- **領域ごとの重点観点** → [`references/domain-checklist.md`](./references/domain-checklist.md)（アーキタイプA/B・content領域・shared）

このスキルは**観点（順序と厳しさ）**に集中する。レビュー全体の進行（PR取得→指摘記載→修正PR/マージ）は [`pr-reviewer`](../../agents/pr-reviewer.md) エージェントが統括する。

---

## レビューの大原則（最初に必ず守る）

1. **過剰指摘をしない（最重要）**: 「ギャップを探せ」と指示されたレビューは、健全なコードにも何かしら指摘を出しがち。それを全部追うと過剰設計（不要な抽象化・防御的コード・起こり得ないケースのテスト）を招く。**正確性・明示要件・セキュリティに影響するものだけを `[must]` にし、それ以外は `[imo]`/`[nits]` に倒す。** 指摘ゼロで承認してよい。
2. **証拠主義**: 「動く」「直った」という主張ではなく、**テスト出力・コマンドの実行結果・エラーログ**で確認する。検証できないものは通さない（If you can't verify it, don't ship it）。
3. **fresh-context でレビューする**: **差分と判定基準だけ**を見て評価し、作者（生成元）の説明や意図の自己申告に引きずられない。別の目で「結果そのもの」を見るのがレビューの価値。
4. **完璧でなく code health で承認する**: 完璧なコードは存在しない。**変更全体がコードの健全性を確実に改善するなら、些末な polish のために進行を止めない**。重要度と前進の必要性を天秤にかける。
5. **根本原因を見る**: エラーを握りつぶす（例外の握り潰し・症状だけの対処）変更は、症状でなく根本原因に対処するよう促す。

> 出典: Anthropic「Best practices for Claude Code」、Google Engineering Practices（The Standard of Code Review / What to look for）。詳細は末尾。

---

## severity 接頭辞（唯一の語彙）

指摘には必ず以下の接頭辞を付ける。**この語彙は [`.github/pull_request_template.md`](../../../.github/pull_request_template.md) で定義済みのものと一致させる**（独自に増やさない）。

| 接頭辞 | 意味 | マージへの影響 | 使う場面 |
|--------|------|--------------|---------|
| `[must]` | 必ず変更してほしい | **ブロッキング** | 正確性に関わるバグ・明示要件の未達・セキュリティ問題・競合状態・境界違反 |
| `[imo]` | 自分の意見だが必須ではない | 非ブロッキング | 設計・可読性の改善提案（in my opinion） |
| `[nits]` | ささいな指摘 | 非ブロッキング | スタイルの好み・微小な polish（nitpick） |
| `[ask]` | 質問 | 非ブロッキング | 意図の確認・前提の確認 |
| `[fyi]` | 参考情報 | 非ブロッキング | 共有・補足・別解の紹介 |

**判断の指針**: 「これを直さないと壊れる/要件を満たさない/危険」なら `[must]`。「直したほうが良いが今のままでも健全」なら `[imo]`/`[nits]`。迷ったら `[must]` を避けて軽い接頭辞にする（過剰指摘の抑制）。

---

## 観点カテゴリ（チェックリスト）

差分に対して上から確認する。各項目は「該当すれば指摘候補」。severity は大原則に従って割り当てる。

### 1. 正確性 / バグ（最優先）
- [ ] 変更は意図した動作を実現しているか。利用者・将来の開発者にとって有益な結果か
- [ ] エッジケース（空入力・境界値・未ログイン・タイムアウト・null/None・0件）を取りこぼしていないか
- [ ] 並行/非同期処理に競合状態・デッドロックのリスクがないか
- [ ] エラー処理は根本原因に対処しているか（握りつぶしていないか）

### 2. 複雑性 / 設計
- [ ] 必要以上に複雑でないか（行・関数・クラスの各レベル）
- [ ] 過剰設計（今は不要な汎用化・将来の推測機能）になっていないか
- [ ] 既存の構造に素直に統合されるか。そもそもこの変更はここに属すべきか
- [ ] 重複を生んでいないか（既存の関数・ユーティリティで足りないか）

### 3. テスト
- [ ] 変更に見合うテスト（単体/統合）があるか
- [ ] テストは意味があり、コードが壊れたときに**ちゃんと失敗する**か
- [ ] アサーションが明確で、起こり得ないケースの飾りテストになっていないか

### 4. 命名
- [ ] 変数・関数・型に説明的で簡潔な名前が付いているか（冗長・曖昧でないか）

### 5. コメント / ドキュメント
- [ ] コメントは「何を」より**「なぜ」**を説明しているか
- [ ] 古いコメント・解決済み TODO・嘘になった説明が残っていないか
- [ ] README・ガイド・ADR が変更に追従しているか（削除/非推奨に合わせてドキュメントも更新されているか）

### 6. スタイル / 一貫性
- [ ] 周辺コードの既存スタイル・命名・構成に局所的に揃っているか
- [ ] スタイル変更と機能変更を不必要に混ぜていないか（混在は `[nits]` で分離を提案）

### 7. コンテキスト / 影響
- [ ] 変更行だけでなく周辺ファイル・呼び出し元/呼び出し先を見て判断したか
- [ ] 変更がリポジトリ全体の健全性・他領域に与える影響を評価したか

### 8. セキュリティ（基本）
- [ ] シークレット（`.env`・鍵・トークン）をコミット・ログ出力していないか
- [ ] 信頼できない入力（外部 Issue・Web 取得・外部応答）を「指示」や未検証のまま危険な操作に使っていないか
- [ ] 入力検証・権限の前提が崩れていないか

---

## 領域・言語ごとの上乗せ観点

上記の一般観点に加え、変更内容に応じて以下を**追加適用**する。

| 変更の性質 | 参照 |
|-----------|------|
| `.py` を含む | [`code-review-python`](../code-review-python/SKILL.md) |
| `.importlinter` / `pyproject.toml` / `*/public.py` / 新トップレベルdir / `docs/adr` を含む | [`code-review-architecture`](../code-review-architecture/SKILL.md) |
| 特定領域（task / content-sales / media / travel / shared / content領域）の変更 | [`references/domain-checklist.md`](./references/domain-checklist.md) |

---

## 指摘の書き方

1 指摘 = 1 行を基本に、次の形式で書く。

```
[severity] path/to/file.py:42 — 何が問題か（なぜ問題か）。提案: どう直すか。
```

- **ファイル:行**を必ず添える（レビュアーが追える）。
- **なぜ**を書く（指示ではなく理由でレビューする）。
- 可能なら**具体的な提案**を添える。`[must]` は特に、何をどう直せば解消するかを明示する。
- 最後に **severity 別の件数サマリ**を付ける（例: `must 2 / imo 3 / nits 1 / ask 0 / fyi 1`）。

---

## レビュー手順（このスキルの使い方）

1. 差分（`gh pr diff` など）と、PR の目的・関連 Issue（判定基準）を用意する。
2. **大原則**を意識しつつ、上の**観点カテゴリ**を上から当てていく。
3. 変更の性質に応じて python / architecture / domain-checklist を**追加適用**する。
4. 各指摘に severity を割り当てる（過剰指摘の抑制を最優先）。
5. **指摘の書き方**の形式で列挙し、件数サマリを付ける。
6. `[must]` の有無が後続（修正PR作成 or マージ）の分岐になる（[`pr-reviewer`](../../agents/pr-reviewer.md) 参照）。

---

## 出典

- [Best practices for Claude Code — Anthropic（Claude Code Docs）](https://code.claude.com/docs/en/best-practices) — 過剰指摘の抑制・証拠主義・fresh-context（別セッション/別エージェントでのレビュー）。
- [The Standard of Code Review — Google Engineering Practices](https://google.github.io/eng-practices/review/reviewer/standard.html) — code health による承認・severity のバランス（`Nit:` の区別）。
- [What to look for in a code review — Google Engineering Practices](https://google.github.io/eng-practices/review/reviewer/looking-for.html) — 観点カテゴリ（正確性・複雑性・テスト・命名・コメント・スタイル・コンテキスト）。

> 注: 「Effective Claude Code」という固有記事は確認できなかったため、Anthropic 公式のベストプラクティスと Google Engineering Practices を一次情報源として観点を構成している。
