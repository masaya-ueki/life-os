# 表現: フロー・プロセス（flow）

順序・手順・流れのある事柄を**段階**で見せる表現。

## いつ使うか・種類
| 見せたいこと | 型 | 補足 |
|------------|----|------|
| 手順・段階 | ステップ（横/縦フロー） | 1→2→3。矢印で進行 |
| 時系列・経緯 | タイムライン | 日付軸に出来事を配置 |
| 繰り返す循環 | サイクル | PDCA 等、円環で戻る |
| 分岐・条件 | フローチャート | 判断ノードで分岐 |

## HTML/CSS 実装指針
- **横ステップ**: `display: flex` でノードを並べ、ノード間に矢印（`::after { content: "→" }` or SVG）。各ノードは番号バッジ＋見出し＋短文。
- **縦タイムライン**: 左に縦線（`border-left`）、各イベントを `::before` の丸ポイントで打つ。日付を左、内容を右。
- **サイクル**: 4要素なら2x2配置＋外周の循環矢印（SVG 円弧 + arrowhead）。または CSS `transform: rotate` で放射配置。
- ステップ番号を `①②③` か円形バッジで明示。**現在地/重要ステップ**は `--accent` で強調。
- 進行方向を一貫させる（左→右、上→下）。

```html
<section class="slide">
  <h2>{title}</h2>
  <p class="lead">{summary}</p>
  <ol class="flow flow--steps">
    <li class="flow__step"><span class="flow__no">1</span><h3>...</h3><p>...</p></li>
    <li class="flow__step"><span class="flow__no">2</span><h3>...</h3><p>...</p></li>
  </ol>
</section>
```
CSS: `.flow--steps { display:flex; gap } .flow__step + .flow__step::before { content:"→" }`

## outline.yml の data
```yaml
expression: flow
data:
  type: steps            # steps | timeline | cycle
  orientation: horizontal # horizontal | vertical
  steps:
    - { label: "検知", desc: "..." }
    - { label: "対応", desc: "..." }
    - { label: "復旧", desc: "..." }
  # timeline は date 付き: steps: [{ date:"2025-01", label:"...", desc:"..." }]
```
