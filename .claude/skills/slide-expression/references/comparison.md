# 表現: 比較（comparison）

2つ以上の対象を**対比**して差を際立たせる表現。

## いつ使うか
- Before / After（対策前後・改善前後）
- メリット / デメリット、長所 / 短所
- 案A / 案B / 案C の比較（比較表）
- 自社 / 他社、現状 / 理想

## 型
1. **2カラム対比**: 左右に2項目を並べ、対立軸を明示。Before-After に最適。
2. **比較表**: 行=評価軸、列=対象。○△× や数値でセルを埋める。3対象以上に。
3. **メリデメ（pros/cons）**: 緑＝メリット、赤＝デメリットで色分け。

## HTML/CSS 実装指針
- 2カラムは `display: grid; grid-template-columns: 1fr 1fr; gap`。中央に「→」や「VS」を置くと対比が強調される。
- 比較表は `<table>`。ヘッダ行・ゼブラ、推しの列に `--accent` 背景。○×は文字でなく色付き記号（`✓` 緑 / `✗` 赤）。
- 意味色を使う: 良い=`--good`(緑系)、悪い=`--bad`(赤系)。Before=`--muted`、After=`--accent`。
- カラム上部にラベル見出し（`Before` / `After`）を必ず付ける。

```html
<section class="slide">
  <h2>{title}</h2>
  <p class="lead">{summary}</p>
  <div class="cmp cmp--two">
    <div class="cmp__col cmp__col--before"><h3>Before</h3><ul>...</ul></div>
    <div class="cmp__arrow">→</div>
    <div class="cmp__col cmp__col--after"><h3>After</h3><ul>...</ul></div>
  </div>
</section>
```

## outline.yml の data
```yaml
expression: comparison
data:
  mode: two-column        # two-column | table | pros-cons
  # two-column / pros-cons:
  left:  { label: "Before", items: ["...", "..."] }
  right: { label: "After",  items: ["...", "..."] }
  # table:
  axes: ["評価軸1", "評価軸2"]
  columns:
    - { name: "案A", values: ["○", "高"] }
    - { name: "案B", values: ["×", "低"] }
```
