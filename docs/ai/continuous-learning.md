# Continuous Learning — 思想設計

> **スキル定義**: [.claude/skills/continuous-learning/SKILL.md](../../.claude/skills/continuous-learning/SKILL.md)
> **設計根拠**: [ADR-0010](../adr/0010-continuous-learning-instinct-based.md)

---

## 1. 動機

Claude Code のセッションはコンテキストが `/clear` でリセットされます。
一方、開発中の気づき（「この境界をこう越えると壊れる」「Docker 経由でテストしないと本番と乖離する」）は再利用価値が高く、セッションをまたいで蓄積されるべきです。

auto memory は「事実・人物像」を記録しますが、「行動パターン（次回も同じ判断をすべき再発性の知見）」は別の概念です。
continuous-learning はこの「行動パターン」を **instinct** として分離し、confidence スコアで管理します。

---

## 2. 核となる考え方

### 2-1. observation → instinct → team artifact の進化フロー

```
セッション中の気づき（observation）
    │
    ▼ /learn
instinct YAML（personal scope）
    │ confidence 蓄積・再観測
    ▼ /evolve
team artifact（.claude/skills / .claude/rules / docs/adr）
    ← Git 管理・PR
```

一度の観測はノイズの可能性がある。複数回観測（同一 ID の再登場）で confidence が上がり、十分高まったとき初めて「組織の知識」へ昇華する設計にした。

### 2-2. なぜ memory と分けるか

| 仕組み | 記録内容 | 進化 |
|--------|---------|------|
| auto memory | 事実・人物像（変わらない） | なし（上書き更新） |
| instinct | 行動パターン（再発する） | confidence → 昇華 → team scope |

memory は「知っている事実」、instinct は「次回こうすべき判断基準」です。
二重管理を避けるため、instinct として記録したものは memory には書かない。

### 2-3. 手動トリガー設計の意図

自動観測（PostToolUse hook 等）は将来 v2 で導入を検討しますが、MVP では意図的に手動にしました。

理由：
- 自動化すると「低品質な観測」が大量に蓄積され、検索精度が落ちる
- 「重要な気づき」かどうかの判断はセッション末尾に人間が行うべき
- `/clear` 前の `/learn` という運用リズムを確立してから自動化する

---

## 3. Confidence スコアリングの設計

### 3-1. 離散 4 値（0.3 / 0.5 / 0.7 / 0.9）を選んだ理由

連続値（0.0〜1.0）にすると「0.63 と 0.65 はどう違うか」が曖昧になります。
4 段階の離散値にすることで：
- 昇華のしきい値（≥ 0.7）が明確
- ユーザーが直感的に理解できる（「暫定」「中程度」「強い」「ほぼ確定」）
- 昇格条件が機械的に判定できる

### 3-2. 登録時の初期 confidence

新規 instinct の初期値は `source` によって決まる：

| source | 初期 confidence |
|--------|----------------|
| `session-observation` | 0.3（主観的な気づき。再観測で検証） |
| `pr-review` | 0.5（PR プロセスで外部検証済み） |
| `user-correction` | 0.3（訂正は降格イベント。新規でも暫定スタート） |

### 3-3. 昇格条件（観測回数 × source 種別）

再観測のたびに必ず上がる単純ルールから、**観測回数と外部検証の有無**を組み合わせた条件に拡張しました（ECC の source 重み付け設計を参考に採用）：

| 現在 | 次段階 | 必要条件（すべて満たすこと） |
|------|--------|---------------------------|
| 0.3 | 0.5 | ① `observation_count ≥ 2` |
| 0.5 | 0.7 | ① `observation_count ≥ 3` かつ ② evidence に `pr-review` または `user-correction` が 1 件以上 |
| 0.7 | 0.9 | ① `observation_count ≥ 4` かつ ② evidence に `user-correction` が 0 件 |

**意図**:
- `0.3 → 0.5`: 「1 度見た」から「繰り返し確認できた」へ。
- `0.5 → 0.7`: セッション内の主観的気づきだけでは上がらない。PR レビューや訂正という外部根拠が必要。
- `0.7 → 0.9`: 一度も訂正されていない実績で「ほぼ確定」の信頼性を担保。

### 3-4. 同一 ID 判定

`id:` フィールドの完全一致のみを「同一 ID」とみなします。セマンティック類似での自動マッチングは行いません。Claude が候補を提示し、ユーザーが再利用か新規かを決定します。これにより `observation_count` の増減が曖昧にならず、confidence の蓄積が確実に追跡できます。

---

## 4. 昇華先の選択基準

| 昇華先 | いつ選ぶか |
|--------|----------|
| `.claude/rules/<name>.md` | 常時適用すべきコーディング規約・チェック事項 |
| `.claude/skills/<name>/SKILL.md` | 複数ステップのワークフロー（手順が伴う） |
| `.claude/commands/<name>.md` | 1 コマンドで起動する定型作業 |
| `docs/adr/XXXX-*.md` | 採用根拠・却下選択肢の記録（重大な設計判断） |

**重複禁止**: 昇華後は元 instinct を `_archive/` に移動し、同じ知見が 2 箇所に存在しないようにします。

---

## 5. Personal → Team の境界

| スコープ | 保存場所 | Git 管理 |
|---------|---------|---------|
| personal | `/home/dev/.claude/projects/-home-dev-workspace-life-os-main/memory/instincts/` | なし |
| team | `.claude/skills/` `.claude/rules/` `docs/adr/` | あり（PR 経由） |

personal scope は個人の観測ノートです。team scope への昇華はユーザーの意思決定と PR レビューを経て行います。

---

## 6. ドメイン分類（life-os 版）

ドメイン追加は本ファイルと `.claude/skills/continuous-learning/SKILL.md` を同時更新する PR が必要です。

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

---

## 7. 段階導入計画

### v1（現在）
- 手動トリガー（`/learn` `/instinct-status` `/evolve`）
- project scope のみ
- ユーザー承認フロー

### v2（将来 Issue 化を推奨）
- Stop hook で `/learn` を半自動発火
- PostToolUse hook でリアルタイム観測
- confidence の自動 decay（30 日更新なし → -0.1）

### v3（将来）
- Background Haiku agent によるパターン抽出
- グローバルスコープへの拡張（複数リポジトリをまたぐ知見）
