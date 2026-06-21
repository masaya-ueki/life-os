---
name: issue-loop
description: Open な GitHub Issue を 1 件選び、worktree 作成 → 実装 → コードレビュー → 静的検証 → PR 作成まで自動で進める Loop Engineering スキル。PR 作成で必ず停止し main マージは人間が行う。Use when: Issue を自動で実装して PR にしたい、loop でバックログを消化したい。Triggers on: issue-loop, Issueループ, バックログ消化, Issue自動実装, loop実行.
argument-hint: "[#Issue番号 | --scope feat,fix | --max N]"
allowed-tools: Bash, Read, Grep, Glob, Skill, Agent
---

# issue-loop スキル

Open な GitHub Issue を **1 件ずつ**選び、worktree の作成から PR 作成まで自動で進める Loop Engineering スキル。

**安全境界: PR 作成で必ず停止する。`main` へのマージは人間が行う。**

> 設計思想: [guides/development-policy/loop-engineering.md](../../../../guides/development-policy/loop-engineering.md)（Stage 3 への足がかり）
> Issue 運用: [guides/development-policy/issue-operation-rules.md](../../../../guides/development-policy/issue-operation-rules.md)

---

## 対象 Issue の選定

### 対象（すべてを満たすもの）

- `kind: task` ラベルを持つ
- `type: *` ラベルと `system: *` ラベルを両方持つ
- `on-hold` ラベルを持たない
- `kind: product-backlog` ではない
- Issue 本文に **完了条件**（チェックリストまたは箇条書き）が明示されている
- オープンな依存 Issue がない（`Depends on #N` や `Blocked by #N` 記述を確認）

### 除外（人間が対応）

| 条件 | 理由 |
|------|------|
| `type: design` | 設計合意が必要 |
| `type` か `system` ラベルが欠けている | スコープ不明 — ラベル整備が先 |
| `docs/adr/` / `.importlinter` / `pyproject.toml` の変更が主体 | 境界・構造変更 — 人間判断が必要 |
| 完了条件が不明確 | 実装の合否を機械判定できない |
| 依存 Issue が未クローズ | 実装順序が決まっていない |

### フェーズ採用（デフォルトスコープ）

```
デフォルト: type: docs | chore | test
拡大後:    type: feat | fix | refactor  （--scope で指定）
```

運用が安定するまで保守的に `docs / chore / test` から始める。

---

## 1 イテレーションのフロー

```
1. Issue 選定     → 対象 Issue を 1 件選ぶ（完了条件を読んで確認）
2. Worktree 作成  → git pull して main 最新化 → {type}/issue-{N}-{description} ブランチ
3. Issue 精読     → 本文・完了条件・依存関係・スコープを把握
4. 実装           → 実装者サブエージェントに委譲
5. コードレビュー → code-review-general + 変更内容に応じて追加スキルを選択適用
6. 静的検証       → docker compose run --rm lint && docker compose run --rm test
7. コミット & Push → Conventional Commits 形式（type(scope): 要約）
8. PR 作成        ← ここで停止（人間ゲート）
9. 進捗ログ       → Issue にコメント（PR リンク・完了状況）
```

**ステップ 8（PR 作成）を超えて自動処理を続けない。**

---

## ステップごとの詳細

### ステップ 2 — Worktree 作成

```bash
git checkout main && git pull
# ブランチ名: {type}/issue-{N}-{description-kebab-case}
# 例: docs/issue-42-update-adr-readme
```

### ステップ 4 — 実装サブエージェントへの委譲

実装者サブエージェントに以下をコンテキストとして渡す:

- Issue 本文・完了条件の全文
- 対象 `system: *` スコープ（bounded context）
- 事前 grep で特定した関連ファイルパス
- 完了条件チェックリスト（ループ進行の合否判定に使う）

### ステップ 5 — レビュー観点の選択

| 変更内容 | 適用スキル |
|----------|-----------|
| 常時 | `code-review-general` |
| `.py` ファイルを含む | `code-review-python` を追加 |
| `public.py` / `.importlinter` / `pyproject.toml` / `docs/adr/` を含む | `code-review-architecture` を追加 |

`[must]` 指摘が残る場合は修正して再レビューする（最大 2 ラウンド）。2 ラウンド後も残る場合は Issue にコメントして停止。

### ステップ 6 — 静的検証

```bash
docker compose run --rm lint   # 領域境界 (.importlinter) 検査
docker compose run --rm test   # pytest スモークテスト
```

両方 PASS しなければ PR を作らない。失敗した場合は原因を修正して再実行する（最大 3 回）。

### ステップ 8 — PR 作成

```bash
gh pr create \
  --title "{type}({scope}): {要約}" \
  --body "$(cat <<'EOF'
## 概要
- （実装内容を箇条書き）

## 完了条件の確認
- [x] （Issue の完了条件チェックリストをそのままコピーして確認）

## 検証
- [x] `docker compose run --rm lint` PASS
- [x] `docker compose run --rm test` PASS

Closes #{N}
EOF
)"
```

### ステップ 9 — 進捗ログ

Issue に以下の形式でコメントを投稿する:

```
🤖 PR #{PR番号} を作成しました。
- ブランチ: {type}/issue-{N}-{description}
- レビュー: [must] 0件 / lint PASS / test PASS
- 次のステップ: PR のレビューと main へのマージ（人間が行う）
```

---

## 停止条件

以下のいずれかで停止し、ユーザーに状況を報告する:

| 条件 | 対処 |
|------|------|
| 対象 Issue が 0 件 | 「処理対象の Issue がありません」と報告して終了 |
| `--max N` の件数を処理完了 | 指定件数の PR を作成したら終了 |
| ブロッカー検出（依存未解決・完了条件不明確・設計判断が必要） | Issue にコメントして次の Issue へ（またはユーザーに判断を委ねて終了） |
| `[must]` 指摘が 2 ラウンド後も解消しない | Issue にコメントして停止 |
| lint / test が 3 回修正しても通らない | Issue にコメントして停止 |

---

## 使用方法

```
/issue-loop                          # デフォルト: 1 件、docs/chore/test スコープ
/issue-loop --scope feat,fix         # スコープを feat/fix に拡大
/issue-loop --scope feat,fix,refactor --max 3  # 最大 3 件を順次処理
/issue-loop #123                     # 指定 Issue（除外条件チェックは必ず実施）
```

引数なしで呼んだ場合は対象 Issue の候補を提示してから実行確認を求める。

---

## 安全に関する注意事項

- **PR 作成後は停止する** — `gh pr merge` は実行しない
- **`main` ブランチを直接変更しない** — worktree 内でのみ作業する
- **`git push --force` を使わない**
- **`on-hold` の Issue には触れない**
- **同一 `system: *` スコープが重なる並列実行は行わない**（ファイル競合のリスク）

---

## Loop Engineering との関係

このスキルは [Loop Engineering](../../../../guides/development-policy/loop-engineering.md) の実践原則を具体化する:

| 原則 | このスキルでの実現 |
|------|-----------------|
| 意図を一度だけ書く | Issue に完了条件を書けば、それをループが読んで判断する |
| 反復の管理を委譲する | `/loop /issue-loop` で無人反復も可能（PR 停止は維持） |
| 再利用可能なスキル群 | `code-review-*` スキルを組み合わせてレビューを実施 |
| 検証ゲート | lint PASS ∧ test PASS ∧ `[must]`=0 でなければ PR を作らない |
| ハードストップ | `--max N`・ブロッカー検出・lint/test 3 回失敗で必ず停止 |

life-os は現在 Stage 2（HITL）にある。このスキルを `type: docs | chore | test` の小さなタスクから試し、経験を積んで `feat | fix` へ段階的に拡大する。
