---
name: close-task
description: 作業クローズの標準ワークフロー。Issue クローズ（テンプレート記録 + close）・気づき/拡張を continuous-learning に蓄積（confidence ≥ 0.7 は issue-memory でタスク化）・worktree とローカルブランチ削除・ProductBacklog 状況/次タスク提示を一括処理する。
argument-hint: "[Issue番号]"
allowed-tools: Bash, Read, Glob, Skill
---

# close-task スキル

作業完了後のクローズ処理を標準化するスキルです。
Issue のクローズから環境クリーンアップ・知識蓄積・次タスク提示まで 5 ステップで一括処理します。

---

## トリガー条件

以下のいずれかの場合に使用：

- ユーザーが `/close-task` または `/close-task <Issue番号>` を実行した場合
- ユーザーが「作業をクローズして」「Issue を閉じて後片付けして」と依頼した場合
- PR 作成後・作業完了後に後処理をまとめて行いたい場合

---

## ワークフロー概要

```
ステップ1: 前提確認（Issue番号・ブランチ・worktreeパスの自動検出）
     ↓
ステップ2: Issue クローズ（テンプレートでコメント記録 → close）
     ↓
ステップ3: 気づき・拡張の収集 → /learn で instinct 化 → confidence ≥ 0.7 は issue-memory でタスク化
     ↓
ステップ4: worktree + ローカルブランチ削除
     ↓
ステップ5: ProductBacklog 状況・次タスクの提示
```

---

## ステップ1: 前提確認

**タイミング**: スキル実行の最初に必ず行う。

### Issue 番号の解決

引数で指定された番号を優先する。未指定の場合はブランチ名から推測する。

```bash
# 現在のブランチ名を取得
git branch --show-current
# 例: feat/issue-123-add-feature → Issue 番号 = 123

# Issue 情報を取得
gh issue view <N> --repo masaya-ueki/life-os \
  --json title,body,number,state,labels
```

### ブランチ・worktree の状態確認

```bash
# main からの差分コミット
git log main..HEAD --oneline

# 変更ファイル一覧
git diff main..HEAD --stat

# worktree 一覧（現在地の確認）
git worktree list

# 未プッシュコミットの確認
git status
```

### ガード条件（エラー終了）

- `main` ブランチで実行している場合 → 「main では実行できません。作業ブランチに切り替えてください。」と伝えて終了
- Issue が既に `closed` の場合 → 「Issue #XXX はすでにクローズされています。ステップ4（環境削除）から続けますか？」と確認

### 出力形式

```
【クローズ対象の確認】
- Issue #XXX: {タイトル}
- ブランチ: {ブランチ名}
- worktree: {絶対パス}
- コミット: {件数}件
  - {コミットメッセージ一覧}
- 変更ファイル: {ファイル名一覧}
- 未プッシュ: {あり/なし}
- PR: #{PR番号}（未作成の場合は「なし」）

上記の内容でクローズ処理を進めます。よろしいですか？
```

---

## ステップ2: Issue クローズ

**タイミング**: ステップ1の確認後。

### クローズコメントテンプレート

コミット履歴・変更ファイル一覧を参照してテンプレートを自動生成し、ユーザーに確認してから記録する。

```markdown
## 対応完了

### 実施内容

- {コミット履歴から生成した箇条書き}

### 成果物

| ファイル / リソース | 変更内容 |
|-------------------|---------|
| {パス} | {変更概要} |

### PR

- #{PR番号}: {PRタイトル}
  （PR がない場合は「PR なし（直接クローズ）」と記載）

### 動作確認

- [ ] 実装確認済み
- [ ] レビュー依頼済み（PR がある場合）

### 派生 Issue

- {ステップ3 で起票された Issue があれば「#XXX: タイトル」の形式で列記}
  （なければ「なし」）
```

### 実行コマンド

```bash
REPO="masaya-uuki/life-os"

# 1. Issue 本文の「## 結果」セクションを更新（テンプレートにセクションがある場合）
CURRENT_BODY=$(gh issue view <N> --repo "$REPO" --json body -q .body)
# <!-- Issue クローズ後に記載 --> または <!-- 完了後に記載 --> を実際の内容に置換
UPDATED_BODY=$(echo "$CURRENT_BODY" | sed 's|<!-- Issue クローズ後に記載 -->|{実施内容の要約}|' \
                                    | sed 's|<!-- 完了後に記載 -->|{実施内容の要約}|')
gh issue edit <N> --repo "$REPO" --body "$UPDATED_BODY"

# 2. クローズコメントを追記
gh issue comment <N> --repo "$REPO" --body "$(cat <<'EOF'
{上記テンプレートの内容}
EOF
)"

# 3. Issue をクローズ
gh issue close <N> --repo "$REPO" --reason completed
```

---

## ステップ3: 気づき・拡張の収集 → continuous-learning → issue-memory

**タイミング**: ステップ2の後。

作業中に得た「気づき（別途対応が必要な事項）」と「拡張案（スコープ外の改善・機能追加）」を収集し、
`/learn`（`continuous-learning` スキル）で instinct として蓄積する。
confidence ≥ 0.7 の instinct は `issue-memory` スキルで Task Issue を起票してタスク化する。

### 3-1. ユーザーへの確認（気づき）

```
作業中に気づいた点・改善候補はありますか？
（例: バグ、技術的負債、設定漏れ、ドキュメント不足、設計の課題）
あれば内容を教えてください。
複数ある場合はまとめて教えてください。
なければ「なし」と回答してください。
```

### 3-2. ユーザーへの確認（拡張）

```
今後の拡張・改善として見込まれる案はありますか？
（例: 機能追加、パフォーマンス改善、対応範囲の拡大）
あれば内容を教えてください。
なければ「なし」と回答してください。
```

### 3-3. /learn で instinct 化

気づき・拡張のいずれかが「あり」だった場合、`continuous-learning` スキルの `/learn` を実行する。

収集した内容を observation として提示し、instinct YAML の候補を生成してユーザーに承認を求める。

```
/learn を実行します。
今回の作業（Issue #XXX）から以下の気づき・拡張案を observations として抽出しました：

【気づき】
- {気づき1}: {内容}
- {気づき2}: {内容}

【拡張案】
- {拡張案1}: {内容}

これらを instinct として蓄積します。confidence の初期値を決定してください。
```

`/learn` の詳細な動作は `.claude/skills/continuous-learning/SKILL.md` を参照。

### 3-4. confidence ≥ 0.7 の instinct を issue-memory でタスク化

`/learn` 完了後、承認された instinct の中で **confidence ≥ 0.7** のものが存在する場合、
`issue-memory` スキルを呼び出して Task Issue を起票する。

```
以下の instinct は confidence ≥ 0.7 のため、Task Issue としてバックログに積みます。

- {instinct ID}: {trigger} / {action}
  → issue-memory で Task Issue を起票します

よろしいですか？
```

`issue-memory` での起票時のラベル構成（参考）：

```
ラベル: no-product-backlog, type: {type}, system: {scope}
タイトル: {type}({scope}): {instinct の action を 1 文で表したタイトル}
```

気づき・拡張が両方「なし」の場合はこのステップ全体をスキップする。

---

## ステップ4: worktree + ローカルブランチ削除

**タイミング**: ステップ3の完了後（Issue 起票が終わってから削除）。

### 実行コマンド

```bash
# 現在のブランチ名とworktreeパスを取得
BRANCH=$(git branch --show-current)
WORKTREE_PATH=$(git rev-parse --show-toplevel)
MAIN_PATH=$(git worktree list | head -1 | awk '{print $1}')

echo "削除対象:"
echo "  worktree: $WORKTREE_PATH"
echo "  branch:   $BRANCH"
echo "  main:     $MAIN_PATH"
```

削除前にユーザーへ確認：

```
以下を削除します。よろしいですか？
- worktree: {WORKTREE_PATH}
- ローカルブランチ: {BRANCH}
```

```bash
# worktree 削除（main から実行）
git -C "$MAIN_PATH" worktree remove "$WORKTREE_PATH" --force
git -C "$MAIN_PATH" worktree prune

# ローカルブランチ削除（マージ済み想定）
git -C "$MAIN_PATH" branch -d "$BRANCH"
```

### 注意事項

- `git branch -d` が失敗した場合（未マージ）は自動的に `-D` を実行せず、ユーザーに確認する
- worktree 削除後はそのシェルセッションは無効になるため、ユーザーに main へ移動するよう案内する

```
✅ worktree を削除しました。
このシェルは無効になりました。main checkout に移動してください：
  cd {MAIN_PATH}
```

---

## ステップ5: ProductBacklog 状況・次タスクの提示

**タイミング**: 最終ステップ。クローズ処理の締めくくりとして、
「次に何に着手すべきか」を提示してセッションを終える。

### 5-1. 親 ProductBacklog の特定

クローズした Issue がどの ProductBacklog（`product-backlog` ラベルの親 Issue）の
サブイシューかを GraphQL で逆引きする。

```bash
REPO="masaya-ueki/life-os"
OWNER="masaya-ueki"
NAME="life-os"

# クローズした Issue #N の親 ProductBacklog を取得
gh api graphql -f query='
query($owner:String!,$name:String!,$num:Int!){
  repository(owner:$owner,name:$name){
    issue(number:$num){
      parent { number title state }
    }
  }
}' -F owner="$OWNER" -F name="$NAME" -F num=<N>
```

### 5-2. 親 ProductBacklog の進捗と次タスク

親が特定できた場合、そのサブイシュー一覧から進捗（完了 / 全体）と
**次のタスク = 最若番の open サブイシュー** を求める。

```bash
gh api graphql -f query='
query($owner:String!,$name:String!,$num:Int!){
  repository(owner:$owner,name:$name){
    issue(number:$num){
      title
      subIssues(first:100){
        totalCount
        nodes{ number title state }
      }
    }
  }
}' -F owner="$OWNER" -F name="$NAME" -F num=<親ProductBacklog番号>
```

- **進捗**: `state == "CLOSED"` のサブイシュー数 / `totalCount`
- **次タスク**: `state == "OPEN"` のサブイシューのうち最も番号が小さいもの

### 5-3. ProductBacklog 全体の状況

リポジトリ全体の open な ProductBacklog 一覧も併せて提示する。

```bash
gh issue list --repo "$REPO" --label "product-backlog" --state open \
  --json number,title,labels --limit 20
```

親が特定できなかった場合（単発 Task Issue 等）は、`no-product-backlog` を除く
open タスクから次の着手候補を提示する。

```bash
gh issue list --repo "$REPO" --label "task" --state open \
  --json number,title --limit 10
```

### 出力形式

```
【ProductBacklog 状況】
- 全体の open ProductBacklog: {件数}件
  - #XXX: {タイトル}（進捗 {完了}/{全体}）

- 今回クローズした Issue #N の親: #XXX「{タイトル}」
  - 進捗: {完了}/{全体} 完了
  - 残タスク: {open サブイシューの番号・タイトル一覧}

【次のタスク】
- #ZZZ: {タイトル}
  （理由: 親 ProductBacklog #XXX の最若番 open サブイシュー）
```

> **注**: 親 ProductBacklog が無い・open サブイシューが残っていない場合は、
> 「この ProductBacklog は完了です」または「次のタスク候補なし」と明示する。

---

## 使用例

### 例1: 標準的なクローズ

```
ユーザー: /close-task

Claude:
[ステップ1] 前提を確認します...

【クローズ対象の確認】
- Issue #55: feat(common): close-task スキルを追加
- ブランチ: feat/issue-55-add-close-task-skill
- worktree: /home/dev/workspace/life-os/main/.claude/worktrees/feat+add-close-task-skill
- コミット: 1件
  - feat(common): close-task スキルを追加
- 変更ファイル: .claude/skills/close-task/SKILL.md
- PR: #56

上記の内容でクローズ処理を進めます。よろしいですか？

ユーザー: はい

[ステップ2] Issue #55 にクローズコメントを記録します...
Issue #55 をクローズしました。

[ステップ3] 気づき・拡張案を確認します...
作業中に気づいた点はありますか？

ユーザー: ステップ間の遷移条件をもっと明確にしたほうがいいかも

Claude:
/learn を実行します。以下の observation を instinct として追加します...
（confidence: 0.7 → issue-memory でタスク化を提案）

[ステップ4] worktree・ブランチを削除します...
✅ 完了しました。cd /home/dev/workspace/life-os/main へ移動してください。

[ステップ5] ProductBacklog 状況・次タスクを確認します...
```

### 例2: Issue 番号を明示して実行

```
ユーザー: /close-task 55
```

引数の `55` を Issue 番号として直接使用し、ブランチ名からの推測をスキップする。

---

## 注意事項

- **main ブランチでの実行禁止**: `main` で実行すると即座にエラー終了する
- **PR がない場合**: クローズコメントの「PR」欄は「PR なし（直接クローズ）」と記載し、そのままクローズする
- **Issue 本文に `## 結果` セクションがない場合**: `gh issue edit` をスキップし、クローズコメントのみ追記する
- **未プッシュコミットがある場合**: ステップ1で警告を表示し、push するかどうかをユーザーに確認する
- **日本語統一**: Issue コメント・新規 Issue の本文はすべて日本語で記述する
- **ステップの中断**: 気づき・拡張が両方「なし」の場合はステップ3の `/learn` をスキップしてよい
- **次タスクの提示（ステップ5）**: 親 ProductBacklog が無い・open サブイシューが残っていない場合は、無理に候補を挙げず「次のタスク候補なし」または「ProductBacklog 完了」と明示する

---

**このスキルは作業完了時（PR 作成後・タスク終了後）に実行してください。**
