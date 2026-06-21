---
name: evolve
description: confidence ≥ 0.7 の instinct をクラスタリングし、skill / command / rule / ADR への昇華を提案・実行する。ユーザー承認後にファイル生成と archive 移動を行う。
---

# /evolve — instinct の昇華

高 confidence（≥ 0.7）の instinct をクラスタリングし、team scope のファイルへ昇華します。

> **このコマンドは [continuous-learning スキル](./../skills/continuous-learning/SKILL.md) の一部です。**

---

## 実行タイミング

- `confidence ≥ 0.7` の instinct が 2 件以上蓄積されたとき
- 月 1 回程度の定期メンテナンス

---

## 処理手順

### ステップ 1: 昇華候補の収集

```
/home/dev/.claude/projects/-home-dev-workspace-life-os-main/memory/instincts/
```

配下（`_archive/` を除く）から `confidence >= 0.7` の instinct を全件抽出します。

### ステップ 2: クラスタリング

同一ドメイン・類似 trigger・相互補完の観点でグルーピングします：

- **同一ドメイン内で複数**: まとめて 1 つの skill / rule に昇華できないか判断
- **単発で confidence 0.9**: ADR や rule として独立昇華を検討
- **手順を持つもの**: skill または command に昇華

### ステップ 3: 昇華先の提案（ユーザー確認）

```
=== /evolve 昇華提案 ===

【クラスタ A】architecture ドメイン（3 件）
  - architecture-public-py-boundary [0.9]
  - architecture-new-domain-checklist [0.7]
  - architecture-adr-link-required [0.7]

  提案昇華先: .claude/rules/architecture-boundaries.md
  理由: 常時適用すべきコーディング規約として、3 件をまとめて rule 化できます

  → 昇華しますか？ [y/n/別の昇華先を指定]

【クラスタ B】testing ドメイン（2 件）
  - testing-docker-compose-run-rm [0.9]
  - testing-lint-before-push [0.7]

  提案昇華先: .claude/rules/testing-docker-first.md
  理由: Docker 経由テストという常時ルールとして rule 化が適切です

  → 昇華しますか？ [y/n/別の昇華先を指定]
```

### ステップ 4: 昇華先ファイル生成

ユーザーが承認した昇華先にファイルを生成します。

**昇華先の選択基準**:

| 昇華先 | 適合する instinct の特徴 |
|--------|------------------------|
| `.claude/rules/<name>.md` | 常時適用すべき規約・コーディングルール |
| `.claude/skills/<name>/SKILL.md` | 複数ステップのワークフロー・判断ロジック |
| `.claude/commands/<name>.md` | 単発で起動する定型作業 |
| `docs/adr/XXXX-*.md` | 重要な設計判断（採用根拠・却下した選択肢） |

**ADR 採番**: `docs/adr/` 配下の最大番号 +1 を自動採番します。

### ステップ 5: Archive 移動

昇華した instinct に `evolved_to` をセットし `_archive/` に移動します：

```yaml
# 元の YAML に追記
evolved_to: ".claude/rules/architecture-boundaries.md"
last_updated: 2026-06-21
```

移動先: `_archive/YYYY-MM-DD-evolved-to-<basename>.yaml`

---

## 生成ファイルのテンプレート

### `.claude/rules/<name>.md`

```markdown
---
name: <name>
description: <1 行説明>
---

# <ルール名>

<適用条件と内容>

## ルール一覧

- <rule 1>
- <rule 2>

> **由来**: continuous-learning instinct より昇華（<日付>）
```

### `docs/adr/XXXX-*.md`

既存の `docs/adr/template.md` を参照して生成します。

---

## 非責務

- **自動昇華**: ユーザー承認なしの自動実行は行わない
- **既存ファイルの上書き**: 同名ファイルが存在する場合は差分を提示して確認を求める
- **archive からの復元**: `/evolve` は archive に移動するのみ（復元は手動）

---

## 実行例

```bash
/evolve

→ [スキャン中...]
→ confidence ≥ 0.7 の instinct: 5 件

【クラスタ A】architecture（3 件）...
昇華しますか？ [y]

→ .claude/rules/architecture-boundaries.md を生成しました
→ 3 件を _archive/ に移動しました

【クラスタ B】testing（2 件）...
昇華しますか？ [y]

→ .claude/rules/testing-docker-first.md を生成しました
→ 2 件を _archive/ に移動しました

=== 完了 ===
昇華: 5 件 → 2 ファイル生成
残り instinct: 7 件（confidence < 0.7）

次のステップ: git add .claude/rules/ → PR を作成してください
```
