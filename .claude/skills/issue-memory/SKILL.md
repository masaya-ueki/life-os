---
name: issue-memory
description: GitHub Issue を Claude の作業メモリとして活用するスキル。Issue 未存在時の起票（ProductBacklog / Task / 調査 Issue）から、作業開始時の読み込み・ブランチ把握、途中経過の記録、最終結果の書き込みまでを一本化する。Use when: Issue を作成したい、起票したい、タスクを登録したい、Issue #XXX で作業を始めたい、Issue に結果を書きたい。Triggers on: Issue作成, Issue起票, タスク登録, create issue, バックログ作成, 調査Issue, ProductBacklog, issue-memory, Issue をメモリとして記録, Issue に結果を書いて, Issue で作業を始めて.
---

# Issue メモリスキル

このスキルは GitHub Issue を Claude の作業メモリとして活用し、**Issue の起票から完了報告まで**をひとつのワークフローに集約します。

---

## トリガー条件

以下のいずれかの場合に使用：

- ユーザーが `/issue-memory` を実行した場合
- ユーザーが「Issue を作成して」「Issue を起票して」「タスクを登録したい」と依頼した場合
- ユーザーが「Issue #XXX で作業を始めて」と言った場合
- ユーザーが「Issue をメモリとして記録して」「Issue に結果を書いて」と依頼した場合
- 作業完了時に Issue への結果記載を求められた場合

---

## ワークフロー概要

```
[Issue が存在しない場合]: Issue を作成する
     ↓
ステップ0: Issue を読む（作業開始時）
     ↓
ステップ1: ブランチ作業内容をまとめる（作業開始時）
     ↓
ステップ2: 都度記録する（作業中・任意タイミング）
     ↓
ステップ3: Issue に最終結果を書く（作業完了時）
```

---

## Issue を作成する（Issue が存在しない場合）

**タイミング**: 作業開始時に対応 Issue がまだ存在しない場合

詳細な Issue 運用ルールは [`guides/development-policy/issue-operation-rules.md`](../../../guides/development-policy/issue-operation-rules.md) を参照。

### 手順 A: Issue の種別を確認

ユーザーに以下を確認する（まだ指定がなければ）：

```
どちらの Issue を作成しますか？
1. ProductBacklog Issue（複数フェーズ・複数日にわたる作業の親 Issue）
2. Task Issue（単発タスク・保守作業など、ProductBacklog が不要な作業）
3. 調査 Issue（技術調査・原因特定・要件調査など）
```

**ProductBacklog Issue の作成条件** — 以下をすべて満たす場合のみ：
- 複数のフェーズ（2つ以上）にわたる作業
- 完了まで複数日かかる見込み
- 他の Issue・作業との依存関係がある

### 手順 B: タイトルの決定

命名規則: `{type}({scope}): {タイトル}`

**type 一覧**（種別ラベル・type ラベルとの対応）:

| type | 用途 | 種別ラベル | type ラベル |
|------|------|-----------|------------|
| `feat` | 新機能の追加 | `task`（ProductBacklog なら `product-backlog`） | `type: feat` |
| `fix` | バグ修正 | `bug` | `type: fix` |
| `design` | 設計フェーズ（Task Issue のみ） | `task` | `type: design` |
| `test` | テストの追加・修正 | `task` | `type: test` |
| `docs` | ドキュメントの追加・更新 | `task` | `type: docs` |
| `refactor` | リファクタリング | `task` | `type: refactor` |
| `chore` | ビルド設定・ツール変更 | `task` | `type: chore` |
| `perf` | パフォーマンス改善 | `task` | `type: perf` |
| `ci` | CI/CD 設定の変更 | `task` | `type: ci` |

**調査 Issue**: type は `investigate` 固定 / 種別ラベル: `task` / 補助ラベル: `investigation`

> **Issue Type は使用しない**: GitHub Organization の Issue Type 機能は運用せず、すべてラベルで管理する。

**scope 一覧**（`system: *` ラベルと一致）:

| scope | 対象 | 対応する system ラベル |
|-------|------|---------------------|
| `task` | タスク管理 | `system: task` |
| `english` | 英語学習 | `system: english` |
| `common` | 横断的・共通基盤 | `system: common` |
| `content-sales` | 自作ツール等の販売管理 | `system: content-sales` |
| `deps` | 依存パッケージ | `system: deps` |

> 今後 life-os の領域が増えたら、scope と `system: *` ラベルを `guides/development-policy/issue-operation-rules.md` と `scripts/setup-github-labels.sh` に追加する。

### 手順 C: Issue 本文の収集

ユーザーから以下の情報を収集する（未提供の項目のみ確認する）。

**ProductBacklog Issue の必須項目**:
1. **概要**: この取り組みで実現したいことを 2〜3 行で記載
2. **要件説明**: 要件テキストまたは要件ドキュメントへのリンク
3. **スコープ**: 対象（含む）と対象外（含まない）
4. **影響範囲**: 変更によって影響を受けるコンポーネント・機能
5. **依存関係**: 依存する Issue・依存される Issue
6. **Task Issue チェックリスト**: フェーズ分けされた Task Issue の一覧
7. **完了条件**: 完了と判断する基準

**Task Issue の必須項目**:
1. **背景**: この Issue が生まれた経緯や状況
2. **課題**: 現状の問題点や達成したいこと
3. **影響範囲**: 変更によって影響を受けるコンポーネント・ファイル
4. **対応方針**: 採用する方針と、その方針を選んだ理由（理由必須）
5. **対応詳細**: 具体的な作業内容

**調査 Issue の必須項目**:
1. **背景**: この調査が必要になった経緯や状況
2. **課題**: 何を調査するのか、調査の目的
3. **影響範囲**: 調査対象のコンポーネント・ファイル・機能
4. **調査方法**: どのように調査するか
5. **調査詳細**: 調査した内容（作成時は空でも可）

### 手順 D: Issue 作成コマンドの実行

収集した情報をもとに `gh issue create` コマンドを実行する（`--repo masaya-ueki/life-os`）。

**ProductBacklog Issue の作成例**:

```bash
gh issue create \
  --repo masaya-ueki/life-os \
  --title "{type}({scope}): {タイトル}" \
  --label "product-backlog,type: feat,system: {scope}" \
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
\`\`\`

## 完了条件

- [ ] 全 Task Issue がクローズされている
- [ ] {その他の完了条件}
EOF
)"
```

**Task Issue の作成例（単発タスク）**:

```bash
gh issue create \
  --repo masaya-uoki/life-os \
  --title "{type}({scope}): {タイトル}" \
  --label "no-product-backlog,type: {type},system: {scope}" \
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

**調査 Issue の作成例**:

```bash
gh issue create \
  --repo masaya-ueki/life-os \
  --title "investigate({scope}): {タイトル}" \
  --label "task,investigation,type: investigate,system: {scope}" \
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

Issue が作成されたら URL を表示し、ProductBacklog Issue の場合は Task Issue（Sub-issue）の作成・紐づけを案内する。

---

## ステップ0: Issue を読む

**タイミング**: 作業開始時（必須）

### 実行コマンド

```bash
gh issue view {issue番号} --repo masaya-ueki/life-os \
  --json title,body,number,state,labels
```

> **注意**: `gh issue view` をオプションなしで実行すると、Projects Classic 非推奨の警告によりエラーになる場合がある。`--json` オプションで取得フィールドを指定することで回避できる。
> **labels も必ず取得**: 種別（`bug` / `task` / `product-backlog` / `on-hold`）・type・system の各分類軸を把握するため。

### 把握する内容

- **ラベル**: 種別ラベル（`bug` / `task` / `product-backlog` / `on-hold` のいずれか・必須）、`type: *`（必須・1件）、`system: *`（推奨・0〜複数件）、補助ラベル
- **背景**: この Issue が生まれた経緯・状況
- **課題**: 解決すべき問題・達成目標
- **対応方針**: 採用する方針とその理由
- **対応詳細**: 具体的な作業内容

### 出力形式

```
【Issue #XXX 概要】
- 目的: {1行で目的}
- ラベル: {種別 / type / system / 補助 を含むラベル一覧}
- 主な作業: {箇条書き2〜3点}
- 完了条件: {何ができたら完了か}
```

---

## ステップ1: ブランチ作業内容をまとめる

**タイミング**: 作業開始時（必須）

### 実行コマンド

```bash
# 現在のブランチと状態を確認
git branch --show-current
git status

# main からの差分コミットを確認
git log main..HEAD --oneline

# 変更ファイルの概要を確認
git diff main..HEAD --stat
```

### 把握する内容

- **現在のブランチ名**: `feat/issue-XXX-XXX` 形式であることを確認
- **コミット済みの変更**: 何がすでに実装されているか
- **未コミットの変更**: 作業途中のファイルがないか

### 出力形式

```
【ブランチ状況】
- ブランチ: {ブランチ名}
- コミット済み: {件数}件
  - {コミットメッセージ1}
  - {コミットメッセージ2}
- 未コミット: {あり/なし}
- 主な変更ファイル: {ファイル名リスト}
```

---

## ステップ2: 都度記録する

**タイミング**: 作業中の任意タイミング（重要な判断・決定のたびに）

### 内部メモとして記録する（Claude Memory）

重要な決定・判断・気づきは Claude の永続メモリ（`/root/.claude/projects/*/memory/`）に記録する。

記録すべき内容：
- 採用した設計の理由（なぜこのアプローチを選んだか）
- 調査した結果（何が分かったか）
- 断念した案とその理由
- 次のセッションで引き継ぐべきコンテキスト

### Issue コメントとして記録する（人間への共有）

ユーザーから依頼があった場合、または重要な節目（設計決定・問題発覚・解決策確定）のタイミングで Issue にコメントを書き込む。

```bash
gh issue comment {issue番号} \
  --repo masaya-ueki/life-os \
  --body "$(cat <<'EOF'
## 作業ログ {yyyy-MM-dd}

### 実施内容
- {作業内容1}
- {作業内容2}

### 決定事項
- {決定内容}: {理由}

### 次のステップ
- {次にやること}
EOF
)"
```

---

## ステップ3: Issue に最終結果を書く

**タイミング**: PR 作成後・作業完了時（必須）

### PR との紐付けコメントを書く

```bash
gh issue comment {issue番号} \
  --repo masaya-ueki/life-os \
  --body "$(cat <<'EOF'
## 対応完了

### 実施内容
- {完了した作業の箇条書き}

### PR
- #{PR番号}: {PRタイトル}

### 変更ファイル
- {変更したファイルパス}: {変更内容の概要}

### 確認事項
- [ ] 動作確認済み
- [ ] レビュー依頼済み
EOF
)"
```

### Issue の「結果」セクションを更新する（可能な場合）

Issue 本文に `## 結果` セクションがある場合は更新する：

```bash
# 現在の Issue 本文を取得して結果セクションを書き込む
gh issue edit {issue番号} \
  --repo masaya-ueki/life-os \
  --body "$(gh issue view {issue番号} --repo masaya-ueki/life-os --json body -q .body \
    | sed 's|<!-- Issue クローズ後に記載 -->|{最終結果の内容}|')"
```

---

## 使用例

### 例1: Issue がない状態から作業開始

```
ユーザー: 新しい英語学習機能を追加したいので Issue を作って作業を始めて

Claude:
[Issue 作成] どちらの Issue を作成しますか？...
→ ユーザーと対話して gh issue create を実行
Issue #55 を作成しました: https://github.com/masaya-ueki/life-os/issues/55

[ステップ0] Issue #55 を読み込みます...
[ステップ1] ブランチ状況を確認します...

【Issue #55 概要】
- 目的: 英語学習機能の追加
- 主な作業: ...
```

### 例2: Issue が既存の状態から作業開始

```
ユーザー: Issue #42 で作業を始めて

Claude:
[ステップ0] Issue #42 を読み込みます...
[ステップ1] ブランチ状況を確認します...

【Issue #42 概要】
...
```

### 例3: 途中経過を記録

```
ユーザー: 今の進捗を Issue に書いて

Claude: Issue #42 に作業ログを書き込みます...
コメントを書き込みました: https://github.com/masaya-ueki/life-os/issues/42#issuecomment-XXXXXXXX
```

### 例4: 作業完了時

```
ユーザー: PR 作成して Issue に結果を書いて

Claude:
[PR を作成] PR #43 を作成しました。

[ステップ3] Issue #42 に最終結果を書き込みます...
結果を書き込みました。
```

---

## 注意事項

- **Issue 番号の確認**: 作業開始時に必ず Issue 番号をユーザーに確認する（ブランチ名 `feat/issue-XXX-*` から推測可能）
- **ラベル**: ProductBacklog Issue は `product-backlog`、単発 Task Issue は `no-product-backlog`、調査 Issue は `investigation`。加えて `type: *`（必須）と `system: *`（推奨）を付与する
- **コメントの日本語統一**: Issue コメントはすべて日本語で記述する
- **過度な記録を避ける**: すべての小さな変更を Issue に書く必要はない。重要な判断・節目のみ記録する
- **内部メモと Issue の使い分け**: Claude 自身への引き継ぎは内部メモ（memory）、人間への共有は Issue コメント

---

**このスキルは Issue の起票から完了報告まで、作業ライフサイクル全体に適用してください。**
