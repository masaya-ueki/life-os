# ADR-0013: presentation 領域を廃止し Claude Design へ移行する

- **ステータス**: `承認済み`
- **決定日**: 2026-07-30
- **決定者**: masaya_ueki
- **関連タスク**: #117
- **置き換え**: [ADR-0003](./0003-presentation-system.md)・[ADR-0007](./0007-pptx-output.md)

---

## コンテキスト

[ADR-0003](./0003-presentation-system.md) で `domains/presentation` を中心とした自己完結 HTML スライド生成基盤を、[ADR-0007](./0007-pptx-output.md) で `scripts/deckgen` によるネイティブ pptx 生成を導入した。以降、`slide-*` スキル・サブエージェント・`domains/presentation/decks/` の生成物を積み重ねてきたが、pptx のフォーマット統一・視覚品質・エージェント責務の整理といった課題が残ったまま運用コストが積み上がっていた（#108〜#114）。

一方で Claude Design（claude.ai の design-system プロジェクト）を使えば、コンポーネント／テンプレートの管理をリポジトリ内の自前パイプラインではなく Claude Design 側のプロジェクトとして持てる。自前の HTML/pptx レンダラ・QA スクリプトを保守し続けるより、Claude Design に一本化した方が持続的にメンテナンスコストが低い。

## 決定事項

**`domains/presentation` 領域、`scripts/deckgen`、および関連する `.claude/skills/slide-*` スキルと `.claude/agents/slide-*` サブエージェントを全て削除する。** 今後のプレゼン／デザイン成果物の作成は Claude Design へ移行する。Claude Design 専用のスキル・テンプレートは本 ADR とは別に、廃止後の作業として整備する。

## 検討した選択肢

### 選択肢A: 全削除して Claude Design へ移行（採用）
- **メリット**: 自前の HTML/pptx レンダラ・視覚 QA ループ・deckgen ツールチェーンの保守コストがゼロになる。Claude Design 側の更新（新表現・品質改善）をそのまま享受できる。
- **デメリット**: `domains/presentation/decks/` の生成済みサンプル（HTML/pptx）は失われる（過去のコミットからは復元可能）。Claude Design 専用の skill/template を新たに整備するまでの間、リポジトリ内でのスライド生成手段が空白になる。

### 選択肢B: 現状維持（不採用）
- **メリット**: 移行コストがかからない。
- **デメリット**: pptx フォーマット統一・エージェント責務整理など未解決の課題（#108〜#114）を自前実装のまま解決し続ける必要がある。
- **不採用理由**: Claude Design という代替手段がある以上、自前実装を維持し続ける理由が薄い。

### 選択肢C: HTML パイプラインのみ残し pptx（deckgen）だけ廃止（不採用）
- **メリット**: 依存ゼロの HTML 生成という ADR-0003 の利点は残せる。
- **デメリット**: 領域を中途半端に残すと「なぜ HTML だけ自前で pptx は Claude Design か」という判断軸が二重になり、richer な移行（Claude Design 一本化）の意図が薄まる。
- **不採用理由**: 段階的移行よりも、一度リセットしてから Claude Design 専用の構成を設計し直す方が明快。

## 結果・トレードオフ

- **削除対象**: `domains/presentation/`（`decks/` の生成物含む）、`scripts/deckgen/`、`docker/Dockerfile.pptx-convert`（`compose.yaml` の `pptx-convert` サービス含む）、`.claude/skills/{slide-expression,slide-pptx,slide-structure,slide-visual-qa}/`、`.claude/agents/{slide-content-planner,slide-deck-builder,slide-html-renderer,slide-pptx-builder,slide-pptx-visual-loop}.md`。
- **設定からの除去**: `pyproject.toml`（uv workspace member）・`.importlinter`（`presentation` root package とコントラクト）・`.gitignore`（deckgen 生成物の除外設定）から presentation 関連の記述を除去した。
- **ADR の扱い**: [ADR-0003](./0003-presentation-system.md)・[ADR-0007](./0007-pptx-output.md) は削除せず `置き換え済み` として履歴に残す（[docs/adr/README.md の運用ルール](./README.md#adr-のステータス管理)）。
- **Issue の扱い**: presentation 領域に紐づく未完了の open Issue（#108〜#114 等）は本 ADR の決定に伴いクローズする。
- **今後**: Claude Design 専用の skill / template の整備は、本 ADR の範囲外として別途行う。

## 関連ドキュメント・リンク

- [ADR-0003](./0003-presentation-system.md) — プレゼン作成システム（HTML パイプライン、本 ADR により置き換え）
- [ADR-0007](./0007-pptx-output.md) — outline.yml から pptx 生成（本 ADR により置き換え）
- [ADR-0009](./0009-group-domains-under-domains-dir.md) — 領域を `domains/` 配下にまとめる方針（presentation もこの対象だった）
