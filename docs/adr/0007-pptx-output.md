# ADR-0007: outline.yml から編集可能ネイティブ pptx を生成する

- **ステータス**: `承認済み`
- **決定日**: 2026-06-18
- **決定者**: masaya_ueki
- **関連タスク**: presentation: pptxの作成
- **置き換え**: -

---

## コンテキスト

[ADR-0003](./0003-presentation-system.md) で、`outline.yml` を単一の真実として自己完結 HTML スライドを生成するパイプラインを導入した。今回、同じ `outline.yml` から **PowerPoint(.pptx)** も生成したいという要件が加わった。

ユーザー確認の結果、要件は2点で確定している。

1. **出力形式**: 「PowerPoint で文字・表を直接編集できる**ネイティブ要素**」を優先する（各スライドを画像として貼り付ける方式ではない）。凝った図解は簡略化を許容する。
2. **実装技術はリポジトリに最適な1つに統一**したい（「pptx の編集に優れる」基盤を選ぶ）。

決めるべき構造的な論点は次の3つで、いずれも複数の有力な選択肢があり自明でない。

1. **pptx 生成の出力形式**: 編集可能なネイティブ要素か、見た目を完全再現する画像貼り付けか。
2. **実装技術**: python-pptx / PptxGenJS / Pandoc / HTML→画像変換 のいずれか。
3. **コードの配置**: [.claude/rule/directory-structure.md](../../.claude/rule/directory-structure.md)（[ADR-0005](./0005-directory-governance-daily-keeper.md)）は `presentation/` を「コードを持たない content 領域」と定める。pptx 生成は Python コードであり、置き場所を決める必要がある。

前提として Anthropic 公式・主要 OSS を調査した。Anthropic 公式 `anthropics/skills` の `pptx` スキルは **PptxGenJS(JS)** ベースで、既存ファイルを読まずゼロから生成する設計。Claude のファイル作成機能も裏で pptx を生成する。python-pptx 1.0 はネイティブ編集可能 pptx・テンプレ(.potx)継承・基本チャート（column/bar/line/pie）に対応し、アニメ・高度チャートは非対応。

## 決定事項

**`outline.yml` から編集可能なネイティブ pptx を `python-pptx` で生成する。** 実装は **支援ディレクトリ `scripts/deckgen/`**（パッケージ名 `deckgen`、uv workspace member 外）に置く。`outline.yml` スキーマは不変で、pptx は HTML と並ぶ新しい出力ターゲットとして追加する。テンプレ(.potx/.pptx)継承は `--template` で任意サポートする。

## 検討した選択肢

### 出力形式

#### 選択肢A: 編集可能ネイティブ要素（採用）
- **メリット**: PowerPoint で文字・表・図形を後編集できる。テンプレ継承で企業ブランドを適用しやすい。ユーザー要件に直接合致。
- **デメリット**: HTML 版の凝った図解（マトリクス/ツリー/フロー）は完全再現が難しく、簡略なネイティブ表現になる。

#### 選択肢B: 見た目完全再現（HTML→各スライド画像→pptx）（不採用）
- **メリット**: 既存 HTML 資産をそのまま使え、再現度が最高。
- **デメリット**: スライドが画像化され**編集不可**。
- **不採用理由**: ユーザーは編集可能を最優先と明言しており要件に反する。

### 実装技術

#### 選択肢A: python-pptx（採用）
- **メリット**: 既存 pptx/テンプレ(.potx)を**読み込んでスライドマスター・配色を継承**できる。ネイティブの表・図形・チャートを生成。本リポジトリは Python 中心（uv / pytest / importlinter）で親和性が高い。MIT。
- **デメリット**: アニメ・高度チャート非対応。複雑レイアウトは図形配置を自前で実装する必要がある。

#### 選択肢B: PptxGenJS（Anthropic 公式採用・不採用）
- **メリット**: 公式 pptx スキルと同基盤。ゼロ依存・高速。
- **デメリット**: **既存 pptx を読めず**ゼロ生成専用 → テンプレ継承・「編集」要件で不利。Node 依存が増える。
- **不採用理由**: 「編集に優れる／テンプレ継承」要件に対し読み込み不可は致命的。Python 中心の本リポジトリに Node を持ち込む必要も薄い。

#### 選択肢C: Pandoc（md→pptx, reference-doc）（不採用）
- **メリット**: reference-doc でネイティブ pptx を簡便に生成。
- **デメリット**: 出力レイアウトがテンプレのプレースホルダに強く制約され、`expression` ごとの自由な図解表現が困難。中間に md 変換が必要。
- **不採用理由**: 表現の自由度と `outline.yml` 直結性で python-pptx に劣る。

### コードの配置

#### 選択肢A: 支援ディレクトリ `scripts/deckgen/`（採用）
- **メリット**: `scripts/` は正典で「支援: ツール」と定義済み。HTML 生成のロジックも agent（`.claude/`=支援）に置かれており、生成コードを支援に置く方針と一貫する。`presentation/` を「コード無しの content 領域」のまま保てる（rule/ と矛盾しない）。`scripts/check_structure.py` のチェックも通る（トップレベルは増えず、member 扱いも不要）。
- **デメリット**: `scripts/` は従来フラットなスクリプト（stdlib のみ）だったが、本ツールは独自 `pyproject.toml`（python-pptx 依存）を持つパッケージである点が新しい。

#### 選択肢B: `presentation/deckgen/`（content 領域に同居・不採用）
- **メリット**: 生成元の content と同居して直感的。
- **デメリット**: `presentation/` は rule/directory-structure.md で「コードを持たない content 領域」と明記。ここにコードを置くと日次 directory-keeper 監査と矛盾し、「content 領域＝コード無し」の不変条件が崩れる。
- **不採用理由**: 統治ルールに正面から反する。

#### 選択肢C: uv workspace member（Bounded Context）化（不採用）
- **メリット**: task/media と同じ規律（public.py / importlinter）に乗る。
- **デメリット**: deckgen は「人生ドメイン」ではなく**ビルドツール**。BC の境界規律を課すのは概念的に過剰で、`root_packages` の意味を濁す（[ADR-0002](./0002-modular-monolith-bounded-context.md)）。
- **不採用理由**: BC は生活領域のための仕組み。ツールは支援ディレクトリが正しい置き場。

> ディレクトリ名は `build` を避け `deckgen` とした。ルート `.gitignore` の `build/` パターンに巻き込まれてソースが無視されるのを防ぐため。

## 結果・トレードオフ

- **配置**: `scripts/deckgen/`（`pyproject.toml` + `src/deckgen/` + `tests/`）。uv member 外・`.importlinter` 対象外。実行は `uv run --project scripts/deckgen -m deckgen <slug>`。
- **Python バージョン**: リポジトリ標準（ルート / 各領域）の `requires-python = ">=3.12"` に統一する。deckgen は uv member 外で独自に `requires-python` を宣言するが、検証環境を揃え方針の一貫性を保つため標準に合わせる（導入初期の暫定 `>=3.10` 差異は解消済み。コードは `from __future__ import annotations` と `X | None` 記法のみで 3.10 固有の回避策は無く、除去対象は無い）。
- **単一の真実**: `outline.yml`（[presentation/README.md](../../presentation/README.md)）は不変。HTML と pptx は同じ契約を読む別レンダラ。
- **マッピング仕様**: expression→ネイティブ pptx の対応は [scripts/deckgen/README.md](../../scripts/deckgen/README.md) に定義。索引スキル `.claude/skills/slide-pptx/` からも参照する。
- **生成物**: 出力 `.pptx` はビルド成果物として `.gitignore` で除外する（[R-STRUCT-4](../../.claude/rule/directory-structure.md)）。deck はコマンドで都度再生成する。
- **割り切り**: アニメ・スピーカーノート・高度チャート非対応。完全ブランド再現は `--template` 運用。図解（matrix-2x2 / tree / pyramid / venn）はネイティブ図形で描き（#32 で tree のコネクタ線・venn の重なり円を作り込み）、表現の限界を超えるものは箇条書きにフォールバックする。`matrix-2x2` の `quadrants` は `[右上, 左上, 右下, 左下]` の順序契約（[structure.md](../../.claude/skills/slide-expression/references/structure.md)）に従い、HTML・pptx で一致させる。
- **ADR-0003 との関係**: ADR-0003 の HTML パイプラインは無改変で併存。本 ADR は出力ターゲットを追加するのみ。`presentation/` の「コード無し content 領域」という位置づけも維持する（コードは `scripts/` 側に置くため）。

## 関連ドキュメント・リンク

- [scripts/deckgen/README.md](../../scripts/deckgen/README.md) — expression→pptx マッピング・使い方
- [presentation/README.md](../../presentation/README.md) — システム概要・YAML スキーマ
- [ADR-0003](./0003-presentation-system.md) — プレゼン作成システム（HTML パイプライン）
- [ADR-0005](./0005-directory-governance-daily-keeper.md) — ディレクトリ統治（配置の根拠）
- [ADR-0002](./0002-modular-monolith-bounded-context.md) — Bounded Context（deckgen を BC 非該当とする根拠）
- Anthropic Agent Skills `pptx`（PptxGenJS）/ python-pptx 1.0 ドキュメント（調査出典）
