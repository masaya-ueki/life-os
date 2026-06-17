---
name: code-review-architecture
description: life-os 固有のアーキテクチャ境界・構造を機械的に確認するレビュースキル。領域間 import は public.py 経由のみ・shared は領域非依存・新トップレベルモジュール追加時の .importlinter / pyproject members / system ラベル / README 同時更新・ADR リンクルールを観点化する。検査は uv run lint-imports。Use when: .importlinter / pyproject.toml / public.py / 新トップレベルdir / docs/adr を含む変更をレビューする、pr-reviewer が境界・構造変更を見つけたとき。Triggers on: アーキテクチャレビュー, 境界レビュー, importlinter, public.py, workspace, ADRレビュー, architecture review.
---

# アーキテクチャ境界レビュー・スキル（life-os 固有）

life-os の **Modular Monolith × Bounded Context**（[ADR-0002](../../../docs/adr/0002-modular-monolith-bounded-context.md)）の構造が崩れていないかを確認する。
一般観点・severity 語彙は [`code-review-general`](../code-review-general/SKILL.md)、領域ごとの重点は [`domain-checklist`](../code-review-general/references/domain-checklist.md) を併用する。

このスキルが扱うのは「**一度崩すと波及が大きく、機械的に判定できる**」構造の観点。該当する `[must]` は妥協しない。

---

## いつ適用するか（トリガーになる変更）

以下のいずれかを含む差分では必ず適用する。

- `.importlinter`
- `pyproject.toml`（ルート / 各領域）
- いずれかの `*/public.py`
- 新しいトップレベルディレクトリ（新領域・新 content領域）の追加
- `docs/adr/` の追加・変更
- 領域内の新規トップレベルモジュール（`public.py` 以外）の追加

---

## 観点カテゴリ（チェックリスト）

### 1. 領域間の依存（public.py 経由のみ）
- [ ] 他領域を参照するとき、相手の `public.py` だけを import しているか。**他領域の内部パッケージ（`domain`/`application`/`adapters`/`models`/`index`）を直接 import していないか**（`[must]`: `.importlinter` の `*-uses-only-public` 契約違反）
- [ ] import の向きが領域の独立性を壊していないか（循環依存を作っていないか）

### 2. shared の独立性
- [ ] `shared` が `task`/`content_sales`/`media`/`travel` のいずれにも依存していないか（`[must]`: `shared-is-foundation` 契約違反）
- [ ] `shared` に特定領域専用の都合を持ち込んでいないか（最小限の基盤に留まっているか）

### 3. 新トップレベルモジュール / 新領域の追加時（同時更新）
領域直下に `public.py` 以外の新規トップレベルモジュールを足した、または新領域を追加した場合、**以下が揃って更新されているか**（ADR-0002 の手順）。1つでも欠けたら `[must]`。
- [ ] `.importlinter` のコントラクト（新モジュールを各領域の forbidden に追記 / 新領域の contract 追加・root_packages 追記）
- [ ] `pyproject.toml` の `[tool.uv.workspace] members` と `[tool.uv.sources]`
- [ ] 対応する `system: *` ラベル（[issue-operation-rules.md](../../../guides/development-policy/issue-operation-rules.md) と `scripts/setup-github-labels.sh`）
- [ ] `README.md` の「ディレクトリ構成」

### 4. content領域の扱い
- [ ] `presentation`/`docs`/`guides` をうっかり uv workspace member / Bounded Context として扱っていないか（これらはコード非依存・`.importlinter` 管理外、[ADR-0003](../../../docs/adr/0003-presentation-system.md)）
- [ ] Claude Code のエージェント/スキルは `.claude/agents/`・`.claude/skills/` に置かれているか

### 5. ADR リンクルール
- [ ] 一般的な慣習から外れた選択・変更コストの高い構造判断に対して、必要なら ADR があるか（基準は [docs/adr/README.md](../../../docs/adr/README.md)）
- [ ] ADR に対応する設計（README/ガイド/コード）から **ADR へのリンク**が張られているか
- [ ] ADR を追加したら `docs/adr/README.md` の一覧表に行が追記されているか
- [ ] 決定を覆す場合、古い ADR を削除せずステータスを `置き換え済み` にしてリンクしているか

### 6. Git・命名の構造
- [ ] ブランチ/コミット/ラベルの識別子が一致しているか（`{type}({scope})` ＝ type ラベル / `system:` ラベル）
- [ ] PR 本文に `Closes #N` があるか（Task Issue の自動クローズ）

---

## 検査コマンド（証拠主義）

```bash
uv run lint-imports     # 領域境界の機械検査（.importlinter）。違反は [must]
uv run pytest           # スモークテスト
```

- 境界に関わる指摘は**主張でなく `lint-imports` の出力**で確認する。
- `.importlinter` を変更した場合、その変更が「境界を緩めていないか（抜け穴を作っていないか）」を特に厳しく見る。

---

## severity の目安

| `[must]`（妥協しない） | `[imo]`/`[ask]` |
|----------------------|------------------|
| 他領域内部の直接 import / shared の領域依存 | 将来の領域分割の提案 |
| 新モジュール追加で `.importlinter`/`pyproject`/README の同時更新漏れ | ディレクトリ命名の好み |
| ADR が必要な構造変更に ADR・リンクが無い | ADR の文章表現の改善 |
| content領域を workspace member 化する誤り | — |
