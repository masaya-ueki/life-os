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

### ステップ 1.5: 重大度チェック（instinct 化 vs 即タスク化の分岐）

観測候補を以下の基準でスクリーニングします。**いずれか 1 つ該当する場合は instinct に登録せず、`issue-memory` スキルで即タスク化します。**

| 重大度 | 判定基準 | 処理 |
|--------|---------|------|
| **ERROR 相当** | プログラムの実行エラー・クラッシュにつながる可能性がある / テスト・lint が失敗したまま放置されている / 本番データの破損・消失リスクがある | `issue-memory` で Bug Issue を即起票 |
| **境界違反相当** | `.importlinter` ルール違反がある / `public.py` を介さない領域間 import がある | `issue-memory` で Bug Issue を即起票 |
| **セキュリティ相当** | 認証・認可の漏れ / 機密情報の露出リスクがある | `issue-memory` で Task Issue を即起票 |

上記に該当しない場合のみ、ステップ 2 以降の instinct 登録フローへ進みます。

> **note**: タスク化後、パターンが修正・解決されたら、その経験を instinct として再入力してよい。
> その場合は `pr-review` が evidence に入るため初期 confidence は **0.5** になる。

### ステップ 2: 既存 instinct のスキャン

```
/home/dev/.claude/projects/-home-dev-workspace-life-os-main/memory/instincts/
```

配下の YAML をスキャンし、**`id:` フィールドの完全一致**で既存 instinct を探します。

**同一 ID 判定ルール**:
- セマンティック類似による自動マッチングは行わない
- `id:` が一字一句同じファイルのみを「既存あり」と判定する
- ID が近い（似ている）ファイルが見つかった場合は**候補として提示**し、ユーザーに再利用か新規かを選ばせる

**スキャン結果の処理**:
- **既存 ID あり（ユーザーが再利用を選択）**: 昇格条件を確認し、条件を満たす場合のみ confidence を次段階へ昇格、`observation_count` +1、evidence 追記
- **既存 ID なし / ユーザーが新規を選択**: source に応じた初期 confidence で新規作成（`session-observation` → 0.3、`pr-review` → 0.5）

### ステップ 3: 候補提示（ユーザー確認）

抽出した候補を以下の形式で提示します：

```
--- 観測候補 #1 ---
ID: architecture-public-py-boundary
domain: architecture
trigger: 新しい領域間連携を実装する場合
action: 他領域の内部パッケージを直接 import せず、public.py 経由でアクセスする
source: pr-review
confidence: 0.5（既存 0.3 から昇格）
  昇格条件チェック: observation_count=2 ✓ → 0.3→0.5 昇格可
evidence: PR #42（境界違反を修正したコミット）

保存しますか？ [y/n/edit]
```

昇格しない場合の例：
```
--- 観測候補 #2 ---
ID: architecture-public-py-boundary（既存あり、observation_count=3）
confidence: 0.5（昇格不可）
  昇格条件チェック（0.5→0.7）: observation_count=3 ✓ / pr-review または user-correction の evidence: なし ✗ → 昇格不可
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
→ [重大度チェック] 全候補: ERROR/境界違反/セキュリティ相当なし → instinct フローへ

--- 観測候補 #1 ---
ID: architecture-public-py-boundary（既存あり）
domain: architecture
trigger: 新しい領域間連携を実装する場合
action: 他領域の内部パッケージを直接 import せず、public.py 経由でアクセスする
source: pr-review
confidence: 0.5（現在 0.3）
  昇格条件チェック（0.3→0.5）: observation_count=2 ✓ → 昇格可
evidence: PR #42（境界違反を修正したコミット）

保存しますか？ [y/n/edit]

--- 観測候補 #2 ---
ID: testing-docker-compose-run-rm（新規）
domain: testing
trigger: テストや境界検査を実行する場合
action: ローカルに Python/uv を導入せず docker compose run --rm test / lint を使う
source: session-observation
confidence: 0.3（初回登録）

保存しますか？ [y/n/edit]

2 件の候補を処理しました。
```
