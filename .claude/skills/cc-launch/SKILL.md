---
name: cc-launch
description: モード選択式で作業を起動するスキル。plan / simple / interactive / fable の 4 モードを引数で切り替え、Issue の自動読み込み・plan モードでの Sonnet/Opus 自動判定を行う。
argument-hint: "<モード> [Issue番号]   モード= plan | simple | interactive | fable"
allowed-tools: Bash, Read, Glob, Grep
---

# /cc-launch — モード選択式 作業起動スキル

このスキルは Claude Code の作業を **モード選択式** で起動します。タスクの性質に応じて
「Issue の自動読み込み」「計画フェーズの有無」「使用モデル」を切り替えます。

> **設計根拠**: [ADR-0010 作業起動フローをモード選択式スキル + Issue 自動読み込みで標準化する](../../docs/adr/0010-cc-launch-skill-and-issue-memory.md)
> **連携スキル**: [issue-memory](../issue-memory/SKILL.md)（Issue 自動読み込み）

---

## トリガー条件

以下のいずれかの場合に使用：

- ユーザーが `/cc-launch <モード> [Issue番号]` を実行した場合
- ユーザーが「plan モードで Issue #XXX を始めて」「対話モードで調査したい」など、
  モードを伴う作業開始を依頼した場合

---

## 引数仕様

| 引数 | 位置 | 必須 | 説明 |
|------|------|:---:|------|
| モード | `$1` | ✅ | `plan` / `simple` / `interactive` / `fable` のいずれか |
| Issue 番号 | `$2` | △ | 対象 Issue 番号。`interactive` 以外では必須（自動読み込みに使用） |

`$ARGUMENTS` で全引数を参照する。Issue 番号が省略され、かつ現在のブランチ名が
`{type}/issue-{番号}-*` 形式の場合は、ブランチ名から Issue 番号を推測する。

```bash
# 例
/cc-launch plan 54          # plan モードで Issue #54 を起動
/cc-launch simple 55        # 簡易タスクモードで Issue #55 を起動
/cc-launch interactive      # 対話モード（Issue 指定なしも可）
/cc-launch fable 56         # Fable モードで Issue #56 を起動
```

---

## モード分岐

`$1`（モード）で以下に分岐する。

```
if   モード == plan         → 「1. plan モード」へ
elif モード == simple       → 「2. 簡易タスクモード」へ
elif モード == interactive  → 「3. 対話モード」へ
elif モード == fable        → 「4. Fable モード」へ
else                        → エラー（有効なモードを案内して終了）
```

無効なモードが渡された場合は、有効なモード一覧（plan / simple / interactive / fable）を
提示して終了する。

---

## 1. plan モード

**用途**: 実装方針の検討が必要なタスク。計画を立ててから実装する。

### 手順

1. **Issue 自動読み込み**: `issue-memory` スキルのステップ0/1 を実行し、対象 Issue の
   背景・課題・対応方針・完了条件と、現在のブランチ状況を把握する。
2. **plan 提示**: 把握した内容をもとに実装計画（ステップ分解）を提示する。
3. **モデル判定**: 下記「plan モードのモデル判定」に従い、Sonnet / Opus のいずれが
   適切かを判定し、**推奨モデルと判定理由を提示**する。
   - セッション全体のモデルはスキルから変更できないため、ユーザーに `/model` での
     切り替え（または推奨モデルでの再起動）を案内する。

### plan モードのモデル判定

以下の観点を評価し、**いずれか 1 つでも Opus 該当なら Opus**、すべて Sonnet 該当なら
Sonnet を推奨する。

| 観点 | Sonnet | Opus |
|------|--------|------|
| **ステップ数** | 5 ステップ以下 | 6 ステップ以上 |
| **新規/既存** | 既存・横展開（類似パターンの展開など） | 新規 |
| **思考量** | agent に則って実施可能 / 一般的な思想に基づく / 他の設計を参考にできる | life-os アーキテクチャ固有の思考が必要 / 設計レビューなど成果物の妥当性を評価する |

> ステップ数の境界は **5 以下 = Sonnet / 6 以上 = Opus**（境界の 5 は Sonnet 側）。

**補足する一般基準（観点として加味する）**:
- 既定は Sonnet。深い推論・大規模コンテキストでの多段計画・誤りのコストが高い高リスク
  タスク・エージェントのオーケストレーションでは Opus へ escalate する。
- 「Opus が計画（plan）し、Sonnet が実装（simple）する」分業はコスト効率に優れる。

### 判定結果の出力形式

```
【plan モード判定】
- 対象: Issue #XXX {タイトル}
- 計画ステップ数: {N}
- 観点評価:
  - ステップ数: {N}（{5以下→Sonnet / 6以上→Opus}）
  - 新規/既存: {既存・横展開→Sonnet / 新規→Opus}
  - 思考量: {少ない→Sonnet / 必要→Opus}
- 推奨モデル: {Sonnet / Opus}
- 理由: {Opus 該当観点があればその観点／なければ全観点 Sonnet}
- 切り替え: `/model {opus|sonnet}` で切り替えてから実装に進んでください
```

### plan モードでの検証コマンド案内

実装ステップに応じて以下のコマンドを案内する:

```bash
docker compose run --rm test    # pytest でスモークテスト
docker compose run --rm lint    # importlinter で境界検査
```

---

## 2. 簡易タスクモード

**用途**: タイポ修正・変数名変更・1〜2 ファイルの明確な変更など、計画が不要な小規模タスク。

### 手順

1. **Issue 自動読み込み**: `issue-memory` スキルのステップ0/1 を実行する。
2. **直接実装**: 計画フェーズを省略し、そのまま実装に進む。
3. **モデル**: Sonnet を既定とする（簡易タスクのため Opus 判定は行わない）。

---

## 3. 対話モード

**用途**: 調査・方針決めをユーザーと協調して進めるタスク。

### 手順

1. **Issue 自動読み込みは任意**: Issue 番号が指定された場合のみ `issue-memory` で読み込む。
   指定がない場合は読み込まない。
2. **協調進行**: 調査結果・選択肢・トレードオフを提示し、ユーザーと方針を決めながら進める。
   勝手に実装へ進まず、合意形成を優先する。

---

## 4. Fable モード

**用途**: 高難易度タスク。Fable モデルで実行する。

### 手順

1. **Issue 自動読み込み**: `issue-memory` スキルのステップ0/1 を実行する。
2. **Fable で実行**: 高難易度タスク向けに Fable モデルでの実行を案内する。
   - セッション全体のモデルはスキルから変更できないため、`/model claude-fable-5` での
     切り替え（または Fable での再起動）を案内する。

---

## 並列実行（複数 Issue を同時に進める場合）

複数 Issue を並列で進める場合は Claude Code 標準の agents 機能を用いる。

- **サブエージェント**（`.claude/agents/`）: 独立 context での委譲実行。
- **worktree 隔離**: 並列実行時のファイル競合は Claude Code 標準の worktree 挙動で回避する。
- **Agent View / Agent Teams**: 複数バックグラウンドセッションの監視・調整。

> 実装時に最新の Claude Code 仕様（サブエージェント frontmatter の `model` / `allowed-tools`、
> worktree 隔離パターン、Agent View/Teams の起動方法）を再確認すること。

---

## 使用例

### 例1: plan モードで起動

```
ユーザー: /cc-launch plan 54

Claude:
[issue-memory] Issue #54 を読み込みます...
【Issue #54 概要】
- 目的: cc-launch / issue-memory スキルを追加
- 主な作業: issue-memory 作成 / cc-launch 作成 / ADR 作成 / CLAUDE.md 更新
...
[計画を提示]
【plan モード判定】
- 計画ステップ数: 4
- 推奨モデル: Sonnet
- 理由: ステップ数 5 以下 + 既存パターンの横展開 + 一般的な思想に基づく実装
- 切り替え: 現在の Sonnet で実装に進んでください
```

### 例2: 簡易タスクモードで起動

```
ユーザー: /cc-launch simple 55

Claude:
[issue-memory] Issue #55 を読み込みます...
計画フェーズを省略し、Sonnet で直接実装に進みます。
```

### 例3: 対話モードで起動

```
ユーザー: /cc-launch interactive

Claude:
対話モードで開始します。調査・方針決めを一緒に進めましょう。何から確認しますか？
```

---

## 注意事項

- **モデル切り替えの制約**: スキルはセッション全体のモデルを変更できない。plan/fable の
  モデル指定は「推奨提示 + `/model` 切り替え案内」として扱う。
- **Issue 番号の確認**: `plan` / `simple` / `fable` では Issue 番号が必須。省略時はブランチ名
  （`{type}/issue-{番号}-*`）から推測し、推測できない場合はユーザーに確認する。
- **日本語統一**: すべての出力は日本語で記述する。
- **並列実行は標準機能へ**: サブエージェント / Agent View / Agent Teams を用いる。

---

**このスキルは `/cc-launch <モード> [Issue番号]` の実行時、またはモードを伴う作業開始の依頼時に適用してください。**
