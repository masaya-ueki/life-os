# task — タスク管理

> **構成根拠**: [ADR-0002 複数領域を Modular Monolith × Bounded Context で共存させる](../../docs/adr/0002-modular-monolith-bounded-context.md)

日々のやること・プロジェクト・進捗を管理する Bounded Context。
ロジックが主役のため **アーキタイプA（軽量ヘキサゴナル）** を採る。

## ユビキタス言語（この領域の用語）

| 用語 | 意味 | 備考 |
|------|------|------|
| Task | 1 件のやること | media の「タグ」等とは無関係。この領域内でのみ通用する |
| Status | 状態（例: todo / doing / done） | |

> 同じ単語でも他領域とは意味が異なる。共通化しないこと（ADR-0002）。

## 内部構成

```
src/task/
├── domain/        # Entity / 値オブジェクト / 集約 + 純粋ロジック
├── application/   # ユースケース（サービス層）
├── adapters/      # 外界との接続
│   ├── cli.py        # 入力: CLI
│   ├── repository.py # 永続化: data/ への読み書き
│   └── acl/          # 他領域参照の腐敗防止層（Anti-Corruption Layer）
└── public.py      # ★他領域に公開する唯一の契約（境界）
data/              # この領域のデータ
tests/
```

## 境界（Context Map メモ）

- 他領域からは `from task.public import ...` のみ許可（内部 import は import-linter で禁止）。
- この領域が他領域を参照する場合は `adapters/acl/` で翻訳し、相手の `public` だけを使う。
- 現状、他領域への依存は無し。追加したらこの欄に関係（Customer-Supplier / Conformist / ACL）を 1 行で記す。
