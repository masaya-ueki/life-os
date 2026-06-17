---
name: create-issue
description: GitHub Issue を対話形式で作成するスキル。ProductBacklog Issue・Task Issue・調査 Issue のテンプレートに対応。Use when: Issueを作成したい、起票したい、タスクを登録したい。Triggers on: Issue作成, Issue起票, タスク登録, create issue, バックログ作成, 調査Issue, ProductBacklog.
---

# Issue 作成スキル

このスキルは GitHub Issue を `.github/ISSUE_TEMPLATE/` のテンプレートに従って対話形式で作成します。

詳細な Issue 運用ルールは [`guides/development-policy/issue-operation-rules.md`](../../../guides/development-policy/issue-operation-rules.md) を参照してください。

---

## トリガー条件

以下のいずれかの場合に使用：

- ユーザーが「Issue を作成して」「Issue を起票して」と依頼した場合
- ユーザーが `/create-issue` を実行した場合
- 作業開始時に対応 Issue がまだ存在しない場合

---

## ステップ1: Issue の種別を確認

ユーザーに以下を確認する（まだ指定がなければ）：

```
どちらの Issue を作成しますか？
1. ProductBacklog Issue（複数フェーズ・複数日にわたる作業の親 Issue）
2. Task Issue（単発タスク・保守作業など、ProductBacklog が不要な作業）
3. 調査 Issue（技術調査・原因特定・要件調査など）
```

### ProductBacklog Issue の作成条件

**以下をすべて満たす場合**に ProductBacklog Issue を作成する。1つでも満たさない場合は Task Issue のみ作成：

- 複数のフェーズ（2つ以上）にわたる作業である
- 完了まで複数日かかる見込みがある
- 他の Issue・作業との依存関係がある

---

## ステップ2: タイトルの決定

**命名規則**:

```
{type}({scope}): {タイトル}
```

**type 一覧**（ProductBacklog Issue・Task Issue・対応する種別ラベルと type ラベル）:

| type | 用途 | 種別ラベル | type ラベル |
|------|------|-----------|------------|
| `feat` | 新機能の追加 | `task`（ProductBacklog の場合は `product-backlog`） | `type: feat` |
| `fix` | バグ修正 | `bug` | `type: fix` |
| `design` | 設計フェーズの作業（Task Issue のみ）| `task` | `type: design` |
| `test` | テストの追加・修正 | `task` | `type: test` |
| `docs` | ドキュメントの追加・更新 | `task` | `type: docs` |
| `refactor` | リファクタリング | `task` | `type: refactor` |
| `chore` | ビルド設定・ツール変更 | `task` | `type: chore` |
| `perf` | パフォーマンス改善 | `task` | `type: perf` |
| `ci` | CI/CD 設定の変更 | `task` | `type: ci` |

**type**（調査 Issue）: `investigate` 固定 / 種別ラベル: `task` / 補助ラベル: `investigation`

> **Issue Type は使用しない**: 本プロジェクトでは GitHub Organization の Issue Type 機能を運用せず、すべてラベルで管理する。

**scope 一覧**（`system: *` ラベルと一致）:

| scope | 対象 | 対応する system ラベル |
|-------|------|---------------------|
| `task` | タスク管理 | `system: task` |
| `common` | 横断的・共通基盤 | `system: common` |
| `content-sales` | 自作ツール等の販売管理 | `system: content-sales` |
| `deps` | 依存パッケージ | `system: deps` |

> 今後 life-os の領域が増えたら、scope と `system: *` ラベルを `guides/development-policy/issue-operation-rules.md` と `scripts/setup-github-labels.sh` に追加する。

---

## ステップ3: Issue 本文の収集

ユーザーから以下の情報を収集する（未提供の項目のみ確認する）。

### ProductBacklog Issue の必須項目

1. **概要**: この取り組みで実現したいことを 2〜3 行で記載
2. **要件説明**: 要件テキストまたは要件ドキュメントへのリンク
3. **スコープ**: 対象（含む）と対象外（含まない）
4. **影響範囲**: 変更によって影響を受けるコンポーネント・機能
5. **依存関係**: 依存する Issue・依存される Issue
6. **Task Issue チェックリスト**: フェーズ分けされた Task Issue の一覧
7. **完了条件**: 完了と判断する基準

### Task Issue の必須項目

1. **背景**: この Issue が生まれた経緯や状況
2. **課題**: 現状の問題点や達成したいこと
3. **影響範囲**: 変更によって影響を受けるコンポーネント・ファイル
4. **対応方針**: 採用する方針と、その方針を選んだ理由（理由必須）
5. **対応詳細**: 具体的な作業内容

### 調査 Issue の必須項目

1. **背景**: この調査が必要になった経緯や状況
2. **課題**: 何を調査するのか、調査の目的
3. **影響範囲**: 調査対象のコンポーネント・ファイル・機能
4. **調査方法**: どのように調査するか
5. **調査詳細**: 調査した内容（作成時は空でも可）

---

## ステップ4: Issue 作成コマンドの実行

収集した情報をもとに `gh issue create` コマンドを実行する。

### ProductBacklog Issue の作成例

```bash
gh issue create \
  --title "{type}({scope}): {タイトル}" \
  --label "product-backlog" \
  --body "$(cat <<'EOF'
## 概要

{概要}

## 要件説明

{要件テキストまたはリンク}

## スコープ

### 対象（含む）

- {対象}

### 対象外（含まない）

- {対象外}

## 影響範囲

- {影響を受けるコンポーネント・機能}

## 依存関係

### このIssueが依存するもの

- {依存する Issue または「なし」}

### このIssueに依存するもの

- {依存される Issue または「なし」}

## Task Issue チェックリスト

### フェーズ 1: 設計

- [ ] `design({scope}): {タイトル}`

### フェーズ 2: 実装

- [ ] `feat({scope}): {タイトル}`

### フェーズ 3: テスト

- [ ] `test({scope}): {タイトル}`

## ブランチ運用

\`\`\`bash
# main から feature ブランチを作成
git switch -c {type}/issue-{N}-{作業名-kebab-case}

# 並行作業する場合は git worktree を使う（Claude Code は --worktree でも可）
# git worktree add ../life-os-{type}-issue-{N} -b {type}/issue-{N}-{作業名-kebab-case}
\`\`\`

## 完了条件

- [ ] 全 Task Issue がクローズされている
- [ ] {その他の完了条件}
EOF
)"
```

### Task Issue の作成例（単発タスク）

```bash
gh issue create \
  --title "{type}({scope}): {タイトル}" \
  --label "no-product-backlog" \
  --body "$(cat <<'EOF'
## 背景

{背景の内容}

## 課題

{課題の内容}

## 影響範囲

- {影響範囲}

## 内容

### 対応方針

{対応方針と理由}

### 対応詳細

{具体的な作業内容}

## 結果

<!-- Issue クローズ後に記載 -->
EOF
)"
```

### 調査 Issue の作成例

```bash
gh issue create \
  --title "investigate({scope}): {タイトル}" \
  --label "investigation" \
  --body "$(cat <<'EOF'
## 背景

{背景の内容}

## 課題

{課題の内容}

## 影響範囲

- {影響範囲}

## 内容

### 調査方法

{調査方法}

### 調査詳細

{調査した内容・ログ・資料など}

## 結果

<!-- 調査完了後に記載 -->
EOF
)"
```

---

## ステップ5: 作成結果の確認

Issue が作成されたら URL を表示し、ユーザーに確認を促す。

ProductBacklog Issue を作成した場合は、Task Issue（Sub-issue）の作成・紐づけを案内する：

```
Issue を作成しました: {URL}

ProductBacklog Issue の場合、以下も実施してください：
1. Task Issue（Sub-issue）を作成して紐づける
2. ProductBacklog 本文の Task Issue チェックリストを更新する
```

---

## 注意事項

- **ラベル**: ProductBacklog Issue は `product-backlog`、単発 Task Issue は `no-product-backlog`、調査 Issue は `investigation`。加えて type ラベル（必須）と system ラベル（推奨）を付与する
- **状態管理**: 外部のプロジェクトボードは使わず、Issue の open/close・チェックリスト・`on-hold` ラベルで管理する
- **タイトル**: 命名規則（`{type}({scope}): {タイトル}`）に従う
- **日本語**: タイトル・本文はすべて日本語で記述
- **理由必須**: Task Issue の対応方針には必ず理由を記載する

---

**このスキルはユーザーが Issue 作成を依頼した際に自動的に適用してください。**
