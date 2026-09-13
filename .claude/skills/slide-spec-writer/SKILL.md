---
name: slide-spec-writer
description: Claude Design で作るスライドの「指示書」をYAML形式で生成し、docs/design/decks/<案件名>/spec.yml としてリポジトリに保存するスキル。[[スライド指示書]] というコマンドが含まれるとき、または「スライドの指示書を作りたい」「スライド構成をymlで書いて」「Claude Designでスライドを作りたい」「プレゼンの全体構成を整理したい」「資料のデザインルールを決めたい」といったリクエストが来たときは必ずこのスキルを使用すること。指示書にはページごとの主張・外せない事実・材料・講師メモと、章ごとのページ上限を書き、完成文やページテンプレート（レイアウト）は書かない。情報の順序は資料タイプ別の型（references/deck-types/）に従い、デザイン値は docs/design/design-system-notion-like.md を参照して複製しない。既存の指示書の修正・内容の書き換え・資料タイプの型の追加依頼でも使用する。
---

# スライド指示書ライター

Claude Design に渡すスライド指示書（YAML）を作り、**リポジトリに保存する**。

life-os では**プログラムで pptx / HTML を生成しない**。作るのは指示書までで、
実際の作図は [Claude Design](https://claude.ai/design) が行う（[ADR-0013](../../../docs/adr/0013-deprecate-presentation-adopt-claude-design.md)）。

指示書の形式の根拠は [ADR-0017](../../../docs/adr/0017-slide-spec-claim-materials-deck-types.md)（置き場所の根拠は [ADR-0016](../../../docs/adr/0016-claude-design-design-system-file.md)）。

## 構成

```
.claude/skills/slide-spec-writer/
├── SKILL.md
├── assets/slide_spec_template.yml     # 指示書の正式な雛形（キー名と書式の基準）
└── references/deck-types/<種類>.md     # 資料タイプ別の型（Claude Design に渡す）
```

- `assets/slide_spec_template.yml` を**必ず最初に読み**、キー名・階層・コメントの書式を踏襲する。
  案件固有の要件は既存キーの値で表現し、キーを勝手に増やしたり組み替えたりしない
- 指示書は `meta` / `design_system` / `deck`（資料タイプ・ページ上限・章）/ `constraints` / `materials` / `content`（素材とページごとの指示）で構成する
- `references/deck-types/` にある型だけが「資料タイプ別の型」。現在は [handson](./references/deck-types/handson.md)

## 判断基準: それが無いと読み手が困るか

**「何を・どのくらい」は指示書で決め、「どう見せるか・どう書くか」は Claude Design に任せる。**
完成文と枠を渡すと Claude Design は転記するだけになり、内容が簡素になる。一方で何も決めないとページ数が膨らむ。

| 指示書で決める（無いと読み手が困る） | Claude Design に任せる（見た目が変わるだけ） |
|---|---|
| 情報の順序（ページの並び・型の順序） | レイアウト・配置 |
| 外せない事実・固有名詞・数値（`must_include`） | 図の種類（表にするか、フローにするか） |
| 量（全体と章ごとのページ上限） | 見出し・本文の言い回し |
| 書いてはいけないこと（`avoid`） | 装飾・強調の付け方 |
| 講師メモ（`speaker_notes`） | 色・文字サイズ（デザインシステムが決める） |

ページテンプレート（ASCII のレイアウト図・slots・rules）は作らない。「参考」として一覧を残しても、結局それが採用されて表現の幅が狭まる。

## 保存先（重要）

**このリポジトリ内で作業しているときは、必ず案件ディレクトリに直接書き込む。**
`/mnt/user-data/outputs/` に置いて終わりにしない（セッション終了で消える）。

```
docs/design/decks/<案件名>/
├── spec.yml         # 指示書（このスキルの出力）
└── materials/       # 素材（画像・xlsx・元資料）※あるときだけ作る
```

- `<案件名>` は kebab-case（例: `data-analysis-platform`）
- **1案件1ディレクトリ**。ファイル数は固定しない。素材が増えれば `materials/` に足す
- 書き出した PDF / PPTX / HTML は **コミットしない**。正本は Claude Design 側に置く
  （[R-STRUCT-4](../../../rule/directory-structure.md)）
- 既存案件の修正依頼なら、新規作成せず既存の `spec.yml` を編集する

life-os の外（claude.ai のチャットなど）で使う場合はリポジトリに書けないため、
`/mnt/user-data/outputs/` に `.yml` と `.txt` の両方を出し（.txt を先に渡す）、
「残すなら `docs/design/decks/<案件名>/spec.yml` に置いてください」と伝える。

## 進め方

### 1. 素材を確認する

ユーザーが内容（議事メモ・データ・箇条書き・ファイル）を持っているかで分岐する。

- **内容がある** → `content.raw_input` に貼り、ページごとの指示まで一気に書く
- **内容がまだない** → `meta` と `deck` だけを先に書いて保存し、「内容をもらえればページごとの指示まで書きます」と伝える

不足情報は最大3点までに絞って聞く。目的・対象者・資料の種類が揃えば着手できる。

**画像・xlsx などのファイルを渡されたら** `materials/` に置き、`materials:` セクションに
パス・種別・使うページ番号・note（何のデータか、出典と期間）を書く。

**社外秘の扱い**: 社外秘・個人情報を含むファイルはコミット前にユーザーへ確認する（リポジトリは公開の場合がある）。
コミットを見送る素材も `materials:` には書き、note に「コミット保留。手元のファイルを Claude Design に渡す」と明記する。
伏せる箇所は `※既存資料を記載` のようなプレースホルダにする。

### 2. 資料タイプを選び、型を読む

`references/deck-types/` に該当する種類があれば `deck.deck_type` に書き、**その型ファイルを読んでから**ページを組む。
ページの並びは型の「全体の流れ」に、ページ内の情報の順序は型の各ページの順序に合わせる。`role` には型にある役割名を書く。

該当する型が無ければ `deck_type` は空のままにする（後述の「新しい種類の資料の運用」）。

### 3. 量を決める（deck と章の上限）

`deck.max_pages`（全体）と `deck.chapters[].max_pages`（章ごと）を先に決める。持ち時間があれば `minutes` も書く。

- 上限は「伝えたいことが入る最小のページ数」で決める
- **上限を超えそうなら分割しない。優先度の低い情報から削る**（分割を許すとページ数が膨らむ）
- 1 つの概念は 1 ページ。同じ概念を「①」「②」に分けない

### 4. ページごとの指示を書く

各ページに `page`（ページ番号）/ `chapter` / `role`（任意）/ `message` / `must_include` / `notes` / `avoid` / `speaker_notes` を書く。

| キー | 書くこと | 書かないこと |
|---|---|---|
| `message` | 伝えたい主張 1 つ | 見出しや本文にそのまま載せる完成文 |
| `must_include` | 外せない事実・固有名詞・数値・パス（短く） | 言い回しを整えた箇条書き |
| `notes` | 材料・背景・例・口頭で話すこと（表示する量より多くてよい） | レイアウトや図の指定 |
| `avoid` | 誤解を招く表現・古い前提・他ページで扱う話 | デザインの禁止事項（正本にある） |
| `speaker_notes` | 講師メモ。話す要点・時間・注意。**全ページ必須** | — |

資料全体に効く「書いてはいけないこと」（用語の揺れなど）は `constraints.avoid` に書く。

### 5. デザインは参照する（複製しない）

デザイン値の正本は [docs/design/design-system-notion-like.md](../../../docs/design/design-system-notion-like.md) の**1ファイルだけ**。
指示書の `design_system` には `source` を書き、色・フォント・文字サイズ・余白の値をコピーしない（[ADR-0016](../../../docs/adr/0016-claude-design-design-system-file.md)）。
型ファイルにも値を書かない。

案件固有の事情で正本から外す場合のみ `design_system.overrides` に**理由つきで**書く。
「見栄えのため」は理由にならない。

**図表3色ルール**が最重要。グラフ・表・図の色は正本の
[「図表 3 色ルール」](../../../docs/design/design-system-notion-like.md#図表-3-色ルール最重要)に従う。
色が意味の識別そのものを担う図で4色目以降が要る場合は、その旨を `overrides` に明記する。

### 6. 保存して報告する

`docs/design/decks/<案件名>/spec.yml` に書き込む。上書きになる場合は先に差分を伝える。

チャット側の説明は3〜5行だけ。保存先パス・章と上限の一覧・次にユーザーがすべきことを伝える。**指示書の中身を再掲しない。**

## Claude Design に渡すもの

1. `docs/design/decks/<案件名>/spec.yml`
2. デザインシステム（`design_system.source`）
3. `deck.deck_type` に対応する型ファイル **1 つだけ**（`references/deck-types/<種類>.md`）
4. `materials:` に書いたファイル

**他の型ファイルは渡さない。** 関係のない型まで渡すと、その型の流れに引っ張られる。`deck_type` が空なら型ファイルは渡さない。

## 新しい種類の資料の運用

型は机上で作らない。実例の無い型は根拠が無く、ページテンプレートと同じ偏りを生む。型は Claude Design の良い出力から逆算して増やす。

1. `deck_type` を空にしたまま指示書を書く（ページの並びと `message` で順序を決める）
2. Claude Design で出力する
3. 良かった出力をユーザーと見ながら、「どの順序で・何が外せなかったか・量はどのくらいか」を相談して型に起こす
4. `references/deck-types/<種類>.md` として追加する。根拠にした出力（書き出したファイル）を「根拠」節に書き、案件の `materials:` から参照する
5. 以降、同じ種類の資料では `deck_type` にその種類を書く

案件の `spec.yml` の中に独自の型やテンプレートを書かない。型を直すときは `references/deck-types/` のファイルを直す。

## 納品前チェック

- `docs/design/decks/<案件名>/spec.yml` に保存したか（`/mnt/user-data/outputs/` で終わっていないか）
- `design_system` や型ファイルに色・フォント・文字サイズの**値を複製していない**か
- `page_templates` / `template` / `values` / `layout` / `slots` を書いていないか
- `message` が表示する完成文になっていないか（主張になっているか）
- 各ページの `message` だけを順に読んで筋が通るか
- **全ページに `speaker_notes` があるか**
- 章ごとのページ数が `max_pages` 以内か。全体が `deck.max_pages` 以内か
- 同じ概念を複数ページに分割していないか
- `deck_type` を書いた場合、ページの並びと `role` が型に沿っているか
- 数値を扱うページの `must_include` に出典と期間があるか
- 素材ファイルに社外秘・個人情報が含まれていないか（含むならコミット保留と note に書いたか）

## 関連

- [docs/design/README.md](../../../docs/design/README.md) — デザイン資産の索引と使い方
- [docs/design/design-system-notion-like.md](../../../docs/design/design-system-notion-like.md) — デザインシステム（正本）
- [ADR-0016](../../../docs/adr/0016-claude-design-design-system-file.md) — 入力を docs/design/ に集約する判断
- [ADR-0017](../../../docs/adr/0017-slide-spec-claim-materials-deck-types.md) — 指示書を「主張＋材料＋資料タイプ別の型」で書く判断
