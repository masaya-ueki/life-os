# 表現: 構造（structure）

要素間の**関係・分類・位置づけ**を空間配置で見せる表現。

## いつ使うか・種類
| 見せたいこと | 型 | 補足 |
|------------|----|------|
| 上下関係・分解 | 階層ツリー | 組織図・構成要素の分解 |
| 2軸での位置づけ | 2x2 マトリクス | 優先度・ポジショニング |
| 重要度の積み上げ | ピラミッド | 土台→頂点。前提の積層 |
| 集合の重なり | ベン図 | 共通点・差分 |
| 分類・一覧 | マトリクス表 | 行列のカテゴリ整理 |

## HTML/CSS 実装指針
- **階層ツリー**: ネストした `ul`／または `grid` で親子を縦配置、コネクタ線は `border` か SVG。
- **2x2 マトリクス**: `grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr`。中央に十字の軸線、四隅に象限ラベル。各セルに項目を配置。軸名を外周に。
- **ピラミッド**: 3〜4 段の台形/三角を重ねる。CSS `clip-path: polygon(...)` か、幅を変えた `div` を積む（下段ほど広い）。
- **ベン図**: 2つの半透明円（`border-radius:50%; mix-blend-mode: multiply` または `opacity`）を重ねる。重なり部にラベル。
- 各領域に**短いラベル**。色で分類を区別。中心/頂点ほど重要と直感させる。

## quadrants の順序契約（matrix-2x2）
`matrix-2x2` の `quadrants` は **4 要素・固定順序**で象限に割り当てる。軸は `axis_x`（→ 右ほど高い）・`axis_y`（↑ 上ほど高い）。**右上＝両軸が高い＝最優先**として強調表示する（HTML・pptx 共通の契約）。

| index | 象限 | axis_x | axis_y | 強調 |
|-------|------|--------|--------|------|
| `quadrants[0]` | 右上 | 高 | 高 | **最優先（accent 強調）** |
| `quadrants[1]` | 左上 | 低 | 高 | — |
| `quadrants[2]` | 右下 | 高 | 低 | — |
| `quadrants[3]` | 左下 | 低 | 低 | — |

順序は `[右上, 左上, 右下, 左下]`。HTML レンダラ・pptx レンダラ（deckgen）はともにこの契約に従う。要素が4未満なら不足分は空セルとして扱う。

```html
<section class="slide">
  <h2>{title}</h2>
  <p class="lead">{summary}</p>
  <div class="matrix matrix--2x2">
    <span class="matrix__axis-x">→ {x軸}</span>
    <span class="matrix__axis-y">→ {y軸}</span>
    <div class="matrix__cell">象限1</div> ... 4セル
  </div>
</section>
```

## outline.yml の data
```yaml
expression: structure
data:
  type: matrix-2x2       # tree | matrix-2x2 | pyramid | venn | matrix-table
  # matrix-2x2:
  axis_x: "緊急度"
  axis_y: "重要度"
  # 順序固定: [右上, 左上, 右下, 左下]。右上(=最優先)を accent 強調。
  quadrants: ["最優先", "計画的に", "委譲", "やらない"]
  # pyramid: layers: ["土台:...", "中:...", "頂点:..."]  # 先頭=土台(最下段), 末尾=頂点
  # tree: root: "...", children: [{name:"...", children:[...]}]  # root+第1階層をコネクタ線で接続
  # venn: sets: ["A","B"], overlap: "共通"  # 2集合の半透明な重なり円。重なり部に overlap
```
