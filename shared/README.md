# shared — Shared Kernel

領域非依存の**最小限の基盤**のみを置く workspace member。

> **設計根拠**: [ADR-0002 複数領域を Modular Monolith × Bounded Context で共存させる](../docs/adr/0002-modular-monolith-bounded-context.md)

## 責務

- ID 型・`Result` 型・日付ユーティリティなど、**どの領域にも属さない**基盤だけを提供する。
- 「タスク」「場所」などの**ドメイン概念をここに入れない**（入った時点で設計の綻び）。
- いかなる領域にも依存しない（[`.importlinter`](../.importlinter) で強制）。

## 構成

```
shared/
└── src/shared/
    ├── ids.py      # ID 型
    ├── result.py   # Result 型
    └── time.py     # 日付・時刻
```

## 開発

ルートの uv workspace から実行する（コマンドの正本は [ルート README](../README.md)）。
