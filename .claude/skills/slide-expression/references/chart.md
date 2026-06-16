# 表現: グラフ・データ（chart）

量・割合・推移などの**数値**を視覚化する表現。

## いつ使うか・種類の選択
| 見せたいこと | グラフ | 補足 |
|------------|-------|------|
| 大小の比較 | 棒グラフ（bar） | 項目間の量を比較。横棒は項目名が長い時 |
| 時間推移・傾向 | 折れ線（line） | 連続的な変化。複数系列で比較 |
| 構成比・内訳 | 円 / ドーナツ（pie） | 合計100%の割合。要素は5個以内 |
| 累積・内訳の推移 | 積み上げ棒（stacked） | 内訳の時系列変化 |
| 単一の重要数値 | → `emphasis` を使う | 1つの数字は強調表現で |

## HTML/CSS 実装指針（依存なし）
- ライブラリは使わない。**インライン SVG** か **CSS のみ**で描く。
- **棒グラフ**: 各バーを `div` の高さ（`height: 70%`）or SVG `<rect>`。値ラベルをバー上に。
- **折れ線**: SVG `<polyline points="...">` + 軸 `<line>` + 点 `<circle>`。`viewBox` で座標系を固定。
- **円グラフ**: SVG `<circle>` の `stroke-dasharray` テクニック、または `conic-gradient(--accent 0 40%, --muted 40% 100%)` で CSS のみ。
- 軸ラベル・凡例・単位を必ず付ける。最大値/合計を明示。
- 色は系列ごとに `--accent` 系の濃淡。強調したい系列だけ濃く。
- データが少なければ「表＋強調数値」でも十分（無理にグラフ化しない）。

```html
<section class="slide">
  <h2>{title}</h2>
  <p class="lead">{summary}</p>
  <svg class="chart" viewBox="0 0 400 240" role="img" aria-label="{title}">
    <!-- bars / polyline をデータから生成 -->
  </svg>
  <p class="chart__note">出典 / 単位</p>
</section>
```

## outline.yml の data
```yaml
expression: chart
data:
  type: bar              # bar | line | pie | stacked
  unit: "%"
  series:
    - { label: "2024", value: 30 }
    - { label: "2025", value: 65 }
  # line/stacked は複数系列:
  # series: [{ name:"A", points:[{x:"1月",y:10}, ...] }]
  note: "出典: ..."
```
