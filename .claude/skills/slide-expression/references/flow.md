# 表現: フロー・プロセス（flow）

順序・手順・流れのある事柄を**段階**で見せる表現。

## いつ使うか・種類
| 見せたいこと | 型 | 補足 |
|------------|----|------|
| 手順・段階 | ステップ（横/縦フロー） | 1→2→3。矢印で進行 |
| 時系列・経緯 | タイムライン | 日付軸に出来事を配置 |
| 繰り返す循環 | サイクル | PDCA 等、円環で戻る |
| 分岐・条件 | フローチャート | 判断ノードで分岐 |

## data フィールド仕様

| フィールド | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| `type` | string | 否 | `steps`（default）/ `timeline` / `cycle` |
| `orientation` | string | 否 | `horizontal`（default）/ `vertical` |
| `steps` | list | **必須** | 各ステップのデータ（下記参照） |
| `steps[].label` | string | **必須** | ステップ名（短い見出し、10字以内が理想） |
| `steps[].desc` | string | **推奨** | 1〜2文の補足説明。**省略すると図が空白になる** |
| `steps[].date` | string | 否 | timeline 型で使用。`"2025-01"` など |

### steps[].desc の書き方（重要）
- **必ず書く**: desc を省略するとボックスにラベルのみ表示され情報が薄くなる
- **具体的に**: 「作業する」より「Jira でチケットを作成し担当者を割り当てる」
- **1〜2文**に収める（60字以内が目安）
- **現在形で行動を書く**: 「〜を行う」「〜を確認する」

### 推奨ステップ数
- `horizontal`: **3〜5 ステップ**（6以上は文字が小さくなり読めない）
- `vertical`: **3〜6 ステップ**（縦は多めに詰められる）

## outline.yml の data

### 横フロー（horizontal / steps）
```yaml
expression: flow
data:
  type: steps
  orientation: horizontal
  steps:
    - label: "要件定義"
      desc: "ステークホルダーと目的・スコープ・制約を合意し、受け入れ条件を文書化する"
    - label: "設計"
      desc: "システム構成・DB スキーマ・API インターフェースを決定し、レビューで承認を得る"
    - label: "実装"
      desc: "設計書に従いコードを書き、ユニットテストで各モジュールの動作を確認する"
    - label: "テスト"
      desc: "結合テスト・E2E テストを実施し、バグを修正して品質基準を満たすことを確認する"
    - label: "リリース"
      desc: "ステージング環境で最終確認後、本番デプロイとモニタリング体制を整えてリリースする"
```

### 縦フロー（vertical / steps）
```yaml
expression: flow
data:
  type: steps
  orientation: vertical
  steps:
    - label: "アラート検知"
      desc: "監視ツールが異常を検知し、オンコールエンジニアに PagerDuty で通知する"
    - label: "初動対応"
      desc: "影響範囲を特定し、必要なら機能を切り離してサービスへの被害を最小化する"
    - label: "根本原因調査"
      desc: "ログ・メトリクスを確認し、障害の根本原因を30分以内に特定する"
    - label: "修正・デプロイ"
      desc: "修正コードをレビュー後に本番へデプロイし、回復を確認する"
    - label: "振り返り"
      desc: "インシデントレポートを作成し、再発防止策とタイムラインを共有する"
```

### タイムライン（timeline）
```yaml
expression: flow
data:
  type: timeline
  orientation: horizontal
  steps:
    - date: "2025 Q1"
      label: "企画・要件固め"
      desc: "プロダクトの方向性を決定し、初期要件と KPI を定義する"
    - date: "2025 Q2"
      label: "α版リリース"
      desc: "コアユーザー30名に限定公開し、フィードバックを収集する"
    - date: "2025 Q3"
      label: "β版拡大"
      desc: "フィードバックを反映し、対象ユーザーを500名に拡大する"
    - date: "2025 Q4"
      label: "正式リリース"
      desc: "全ユーザーに公開し、マーケティングキャンペーンと同時展開する"
```

### サイクル（cycle）
```yaml
expression: flow
data:
  type: cycle
  orientation: horizontal
  steps:
    - label: "Plan"
      desc: "目標と達成指標（KPI）を設定し、実施計画を立てる"
    - label: "Do"
      desc: "計画に従って施策を実行し、進捗を記録する"
    - label: "Check"
      desc: "結果を KPI と照合し、目標との差異を分析する"
    - label: "Act"
      desc: "分析から得た改善策を次サイクルの計画に反映する"
```

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
