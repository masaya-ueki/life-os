# deckgen — outline.yml → 編集可能ネイティブ pptx

`outline.yml`（プレゼンの単一の真実）から、**PowerPoint で文字・表・図形を直接編集できるネイティブな .pptx** を生成する支援ツール。

> **設計根拠**: [ADR-0007 outline.yml から編集可能ネイティブ pptx を生成する](../../docs/adr/0007-pptx-output.md)

- プレゼン作成システム（[ADR-0003](../../docs/adr/0003-presentation-system.md)）の **pptx 出力ターゲット**。`outline.yml` スキーマは HTML パイプラインと共有・不変。
- 出力は **python-pptx** によるネイティブ要素（テキストボックス／表／オートシェイプ／ネイティブチャート）。画像貼り付けは行わない＝後から PowerPoint で編集可能。
- 配置は `scripts/`（支援ディレクトリ＝ツール置き場）。コードは `scripts/deckgen/` に置く。uv workspace member ではなく、依存は本ディレクトリの `pyproject.toml` に閉じる。

## 使い方

> 前提: Python **3.12 以上**（リポジトリ標準 `requires-python = ">=3.12"` に統一。根拠は [ADR-0007](../../docs/adr/0007-pptx-output.md)）。

```bash
# slug 指定（domains/presentation/decks/{slug}/outline.yml を読む）
uv run --project scripts/deckgen -m deckgen claude-code-security
#   → domains/presentation/decks/claude-code-security/claude-code-security.pptx

# outline.yml を直接指定 + 出力先指定
uv run --project scripts/deckgen -m deckgen path/to/outline.yml --out deck.pptx

# 企業テンプレ(.potx/.pptx)のマスター・配色を継承
uv run --project scripts/deckgen -m deckgen claude-code-security --template brand.potx
```

テスト: `uv run --directory scripts/deckgen pytest`

> `--directory` で deckgen を作業ディレクトリにする（pytest の rootdir を `scripts/deckgen` に固定するため）。`--project scripts/deckgen pytest` だとリポジトリルートの pytest 設定（`addopts=--ignore=scripts/deckgen`）が効き、deckgen のテストが収集されないので注意。

## expression → ネイティブ pptx マッピング

`outline.yml` の各 expression（`data` 契約は `.claude/skills/slide-expression/references/*.md`）を、編集可能なネイティブ要素へ写像する。各コンテンツスライドは共通で **タイトル(h2相当) + 下線 + リード(summary)** のヘッダを持つ。

| expression | data | pptx での表現（すべてネイティブ＝編集可能） |
|-----------|------|------|
| `title` | 不要 | 全面の表紙レイアウト（中央寄せの大タイトル＋サブ＋content行＋日付）。左揃えラインはコンテンツスライドと同じ `CONTENT_LEFT` |
| `bullet` | content を使用 | ネイティブ箇条書きテキストフレーム（件数で文字サイズ自動調整、溢れ時は自動縮小） |
| `comparison` | `mode: two-column` / `pros-cons` | 左右2枚の統一カード（`add_card`・角丸）＋ラベル＋箇条書き、`note` を脚注に。見出し色は意味色（pros-cons=good/bad、通常比較=accent2/accent） |
| `comparison` | `mode: table` | ネイティブ表（ヘッダ行=accent、行=評価軸、ゼブラ） |
| `flow` | `type: steps`（horizontal/vertical） | 統一カード（`add_card`・角丸・line 1.0pt 枠）の連結＋番号バッジ（楕円・accent 塗り）＋矢印オートシェイプ |
| `flow` | timeline / cycle | steps と同様に描画（date があれば見出しに付与） |
| `structure` | `type: matrix-2x2` | 2×2 の統一カード（`add_card`・角丸）＋ X/Y 軸ラベル。右上象限は `variant="accent"` で強調。`quadrants` は順序契約 `[右上, 左上, 右下, 左下]`（右上=最優先を accent 強調。契約は structure.md） |
| `structure` | `type: tree` | root（統一カード・accent 強調）+ 第1階層を統一カード＋コネクタ線で接続（孫は子ボックス内に小さく列挙）。root/children が片方のみなら多階層箇条書き |
| `structure` | `type: pyramid` | 段を積層（頂点=三角形・中段=台形・土台=矩形、下段ほど広い） |
| `structure` | `type: venn` | 2集合の半透明な重なり円＋重なり部の overlap ラベル（`sets` が2未満なら tree にフォールバック） |
| `structure` | matrix-table | tree 同様の箇条書きにフォールバック（汎用分類は rows/cols を持たないため） |
| `emphasis` | `mode: big-number` | accent 面＋巨大数値＋単位＋ラベル（中央） |
| `emphasis` | `mode: message` / `quote` | accent 面＋大きな1文（quote は引用符＋出典） |
| `emphasis` | `mode: kpi` | 統一カードを横並び（数値＋増減＋ラベル）。増減（delta）は符号で意味色（マイナス方向=bad、それ以外=good） |
| `chart` | `type: bar/line/pie/stacked` | **ネイティブ PowerPoint チャート**（編集可能。データ不足時は本文の箇条書きにフォールバック） |
| 未知/欠落 | — | `bullet` にフォールバックし、警告を出力 |

配色は `theme.py`（`domains/presentation/templates/theme-tokens.yml` を単一ソースとして読み、`deck.theme` で `default`/`dark`）。HTML スライドと同じトークンを共有する。`--template` 指定時はマスター背景・配色を優先するため自前の背景塗りは行わない。

## スタイル統一の規約（Issue #109）

expression ごとに「カード」の枠線・角丸・型スケール・余白がばらつかないよう、以下を単一の規約とする。

- **カード風の面は `layout.add_card()` のみで描く**。comparison カラム／KPI／flow ステップ／tree ノード／matrix-2x2 象限など、角丸の面はすべて `add_card(slide, left, top, width, height, theme, *, variant="outline", accent_bar=None)` を使う。
  - `variant="outline"`（既定）: card 塗り＋line 枠 1.0pt（`CARD_LINE_W`）の標準カード。
  - `variant="accent"`: accent 塗り・枠なし。スライド内で最重要の面（tree の root、matrix-2x2 の最優先象限など）にのみ使う。
  - `accent_bar`: 色 hex を渡すと左端にピル形状のアクセントバーを添える（カラム見出し色など）。
  - 個別 expression から `add_box_shape()` で角丸矩形を直接描かないこと（低レベル API は add_card 内部専用）。
- **型スケールは 8 段のみ**（`layout.py` の `FONT_*` が単一ソース）。役割対応:

  | 定数 | pt | 役割 |
  |------|----|------|
  | `FONT_CAPTION` | 14 | 注記・軸ラベル・ステップ説明 |
  | `FONT_SMALL` | 16 | バッジ・表セル・ツリー子ノード・表紙補足行 |
  | `FONT_BODY` | 18 | カード本文・ラベル・表ヘッダ |
  | `FONT_LEAD` | 22 | リード(summary)・箇条書き本文・カード見出し |
  | `FONT_H2` | 36 | スライド見出し |
  | `FONT_H1` | 40 | メッセージ・big-number の単位 |
  | `FONT_DISPLAY` | 48 | 表紙タイトル・KPI 数値 |
  | `FONT_HERO` | 96 | big-number の数値 |

- **余白は 8pt グリッド（`SPACE_*`）と `layout.py` の名前付き定数のみを使う**。expression 側のコードに生の `Inches(...)` / `Pt(...)` の寸法リテラルを書かないこと。ベン図の重なり幅など比率演算に由来する式は例外的に許容する。
- **表紙はコンテンツスライドと同じ `CONTENT_LEFT` に左揃え**。`title.py` は `layout.CONTENT_LEFT` / `CONTENT_WIDTH` を使い、章をまたいでも左端が一直線に揃う。
- **comparison two-column の見出し色は意味色**: `pros-cons` は good/bad、通常の two-column（muted ではなく）accent2/accent を使う。
- **KPI の増減表示（delta）も意味色**: 符号（`-` / `−` / `▼` / `▽` / `↓` で始まる）はマイナス方向とみなし bad、それ以外は good で色付けする。

## ブランドテンプレートの運用（`--template`）

### サンプルテンプレートで即試す

リポジトリには `scripts/deckgen/templates/sample-brand.pptx` が同梱されている。
`domains/presentation/templates/theme-tokens.yml` の `default` テーマカラーをマスターに設定した最小テンプレート。

```bash
# サンプルテンプレートでブランド継承を確認
uv run --project scripts/deckgen -m deckgen claude-code-security \
    --template scripts/deckgen/templates/sample-brand.pptx
```

### 背景塗りの抑止（重要）

`--template` を指定すると、deckgen はスライドごとの **背景塗りを自動で省略**する（`builder.py` の `use_bg = template_path is None`）。テンプレートのスライドマスターに設定した背景がそのまま使われる。テンプレートなしで生成した場合は `theme-tokens.yml` の `bg` カラーを自前で塗る。

### カスタムブランドテンプレートの作成

#### 方法A: スクリプトで生成（python-pptx ベース）

```bash
# サンプルテンプレートを再生成（コードでカスタマイズ後に実行）
uv run --project scripts/deckgen \
    python scripts/deckgen/tools/make_brand_template.py
# → scripts/deckgen/templates/sample-brand.pptx を更新
```

`scripts/deckgen/tools/make_brand_template.py` の `BRAND_*` 定数を自社カラーに書き換えてから実行する。

#### 方法B: PowerPoint で作成（推奨）

1. PowerPoint で既存の `.pptx` または空のプレゼンを開く
2. 「表示」→「スライドマスター」でマスターの背景・フォント・配色を設定
3. 「ファイル」→「名前を付けて保存」→「PowerPoint テンプレート（.potx）」で保存
4. 保存した `.potx` を `--template` に指定

```bash
uv run --project scripts/deckgen -m deckgen <slug> --template path/to/brand.potx
```

#### テンプレートに含めるべき内容

| 設定項目 | 場所 | deckgen への影響 |
|---------|------|----------------|
| スライドマスター背景色 | スライドマスター | `--template` 時の背景として使われる |
| フォント（テーマフォント） | テーマ設定 | deckgen は直接フォント名を指定するため影響小 |
| カラースキーム | テーマ設定 | deckgen は RGB を直接指定するため影響小 |

> **注意**: テンプレートファイル内に実際のスライドを含めないこと。`Presentation(template_path)` はテンプレートのスライドをそのまま引き継ぐため、テンプレートにスライドが含まれると生成物に混入する。

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
  templates/
    sample-brand.pptx     # サンプルブランドテンプレート（--template に直接渡せる）
  tools/
    make_brand_template.py  # sample-brand.pptx を再生成するユーティリティ
  tests/test_builder.py
```
