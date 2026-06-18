---
name: slide-pptx
description: outline.yml を編集可能なネイティブ PowerPoint(.pptx) に変換する方針を示すスキル。expression → ネイティブ pptx 要素のマッピングと、生成ツール deckgen の使い方を案内する索引。Use when: outline.yml を pptx 化する、PowerPoint で編集可能なスライドが欲しい、expression が pptx でどう描かれるか知りたい。Triggers on: pptx, パワーポイント, PowerPoint, pptx化, スライドをpptxに, 編集可能なスライド.
---

# スライド pptx 化スキル

`outline.yml` を **PowerPoint で編集可能なネイティブ pptx**（テキストボックス／表／オートシェイプ／ネイティブチャート、画像貼り付けではない）に変換するための索引スキル。

> 設計根拠: [ADR-0007](../../../docs/adr/0007-pptx-output.md)

## 原則
- `outline.yml` が**単一の真実**。pptx は HTML と並ぶ出力ターゲットで、スキーマは [slide-structure](../slide-structure/SKILL.md) / [slide-expression](../slide-expression/SKILL.md) と共有する。
- 生成は決定的ツール **deckgen**（python-pptx 製）が担う。手作業で pptx を組まない。
- 図解の再現は HTML 版より簡略になりうる（編集可能性を優先）。完全なブランド再現はテンプレ継承で対応する。

## やること
1. `outline.yml` を用意（無ければ slide-content-planner で作る）。
2. 生成: `uv run --project scripts/deckgen -m deckgen <slug>`（テンプレ継承は `--template <path.potx>`）。
   - 実際の起動・検証は **`slide-pptx-builder` エージェント**に委譲してよい。
3. `presentation/decks/{slug}/{slug}.pptx` を PowerPoint で開いて編集。

## expression がどう pptx になるか
各 expression → ネイティブ pptx 要素の**対応表（単一の真実）は [scripts/deckgen/README.md](../../../scripts/deckgen/README.md)** を参照する（ここでは重複させない）。各スライドは共通で「タイトル＋下線＋リード」のヘッダを持ち、`title` は全面表紙、`emphasis` は accent 面、`chart` はネイティブチャート、未知 expression は `bullet` にフォールバックする。

## 関連
- 生成ツール: [scripts/deckgen/README.md](../../../scripts/deckgen/README.md)
- 出力エージェント: `.claude/agents/slide-pptx-builder.md`
- 配色トークン（単一ソース）: [presentation/templates/theme-tokens.yml](../../../presentation/templates/theme-tokens.yml)
