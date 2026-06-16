---
name: slide-expression
description: スライド1枚の「表現方法」（比較・グラフ・フロー・構造・強調など）を選び、自己完結HTML/CSSで実装するためのスキル。表現方法ごとの参照ファイル（references/）に詳細な型と実装指針を持つ索引スキル。Use when: スライドの図解・レイアウトを決める、比較表/グラフ/フロー図/マトリクスを作る、数値を強調する、outline.yml の expression を選ぶ、yml を HTML 化する。Triggers on: スライド表現, 図解, 比較表, グラフ, フロー図, ダイアグラム, マトリクス, 強調, slide expression, HTML スライド化.
---

# スライド表現スキル（索引）

スライド1枚を**どう見せるか**を決め、依存ライブラリなしの自己完結 HTML/CSS で実装するためのスキル。構成（順序・論理）は [`slide-structure`](../slide-structure/SKILL.md) が担当し、本スキルは**1枚の表現**に集中する。

各表現方法の「いつ使うか・型・HTML/CSS実装・必要データ(`data`)」は `references/` の各ファイルに詳述する（progressive disclosure: 必要な表現の参照ファイルだけ読む）。

---

## 表現の早見表（expression 値の選び方）

`outline.yml` の各スライドの `expression` に設定する値と、対応する参照ファイル。

| expression | いつ使うか | 参照ファイル |
|-----------|-----------|-------------|
| `title` | 表紙・章扉。タイトルとサブタイトルのみ | （本ファイル末尾の共通レイアウト参照） |
| `bullet` | 背景・アジェンダ・まとめ。要点の箇条書き | （同上） |
| `comparison` | 2つ以上を対比。Before/After・メリデメ・比較表 | [comparison.md](references/comparison.md) |
| `chart` | 量・割合・推移を見せる。棒/折線/円/KPI | [chart.md](references/chart.md) |
| `flow` | 順序・手順・流れ。ステップ/タイムライン/サイクル | [flow.md](references/flow.md) |
| `structure` | 関係・分類を見せる。階層/2x2/ピラミッド/ベン図 | [structure.md](references/structure.md) |
| `emphasis` | 1つの強いメッセージ。大きな数値/KPI/引用 | [emphasis.md](references/emphasis.md) |

### 選び方の指針
- **対比したい** → comparison
- **数で語りたい** → chart（推移=折線、内訳=円/積み上げ、大小比較=棒）
- **順番・手順がある** → flow
- **要素の関係・位置づけ** → structure
- **1つだけ強く言いたい** → emphasis
- 上記に当てはまらない説明 → bullet

---

## 共通実装規約（全 expression 共通）

renderer（`slide-html-renderer`）はこの規約に従って自己完結 HTML を生成する。詳細な CSS 方針は [`presentation/templates/base.css.md`](../../../presentation/templates/base.css.md) を参照。

1. **自己完結**: 1つの `index.html` に CSS を `<style>` でインライン。外部 CSS/JS/画像依存なし（SVG はインライン、画像は data URI）。
2. **16:9**: 各スライドは `aspect-ratio: 16 / 9`、基準サイズ 1280×720px を想定。`.slide` クラスで統一。
3. **1スライド1要素**: 1つの `<section class="slide">` が1枚。`page-break-after: always` で印刷時に改ページ。
4. **配色トークン**: CSS 変数（`--bg`, `--fg`, `--accent`, `--muted` 等）で `deck.theme` を切替可能にする。
5. **印刷対応**: `@media print` で操作UIを隠し、`@page { size: 1280px 720px landscape; margin: 0 }` 相当でPDF化できるようにする。
6. **画面操作**: 任意で軽量な JS（キーボード ←/→ でスクロール）を1つだけインライン可。フレームワーク不要。
7. **可読性**: 本文 24px 以上、見出し 40px 以上を目安。1行は折り返さない長さに。

### title / bullet の基本レイアウト

```html
<!-- 表紙 -->
<section class="slide slide--title">
  <h1>メインタイトル</h1>
  <p class="subtitle">サブタイトル</p>
</section>

<!-- 箇条書き -->
<section class="slide">
  <h2>スライド見出し（title）</h2>
  <p class="lead">概要＝主張（summary）</p>
  <ul>
    <li>内容1（content[0]）</li>
    <li>内容2</li>
  </ul>
</section>
```

> `summary` は各スライドの**結論**。`<p class="lead">` 等で見出し直下に必ず置き、1スライド1メッセージを担保する。

---

## レイアウトの一般原則

- **余白を恐れない**: 詰め込まない。1枚に主張1つ。
- **視線の流れ**: 左上 → 右下（Z/F型）。重要要素を左上か中央に。
- **整列**: 要素は左/中央で揃える。グリッドを意識。
- **色は意味で使う**: アクセント色は「強調1色＋対比1色」程度に絞る。`comparison` の良し悪しは緑/赤など意味色で。
- **コントラスト**: 背景と文字のコントラストを確保（暗背景なら明文字）。
