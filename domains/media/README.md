# media — 画像・動画管理

> **構成根拠**: [ADR-0002 複数領域を Modular Monolith × Bounded Context で共存させる](../../docs/adr/0002-modular-monolith-bounded-context.md)

写真・動画などのメディア資産の整理・管理を行う Bounded Context。
データ（メタ情報）が主役のため **アーキタイプB（薄い構成）** を採る。

## ユビキタス言語（この領域の用語）

| 用語 | 意味 | 備考 |
|------|------|------|
| Asset | 1 つのメディア資産（画像/動画） | |
| Tag | media 内の分類ラベル | task の「タグ」とは別概念。共通化しない |

## 内部構成

```
src/media/
├── models.py   # スキーマ（dataclass / 将来 pydantic 等）
├── index.py    # 整形・検索・自動化
└── public.py   # ★他領域に公開する唯一の契約
data/           # ★主役: メタデータ（JSON/YAML）・索引
tests/
```

## 境界（Context Map メモ）

- 他領域からは `from media.public import ...` のみ許可。
- 例: travel が「旅行に紐づく写真」を扱う場合、travel 側が `media.public` を参照する（media は travel を知らない）。
- データが育って複雑なロジックを持ち始めたらアーキタイプB → A への昇格を検討（別 ADR）。
