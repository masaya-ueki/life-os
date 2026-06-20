# travel — 旅行の行先管理

> **構成根拠**: [ADR-0002 複数領域を Modular Monolith × Bounded Context で共存させる](../../docs/adr/0002-modular-monolith-bounded-context.md)

行きたい場所・旅程・記録を管理する Bounded Context。
データ（行先・旅程）が主役のため **アーキタイプB（薄い構成）** を採る。

## ユビキタス言語（この領域の用語）

| 用語 | 意味 | 備考 |
|------|------|------|
| Destination | 行きたい/行った場所 | media の「撮影地」とは別概念。共通化しない |
| Trip | 1 回の旅行（旅程） | |

## 内部構成

```
src/travel/
├── models.py   # スキーマ（dataclass / 将来 pydantic 等）
├── index.py    # 整形・検索・自動化
└── public.py   # ★他領域に公開する唯一の契約
data/           # ★主役: 行先・旅程・記録（JSON/YAML）
tests/
```

## 境界（Context Map メモ）

- 他領域からは `from travel.public import ...` のみ許可。
- 例: travel が「旅行に紐づく写真」を扱う場合、ここから `media.public` を参照する（ACL は不要なほど薄ければ直接でも可だが、翻訳が要るなら adapters 相当を設ける）。
- 現状、他領域への依存は無し。
