---
name: continuous-learning
description: セッションを跨いだパターン学習を支援するスキル。observation → instinct 蓄積 → skill/command/rule/ADR への昇華という進化フローを、`/learn` `/instinct-status` `/evolve` の手動コマンドで運用する。life-os 固有の設計判断・トラブルシューティング知見を組織知化する。Use when: `/learn` `/instinct-status` `/evolve` を実行した場合、「学習させて」「instinct 確認」「昇華して」と依頼された場合、セッション末尾に重要な気づきがあり /clear 前に蓄積したい場合。Triggers on: /learn, /instinct-status, /evolve, 学習, instinct, 昇華, 知見蓄積.
---

# Continuous Learning（継続的学習）スキル

このスキルはセッションを跨いだパターン学習を支援します。observation → instinct 蓄積 → skill/command/rule/ADR への昇華という進化フローを、手動トリガーで運用します。

> **思想・設計の詳細**: [docs/ai/continuous-learning.md](../../../docs/ai/continuous-learning.md)
> **設計根拠**: [ADR-0010](../../../docs/adr/0010-continuous-learning-instinct-based.md)

---

## トリガー条件

以下のいずれかの場合に使用：

- ユーザーが `/learn` `/instinct-status` `/evolve` を実行した場合
- ユーザーが「学習させて」「instinct 確認」「昇華して」と依頼した場合
- セッション末尾に重要な気づきがあり、`/clear` 前に蓄積したい場合

---

## 全体ワークフロー

```
セッション活動
   │
   ▼ /learn 実行
観測抽出 → 候補提示 → ユーザー承認 → instinct YAML 保存
   │
   ▼ /instinct-status 実行
ドメイン別・confidence 順で一覧表示
   │
   ▼ /evolve 実行
クラスタリング → 昇華先提案 → ユーザー承認 → ファイル生成 → archive
   │
   ▼ コミット → PR
team scope（.claude/ または docs/adr/）に反映
```

---

## Instinct データモデル

各 instinct は 1 ファイル 1 YAML で保存します。

### スキーマ

```yaml
id: <domain>-<verb>-<object>           # kebab-case 必須
trigger: "<いつ適用するか>"             # 日本語の自然文
action: "<何をするか>"                  # 日本語の自然文（1 文で完結）
domain: <domain>                       # 下記ドメイン一覧から選択
confidence: 0.3 | 0.5 | 0.7 | 0.9      # 離散 4 値のみ（中間値禁止）
scope: project | global                # MVP は project のみ運用
evidence:
  - date: YYYY-MM-DD
    ref: "<PR #/コミット ID/Issue #/会話の要旨>"
source: session-observation | user-correction | pr-review
created_at: YYYY-MM-DD
last_updated: YYYY-MM-DD
observation_count: <int>
evolved_to: null | "<昇華先のファイルパス>"
```

### サンプル

```yaml
id: architecture-public-py-boundary
trigger: "新しい領域間連携を実装する場合"
action: "他領域の内部パッケージを直接 import せず、必ず対象領域の public.py 経由でアクセスする"
domain: architecture
confidence: 0.9
scope: project
evidence:
  - date: 2026-06-01
    ref: "PR #42 task 領域から media 領域への直接 import を public.py 経由に修正"
source: pr-review
created_at: 2026-06-01
last_updated: 2026-06-01
observation_count: 3
evolved_to: null
```

---

## ドメイン分類

| ドメイン | 学習対象 |
|---------|---------|
| `task` | タスク管理の設計パターン・運用ノウハウ |
| `english` | 英語学習システム設計・語彙管理 |
| `media` | メディア管理パターン |
| `travel` | 旅行管理パターン |
| `content-sales` | 販売管理パターン |
| `git-workflow` | Git / PR 運用 |
| `claude-workflow` | Claude Code 自体の使い方・スキル運用 |
| `testing` | テスト戦略（pytest / Docker）|
| `architecture` | アーキテクチャ境界・設計判断 |

ドメイン追加には PR が必要。本 SKILL.md と `docs/ai/continuous-learning.md §6` を同時更新します。

---

## Confidence スコアリング

| 値 | 名前 | 適用方針 |
|----|------|---------|
| 0.3 | 暫定 | `/instinct-status` で参照のみ。自動適用なし |
| 0.5 | 中程度 | 関連場面で考慮事項として提示 |
| 0.7 | 強い | `/evolve` の昇華候補。デフォルトで適用提案 |
| 0.9 | ほぼ確定 | 中核行動。skill / rule / ADR への昇華を強く推奨 |

### 増減ルール

| イベント | 変動 |
|---------|------|
| 同一 ID を再観測 | 次の離散段階へ昇格（0.3→0.5→0.7→0.9、最大 0.9 で頭打ち）＋ `observation_count` を +1 |
| ユーザーが訂正 | -0.2（`source: user-correction` の evidence 追加） |
| 30 日間更新なし | -0.1（MVP では未実装、`/instinct-status --orphaned` で表示のみ） |
| 昇華成功 | confidence 変更なし、`evolved_to` セット、`_archive/` に移動 |

---

## ファイル配置

### Personal scope（Git 管理外）

```
/home/dev/.claude/projects/-home-dev-workspace-life-os-main/memory/instincts/
├── README.md                                # フォーマット説明
├── task/
│   └── domain-driven-design.yaml
├── english/
│   └── vocabulary-dedup-on-save.yaml
├── git-workflow/
│   └── conventional-commit-scope.yaml
├── architecture/
│   └── public-py-boundary.yaml
└── _archive/
    └── 2026-06-01-evolved-to-architecture-rule.yaml
```

ディレクトリは初回 `/learn` 実行時に Claude が自動作成します。

### Team scope（Git 管理）

`/evolve` で生成される昇華先のみ Git 管理対象です。

| 昇華先 | 適合する instinct |
|--------|------------------|
| `.claude/skills/<name>/SKILL.md` | 複数ステップの再利用ワークフロー |
| `.claude/commands/<name>.md` | 単発で起動するコマンド |
| `.claude/rules/<name>.md` | 常時適用すべきコーディング規約 |
| `docs/adr/XXXX-*.md` | 重要な設計判断（ADR 必要性基準を満たす場合） |

---

## コマンドの責務

### `/learn` — 観測 → instinct 蓄積

**呼び出しタイミング**: セッション末尾、または重要な気づきがあった直後。`/clear` 前を推奨。

**処理内容**:
1. 直近の `git log main..HEAD` / `git diff main..HEAD` / 直近会話 / Issue コメントから観測候補を抽出
2. 各候補を提示し、新規 instinct or 既存 ID マッチを判定
3. ユーザー承認 → 該当ファイルへ書き込み

**非責務**: 全自動記録 / confidence の自動 decay

詳細は [.claude/commands/learn.md](../../commands/learn.md)

### `/instinct-status` — 可視化

**呼び出しタイミング**: 蓄積された instinct を確認したい時。

**処理内容**:
- personal scope 配下の YAML をスキャン
- ドメイン別グルーピング、confidence 降順表示
- フィルタ: `--domain` `--min-confidence` `--orphaned`

詳細は [.claude/commands/instinct-status.md](../../commands/instinct-status.md)

### `/evolve` — 昇華

**呼び出しタイミング**: confidence ≥ 0.7 の instinct が複数蓄積されたタイミング。

**処理内容**:
1. confidence ≥ 0.7 の instinct をクラスタリング
2. クラスタごとに昇華先（skill / command / rule / ADR）を提案
3. ユーザー承認 → ファイル生成 → 元 instinct を `_archive/` へ移動、`evolved_to` セット

**非責務**: 自動昇華 / 既存ファイルの上書き

詳細は [.claude/commands/evolve.md](../../commands/evolve.md)

---

## 運用ガイドライン

### 推奨運用パターン

```
セッション開始（タスク作業）
   │
   ▼ ... 設計判断・問題解決・PR レビューを経験 ...
   │
   ▼ タスク完了 / Issue クローズ
/learn を実行（重要な気づきを instinct 化）
   │
   ▼ /clear（コンテキストリセット）
   │
   ▼ 次のセッション
/instinct-status で蓄積を確認
   │
   ▼ 月 1 回程度
/evolve で confidence ≥ 0.7 の instinct を昇華
```

### 機密情報の取り扱い

- **絶対禁止**: パスワード・API キー・認証情報を instinct の `trigger` `action` `evidence` に書かない
- **OK**: 「Secrets Manager にこのプレフィックスで配置する」のような構造的パターン
- **NG**: 「API キーを `xxx` という値で設定する」のような実値

`/learn` 実行時に Claude が機密情報パターンを検知したら、その候補を除外して提示します。

### 機密情報チェックリスト

`/learn` `/evolve` 実行前に以下を確認:

- [ ] `evidence.ref` に PR / コミット番号や Issue 番号のみが入っているか（コード片や認証情報を含まない）
- [ ] `trigger` `action` に固有値（バケット名・テーブル名・ファイル実値）が入っていないか
- [ ] `domain` が `security` 関連の場合、特に注意

---

## 既存仕組みとの使い分け

| 仕組み | 用途 | 永続性 |
|--------|------|--------|
| **auto memory** (`memory/MEMORY.md`) | 事実・人物像 | personal |
| **continuous-learning instinct** | 行動パターン（再発） | personal → team（昇華） |
| **`.claude/rules/`** | 常時適用ルール（高 confidence） | team |
| **`.claude/skills/`** | ワークフロー（手順） | team |
| **`.claude/commands/`** | スラッシュコマンド | team |
| **`docs/adr/`** | 設計判断の根拠 | team |

**重複禁止**: 同じ知見を複数仕組みに書かない。`/evolve` した知見は元 instinct を archive に移動し、二重管理を避ける。

---

## 段階導入計画

### v1（本実装）

- このスキルと 3 コマンド（`/learn` `/instinct-status` `/evolve`）
- 手動トリガー
- ユーザーメモリ保存

### v2（別 Issue 化を推奨）

- Stop hook で `/learn` を半自動発火
- PreToolUse / PostToolUse hooks でリアルタイム観測
- confidence 自動 decay

### v3（将来）

- Background Haiku agent によるパターン抽出
- `/instinct-export` `/instinct-import`
- グローバルスコープへの拡張

---

## トラブルシューティング

### Q. instinct ディレクトリが見つからない

`/learn` を未実行の場合、ディレクトリは存在しません。`/learn` を 1 度実行すると自動作成されます。

### Q. confidence が一向に上がらない

同一 ID で再観測される必要があります。`/learn` 実行時に既存 instinct と同じ ID を生成するよう促してください（Claude が既存ファイルをスキャンしてマッチを試みる）。

### Q. `/evolve` で何も提案されない

confidence ≥ 0.7 の instinct が 2 件以上必要です。`/instinct-status --min-confidence 0.7` で件数を確認してください。

### Q. archive から instinct を復元したい

`_archive/<id>.yaml` を該当ドメインディレクトリに戻し、`evolved_to: null` に書き換えれば復元できます。ただし通常は再観測 → 新規 instinct を推奨します。

---

**このスキルは `/learn` `/instinct-status` `/evolve` の各コマンド実行時に自動的に適用されます。**
