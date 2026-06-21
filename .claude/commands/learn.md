---
name: learn
description: 直近セッションの設計判断・問題解決から観測を抽出し、instinct YAML として蓄積する。セッション末尾や /clear 前に実行する。
---

# /learn — 観測 → instinct 蓄積

セッションの設計判断・問題解決・PR レビューから「繰り返し価値のある気づき」を抽出し、instinct YAML として保存します。

> **このコマンドは [continuous-learning スキル](./../skills/continuous-learning/SKILL.md) の一部です。**

---

## 実行タイミング

- タスク完了 / Issue クローズ直後
- `/clear` によるコンテキストリセット直前
- 重要な設計判断をした直後

---

## 処理手順

### ステップ 1: 観測候補の抽出

以下のソースから「繰り返し価値のある気づき」を探します：

```bash
git log main..HEAD --oneline        # 今セッションのコミット
git diff main..HEAD --stat          # 変更ファイル概要
```

加えて直近の会話履歴から：
- 意思決定の根拠（「なぜ〇〇ではなく△△にしたか」）
- 解決したトラブルのパターン
- レビューで指摘された / 気づいた設計の問題
- 「次回も同じようにすべき」と判断した行動

### ステップ 2: 既存 instinct のスキャン

```
/home/dev/.claude/projects/-home-dev-workspace-life-os-main/memory/instincts/
```

配下の YAML をスキャンし、同じ ID が既に存在するか確認します。

- **既存 ID あり**: confidence を次の離散段階へ昇格（0.3→0.5→0.7→0.9）、`observation_count` +1、evidence 追記
- **既存 ID なし**: 新規 instinct として confidence 0.3 から作成

### ステップ 3: 候補提示（ユーザー確認）

抽出した候補を以下の形式で提示します：

```
--- 観測候補 #1 ---
ID: architecture-public-py-boundary
domain: architecture
trigger: 新しい領域間連携を実装する場合
action: 他領域の内部パッケージを直接 import せず、public.py 経由でアクセスする
confidence: 0.5（既存 0.3 から昇格）
evidence: PR #42（境界違反を修正したコミット）

保存しますか？ [y/n/edit]
```

ユーザーが `edit` を選択した場合、trigger / action / domain を対話的に修正します。

### ステップ 4: YAML 書き込み

承認された instinct を保存します。ディレクトリが存在しない場合は自動作成します：

```
/home/dev/.claude/projects/-home-dev-workspace-life-os-main/memory/instincts/
├── README.md            # 初回作成時に生成
├── <domain>/
│   └── <id>.yaml        # 保存先
└── _archive/
```

**保存ファイル名**: `<id から domain プレフィックスを除いた部分>.yaml`
（例: `id: architecture-public-py-boundary` → `architecture/public-py-boundary.yaml`）

---

## instinct YAML フォーマット

```yaml
id: <domain>-<verb>-<object>
trigger: "<いつ適用するか>"
action: "<何をするか>"
domain: <domain>
confidence: 0.3 | 0.5 | 0.7 | 0.9
scope: project
evidence:
  - date: YYYY-MM-DD
    ref: "<PR #/コミット ID/Issue #/会話の要旨>"
source: session-observation | user-correction | pr-review
created_at: YYYY-MM-DD
last_updated: YYYY-MM-DD
observation_count: <int>
evolved_to: null
```

---

## ドメイン一覧

| ドメイン | 学習対象 |
|---------|---------|
| `task` | タスク管理の設計パターン |
| `english` | 英語学習システム設計 |
| `media` | メディア管理パターン |
| `travel` | 旅行管理パターン |
| `content-sales` | 販売管理パターン |
| `git-workflow` | Git / PR 運用 |
| `claude-workflow` | Claude Code の使い方・スキル運用 |
| `testing` | テスト戦略（pytest / Docker）|
| `architecture` | アーキテクチャ境界・設計判断 |

---

## 機密情報チェック

保存前に必ず確認：

- [ ] `evidence.ref` に PR / コミット番号のみ（認証情報やコード片を含まない）
- [ ] `trigger` `action` に実値（ファイル名・URL・キー値）が入っていない
- [ ] `domain: security` の場合、特に慎重に確認

---

## 実行例

```
/learn

→ [観測抽出中...]
→ git log, git diff をスキャン

--- 観測候補 #1 ---
ID: architecture-public-py-boundary（既存あり、0.3 → 0.5 昇格）
...

--- 観測候補 #2 ---
ID: testing-docker-compose-run-rm（新規、0.3）
trigger: テストや境界検査を実行する場合
action: ローカルに Python/uv を導入せず docker compose run --rm test / lint を使う
...

2 件の候補を見つけました。どれを保存しますか？
```
