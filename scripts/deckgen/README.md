# deckgen — outline.yml → 編集可能ネイティブ pptx

`outline.yml`（プレゼンの単一の真実）から、**PowerPoint で文字・表・図形を直接編集できるネイティブな .pptx** を生成する支援ツール。

> **設計根拠**: [ADR-0007 outline.yml から編集可能ネイティブ pptx を生成する](../../docs/adr/0007-pptx-output.md)

- プレゼン作成システム（[ADR-0003](../../docs/adr/0003-presentation-system.md)）の **pptx 出力ターゲット**。`outline.yml` スキーマは HTML パイプラインと共有・不変。
- 出力は **python-pptx** によるネイティブ要素（テキストボックス／表／オートシェイプ／ネイティブチャート）。画像貼り付けは行わない＝後から PowerPoint で編集可能。
- 配置は `scripts/`（支援ディレクトリ＝ツール置き場）。`presentation/` は [rule/directory-structure.md](../../rule/directory-structure.md) で「コード無しの content 領域」と定められているため、コードは `scripts/deckgen/` に置く。uv workspace member ではなく、依存は本ディレクトリの `pyproject.toml` に閉じる。

## 使い方

> 前提: Python **3.12 以上**（リポジトリ標準 `requires-python = ">=3.12"` に統一。根拠は [ADR-0007](../../docs/adr/0007-pptx-output.md)）。

```bash
# slug 指定（presentation/decks/{slug}/outline.yml を読む）
uv run --project scripts/deckgen -m deckgen claude-code-security
#   → presentation/decks/claude-code-security/claude-code-security.pptx

# outline.yml を直接指定 + 出力先指定
uv run --project scripts/deckgen -m deckgen path/to/outline.yml --out deck.pptx

# 企業テンプレ(.potx/.pptx)のマスター・配色を継承
uv run --project scripts/deckgen -m deckgen claude-code-security --template brand.potx
```

テスト: `uv run --project scripts/deckgen pytest`

## expression → ネイティブ pptx マッピング

`outline.yml` の各 expression（`data` 契約は `.claude/skills/slide-expression/references/*.md`）を、編集可能なネイティブ要素へ写像する。各コンテンツスライドは共通で **タイトル(h2相当) + 下線 + リード(summary)** のヘッダを持つ。

| expression | data | pptx での表現（すべてネイティブ＝編集可能） |
|-----------|------|------|
| `title` | 不要 | 全面の表紙レイアウト（中央寄せの大タイトル＋サブ＋content行＋日付） |
| `bullet` | content を使用 | ネイティブ箇条書きテキストフレーム（件数で文字サイズ自動調整） |
| `comparison` | `mode: two-column` / `pros-cons` | 左右2枚のカード（角丸シェイプ）＋ラベル＋箇条書き、`note` を脚注に |
| `comparison` | `mode: table` | ネイティブ表（ヘッダ行=accent、行=評価軸、ゼブラ） |
| `flow` | `type: steps`（horizontal/vertical） | 角丸シェイプの連結＋番号バッジ（楕円）＋矢印オートシェイプ |
| `flow` | timeline / cycle | steps と同様に描画（date があれば見出しに付与） |
| `structure` | `type: matrix-2x2` | 2×2 の矩形セル＋ X/Y 軸ラベル。`quadrants` は順序契約 `[右上, 左上, 右下, 左下]`（右上=最優先を accent 強調。契約は structure.md） |
| `structure` | `type: tree` | root + 第1階層を角丸ボックス＋コネクタ線で接続（孫は子ボックス内に小さく列挙）。root/children が片方のみなら多階層箇条書き |
| `structure` | `type: pyramid` | 段を積層（頂点=三角形・中段=台形・土台=矩形、下段ほど広い） |
| `structure` | `type: venn` | 2集合の半透明な重なり円＋重なり部の overlap ラベル（`sets` が2未満なら tree にフォールバック） |
| `structure` | matrix-table | tree 同様の箇条書きにフォールバック（汎用分類は rows/cols を持たないため） |
| `emphasis` | `mode: big-number` | accent 面＋巨大数値＋単位＋ラベル（中央） |
| `emphasis` | `mode: message` / `quote` | accent 面＋大きな1文（quote は引用符＋出典） |
| `emphasis` | `mode: kpi` | KPI カードを横並び（数値＋増減＋ラベル） |
| `chart` | `type: bar/line/pie/stacked` | **ネイティブ PowerPoint チャート**（編集可能。データ不足時は本文の箇条書きにフォールバック） |
| 未知/欠落 | — | `bullet` にフォールバックし、警告を出力 |

配色は `theme.py`（`presentation/templates/theme-tokens.yml` を単一ソースとして読み、`deck.theme` で `default`/`dark`）。HTML スライドと同じトークンを共有する。`--template` 指定時はマスター背景・配色を優先するため自前の背景塗りは行わない。

## 既知の割り切り（編集可能性を優先した結果）
- アニメーション・スピーカーノート・高度チャート（Waterfall 等）は非対応（python-pptx の制約）。
- 図解（matrix-2x2 / tree / pyramid / venn）はネイティブ図形で描く。tree はコネクタ線、venn は半透明の重なり円。深い階層や3集合以上など表現の限界を超えるものは箇条書きにフォールバックする。
- 完全なブランド再現が必要なら `--template` でコーポレートテンプレを継承する運用。

## 構成

```
scripts/deckgen/
  pyproject.toml          # deckgen パッケージ（uv member 外の支援ツール）。dep: python-pptx, PyYAML
  src/deckgen/
    __main__.py           # CLI
    loader.py             # outline.yml 読込・検証・パス解決
    theme.py              # 配色トークン（theme-tokens.yml を読む単一ソース）
    layout.py             # 寸法・色・テキストボックス・図形・表の共通ヘルパ
    builder.py            # Presentation 組み立て（ヘッダ＋expression dispatch）
    expressions/          # title / bullet / comparison / flow / structure / emphasis / chart
  tests/test_builder.py
```
