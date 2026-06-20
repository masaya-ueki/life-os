# content-sales — 販売管理

> **構成根拠**: [ADR-0002 複数領域を Modular Monolith × Bounded Context で共存させる](../../docs/adr/0002-modular-monolith-bounded-context.md)

自作ツール等の販売に関する Bounded Context（今後展開予定）。
売上・価格などのロジックが主役になるため **アーキタイプA（軽量ヘキサゴナル）** を採る。

> パッケージ名（import 名）は `content_sales`（アンダースコア）、ディレクトリ・配布名は `content-sales`（ハイフン）。

## ユビキタス言語（この領域の用語）

| 用語 | 意味 | 備考 |
|------|------|------|
| Product | 販売物（自作ツール等） | media の素材とは別概念 |
| Sale | 1 件の販売 | |

## 内部構成

```
src/content_sales/
├── domain/        # Entity / 値オブジェクト / 集約 + 純粋ロジック
├── application/   # ユースケース（サービス層）
├── adapters/      # CLI・永続化・他領域連携（acl/）
└── public.py      # ★他領域に公開する唯一の契約
data/
tests/
```

## 境界（Context Map メモ）

- 他領域からは `from content_sales.public import ...` のみ許可。
- 現状、他領域への依存は無し。
