# 表現: 強調（emphasis）

1枚で**たった1つの強いメッセージ**を伝える表現。山場・効果・キーメッセージに使う。

## いつ使うか
- 大きな数値・KPI（「導入後、インシデント -80%」）
- キーメッセージ・スローガン（章の主張を1文で）
- 印象的な引用（顧客の声・原則）
- Before-After の結果数値

## 型
1. **ビッグナンバー**: 巨大な数値＋単位＋一言ラベル。スライド中央。
2. **KPI カード**: 数値カードを 2〜4 枚並べ、各指標を1枚に。
3. **キーメッセージ**: 大きな1文を中央に。背景は単色 or アクセント。
4. **引用**: 大きな引用符＋本文＋出典。

## HTML/CSS 実装指針
- **とにかく大きく**: 数値は 96px〜160px。`font-weight: 800`、`--accent` 色。単位・ラベルは小さく添える。
- 中央寄せ（`display:flex; align-items:center; justify-content:center; flex-direction:column`）。
- 情報を**削る**: このスライドに箇条書きを足さない。1メッセージのみ。
- KPI カードは `grid` で等幅。各カードに「数値＋ラベル＋増減（▲▼色付き）」。
- 引用は `blockquote`、装飾の大きな `"`（`::before`）。
- 背景にアクセント面を敷くと山場感が出る（`.slide--emphasis { background: var(--accent); color:#fff }`）。

```html
<section class="slide slide--emphasis">
  <p class="big-number">-80<span class="unit">%</span></p>
  <p class="big-label">{summary}</p>
</section>

<!-- KPI -->
<section class="slide">
  <h2>{title}</h2>
  <div class="kpis">
    <div class="kpi"><span class="kpi__num">3.2x</span><span class="kpi__label">生産性</span></div>
    ...
  </div>
</section>
```

## outline.yml の data
```yaml
expression: emphasis
data:
  mode: big-number       # big-number | kpi | message | quote
  # big-number:
  value: "-80"
  unit: "%"
  label: "導入後のインシデント件数"
  # kpi: cards: [{ num:"3.2x", label:"生産性", delta:"▲" }]
  # message: text: "セキュリティは設計で作る"
  # quote: text: "...", cite: "— 出典"
```
