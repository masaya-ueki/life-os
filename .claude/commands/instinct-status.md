---
name: instinct-status
description: 蓄積された instinct を一覧表示する。ドメイン別・confidence 降順。--domain / --min-confidence / --orphaned フィルタ対応。
argument-hint: "[--domain <name>] [--min-confidence <0.3|0.5|0.7|0.9>] [--orphaned]"
---

# /instinct-status — instinct の可視化

蓄積された instinct の一覧を表示します。

> **このコマンドは [continuous-learning スキル](./../skills/continuous-learning/SKILL.md) の一部です。**

---

## 処理手順

### ステップ 1: YAML スキャン

```
/home/dev/.claude/projects/-home-dev-workspace-life-os-main/memory/instincts/
```

配下（`_archive/` を除く）の全 YAML ファイルを読み込みます。

### ステップ 2: フィルタリング

| 引数 | 効果 |
|------|------|
| `--domain <name>` | 指定ドメインのみ表示 |
| `--min-confidence <値>` | 指定値以上の instinct のみ表示 |
| `--orphaned` | 30 日以上更新されていない instinct のみ表示 |

フィルタなしの場合は全件表示。

### ステップ 3: 表示

ドメイン別グルーピング、confidence 降順で出力します：

```
=== instinct status ===
総数: 12 件（archive 除く）

【architecture】(3 件)
  ● [0.9] architecture-public-py-boundary
      trigger: 新しい領域間連携を実装する場合
      action:  他領域の内部パッケージを直接 import せず、public.py 経由でアクセスする
      観測: 3 回 | 最終更新: 2026-06-15

  ● [0.7] architecture-new-domain-checklist
      trigger: 新しい領域（Bounded Context）を追加する場合
      action:  .importlinter / pyproject.toml / system:* ラベル / README を同時更新する
      観測: 2 回 | 最終更新: 2026-06-10

  ○ [0.3] architecture-adr-link-required
      trigger: ADR に対応する設計を実装する場合
      action:  コード内または SKILL.md から ADR へのリンクを張る
      観測: 1 回 | 最終更新: 2026-06-01

【git-workflow】(2 件)
  ● [0.5] git-workflow-pull-before-branch
      trigger: 新しいブランチを切る前
      action:  必ず git pull で main を最新化してからブランチを作成する
      観測: 2 回 | 最終更新: 2026-06-12
  ...

昇華推奨（confidence ≥ 0.7）: 4 件
→ /evolve で昇華候補を確認できます
```

---

## confidence の見方

| マーク | confidence | 意味 |
|--------|-----------|------|
| ● | 0.9 | ほぼ確定。ADR/skill への昇華を強く推奨 |
| ● | 0.7 | 強い。`/evolve` の昇華候補 |
| ○ | 0.5 | 中程度。関連場面で考慮事項として提示 |
| ○ | 0.3 | 暫定。参照のみ、自動適用なし |

---

## 実行例

```bash
/instinct-status
# → 全件表示

/instinct-status --domain architecture
# → architecture ドメインのみ

/instinct-status --min-confidence 0.7
# → confidence 0.7 以上のみ（昇華候補確認）

/instinct-status --orphaned
# → 30 日以上更新されていない instinct を表示
```
