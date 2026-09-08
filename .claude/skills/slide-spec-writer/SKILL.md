---
name: slide-spec-writer
description: Claude Design で作るスライドの「指示書」をYAML形式で生成し、docs/design/decks/<案件名>/spec.yml としてリポジトリに保存するスキル。[[スライド指示書]] というコマンドが含まれるとき、または「スライドの指示書を作りたい」「スライド構成をymlで書いて」「Claude Designでスライドを作りたい」「プレゼンの全体構成とページテンプレートを整理したい」「資料のデザインルールを決めたい」といったリクエストが来たときは必ずこのスキルを使用すること。デザイン値は docs/design/design-system-notion-like.md を参照し指示書には複製しない。全体構成（deck）と17種のページテンプレートを持つYAMLを出力する。既存の指示書の修正・テンプレート追加・内容の割り付け依頼でも使用する。
---

# スライド指示書ライター

Claude Design に渡すスライド指示書（YAML）を作り、**リポジトリに保存する**。
指示書は「デザインルール」「全体構成」「ページテンプレート」「内容」の4層で構成され、
内容が差し替わってもデザインの一貫性が崩れないようにするのが目的。

life-os では**プログラムで pptx / HTML を生成しない**。作るのは指示書までで、
実際の作図は [Claude Design](https://claude.ai/design) が行う（[ADR-0013](../../../docs/adr/0013-deprecate-presentation-adopt-claude-design.md)）。

## 出力の基準ファイル

`assets/slide_spec_template.yml` が正式なテンプレート。**必ず最初にこのファイルを読み**、
構成・キー名・コメントの書式をそのまま踏襲する。勝手にキー名を変えたり階層を組み替えたりしない。
案件固有の要件は既存キーの値として表現し、それでも足りない場合のみキーを追加する。

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

### 1. 素材の有無を確認する

ユーザーが内容（議事メモ・データ・箇条書き・ファイル）を持っているかで分岐する。

- **内容がある** → 内容を読み、後述の割り付けまで一気に行う
- **内容がまだない** → テンプレートだけを先に出す。`content` セクションは空のまま保存し、
  「内容をもらえれば割り付けまでやります」と伝える

不足情報は最大3点までに絞って聞く。目的・対象者・枚数の3つが揃えば着手できるので、
それ以上の詰めは指示書を出してから行うほうが速い。

**画像・xlsx などのファイルを渡されたら** `materials/` に置き、`materials:` セクションに
パス・種別・使うページ番号・note（何のデータか、出典と期間）を書く。
社外秘・個人情報を含むファイルはコミット前にユーザーへ確認し、伏せる箇所は
`※既存資料を記載` のようなプレースホルダにする。

### 2. デザインは参照する（複製しない）

デザイン値の正本は [docs/design/design-system-notion-like.md](../../../docs/design/design-system-notion-like.md) の**1ファイルだけ**。
指示書の `design_system` には `source` を書き、色やフォントの値をコピーしない（[ADR-0016](../../../docs/adr/0016-claude-design-design-system-file.md)）。

案件固有の事情で正本から外す場合のみ `design_system.overrides` に**理由つきで**書く。
「見栄えのため」は理由にならない。**構造とルールは変えない。**

**図表3色ルール**が最重要。グラフ・表・図は正本の `chart_palette` の3色で表現する。

| 色 | 役割 |
|---|---|
| 1色目（accent） | 注目させたい系列・推奨案・現在地 |
| 2色目（グレー） | 比較対象・その他 |
| 3色目（ライトグレー） | 母数・背景・非注目 |

構成説明図や状態遷移など、色が意味の識別そのものを担う場合だけ4色目以降を許可し、
その旨を `overrides` に明記する。

### 3. 全体構成（deck）を組む

`deck.flow_pattern` を選び、`deck.pages` にテンプレートIDを並べる。
既定は**結論先出し**（表紙 → サマリ → 目次 → 章扉 → 本編 → ネクストアクション → Appendix）。

- 社内の意思決定資料 → 結論先出し
- 顧客提案 → 課題→解決
- 報告・振り返り → 時系列

章扉（T03）は3枚以上の章がある場合のみ入れる。枚数が10枚未満なら目次と章扉は省いてよい。

### 4. 内容を割り付ける

素材を `content.raw_input` に貼り、各ページの `values` を埋める。割り付けの判断基準：

- 主張を1つ述べる → `T04_message`
- 並列の要素を3つ以上並べる → `T05_bullets` / `T06_cards`
- 複数案を評価軸で比べる → `T07_table`（表の下に必ず結論を置く）
- 数値で語る → `T10_chart`（1ページ1グラフ、系列3つまで）
- 順序に意味がある → `T09_process`

**1ページ1メッセージ**を守る。1枚に2つの主張が入りそうなら分割する。
逆に、内容が薄いページは隣のページに統合する。

### 5. 保存して報告する

`docs/design/decks/<案件名>/spec.yml` に書き込む。上書きになる場合は先に差分を伝える。

チャット側の説明は3〜5行だけ。保存先パス・構成ブロックの一覧・次にユーザーがすべきこと
（内容を渡す／deck を調整する／Claude Design に渡す）を伝える。**指示書の中身を再掲しない。**

Claude Design に渡すものは次の2つ（素材があれば3つめも）。

1. `docs/design/decks/<案件名>/spec.yml`
2. `docs/design/design-system-notion-like.md`
3. `materials/` 配下のファイル

## 納品前チェック

- `docs/design/decks/<案件名>/spec.yml` に保存したか（`/mnt/user-data/outputs/` で終わっていないか）
- `design_system` に色やフォントの**値を複製していない**か（`source` 参照になっているか）
- 各ページの `key_message` だけを順に読んで筋が通るか
- 使用色が3色に収まっているか（逸脱があれば `overrides` に理由が書かれているか）
- 数値ページに出典と期間があるか
- 1ページに主張が2つ入っていないか
- 最終ページに担当・期限・依頼事項があるか
- 素材ファイルに社外秘・個人情報が含まれていないか

## テンプレート一覧（詳細は `assets/slide_spec_template.yml` 参照）

T01 表紙 / T02 目次 / T03 章扉 / T04 メッセージ＋本文 / T05 要点リスト / T06 並列カード /
T07 比較表 / T08 2軸マトリクス / T09 プロセス / T10 グラフ＋示唆 / T11 数値ハイライト /
T12 タイムライン / T13 Before-After / T14 一言強調 / T15 サマリ / T16 ネクストアクション / T17 Appendix

案件固有のテンプレートが必要になったら、既存の書式（`id` / `name` / `use_when` /
`layout`（ASCIIワイヤー） / `slots` / `rules`）に合わせて追加する。IDは T18 以降の連番。

## 関連

- [docs/design/README.md](../../../docs/design/README.md) — デザイン資産の索引と使い方
- [docs/design/design-system-notion-like.md](../../../docs/design/design-system-notion-like.md) — デザインシステム（正本）
- [ADR-0016](../../../docs/adr/0016-claude-design-design-system-file.md) — 入力を docs/design/ に集約する判断
