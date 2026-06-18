# deckgen — outline.yml → 編集可能ネイティブ pptx

`outline.yml`（プレゼンの単一の真実）から、**PowerPoint で文字・表・図形を直接編集できるネイティブな .pptx** を生成する支援ツール。

> **設計根拠**: [ADR-0007 outline.yml から編集可能ネイティブ pptx を生成する](../../docs/adr/0007-pptx-output.md)

- プレゼン作成システム（[ADR-0003](../../docs/adr/0003-presentation-system.md)）の **pptx 出力ターゲット**。`outline.yml` スキーマは HTML パイプラインと共有・不変。
- 出力は **python-pptx** によるネイティブ要素（テキストボックス／表／オートシェイプ／ネイティブチャート）。画像貼り付けは行わない＝後から PowerPoint で編集可能。
- 配置は `scripts/`（支援ディレクトリ＝ツール置き場）。`presentation/` は [rule/directory-structure.md](../../rule/directory-structure.md) で「コード無しの content 領域」と定められているため、コードは `scripts/deckgen/` に置く。uv workspace member ではなく、依存は本ディレクトリの `pyproject.toml` に閉じる。

## 使い方

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
| `structure` | `type: matrix-2x2` | 2×2 の矩形セル（右上=accent 強調）＋ X/Y 軸ラベル |
| `structure` | `type: tree` | 多階層のネイティブ箇条書き（root→children をインデント） |
| `structure` | `type: pyramid` | 段ごとの台形/矩形を積層（下段ほど広い） |
| `structure` | matrix-table / venn | tree 同様の箇条書きにフォールバック（簡略化） |
| `emphasis` | `mode: big-number` | accent 面＋巨大数値＋単位＋ラベル（中央） |
| `emphasis` | `mode: message` / `quote` | accent 面＋大きな1文（quote は引用符＋出典） |
| `emphasis` | `mode: kpi` | KPI カードを横並び（数値＋増減＋ラベル） |
| `chart` | `type: bar/line/pie/stacked` | **ネイティブ PowerPoint チャート**（編集可能。データ不足時は本文の箇条書きにフォールバック） |
| 未知/欠落 | — | `bullet` にフォールバックし、警告を出力 |

配色は `theme.py`（`presentation/templates/base.css.md` のトークンを転記、`deck.theme` で `default`/`dark`）。`--template` 指定時はマスター背景・配色を優先するため自前の背景塗りは行わない。

## 既知の割り切り（編集可能性を優先した結果）
- アニメーション・スピーカーノート・高度チャート（Waterfall 等）は非対応（python-pptx の制約）。
- 凝った図解（tree/venn 等）は HTML 版ほどの作り込みはせず、簡略なネイティブ表現にする。
- 完全なブランド再現が必要なら `--template` でコーポレートテンプレを継承する運用。

## 構成

```
scripts/deckgen/
  pyproject.toml          # deckgen パッケージ（uv member 外の支援ツール）。dep: python-pptx, PyYAML
  src/deckgen/
    __main__.py           # CLI
    loader.py             # outline.yml 読込・検証・パス解決
    theme.py              # 配色トークン（base.css.md と一致）
    layout.py             # 寸法・色・テキストボックス・図形・表の共通ヘルパ
    builder.py            # Presentation 組み立て（ヘッダ＋expression dispatch）
    expressions/          # title / bullet / comparison / flow / structure / emphasis / chart
  tests/test_builder.py
```
