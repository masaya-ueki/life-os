# rule — ディレクトリ構成論ルール

> **適用対象**: life-os リポジトリ全体の**構造（ディレクトリ・ファイル配置・ドキュメント）**

このディレクトリは「life-os の**リポジトリはどうあるべきか**」を定めるルール集です。
時間が経っても構造が崩れないよう、判断基準を明文化し、`scripts/check_structure.py` と
日次の [directory-keeper](../.claude/skills/directory-keeper/SKILL.md) で機械的に検査します。

> **設計根拠**: [ADR-0005 ディレクトリ統治と日次 directory-keeper](../docs/adr/0005-directory-governance-daily-keeper.md)

---

## `rule/` と `guides/` の違い（役割分担）

二重管理を避けるため、責務を明確に分ける。

| | 問い | 例 |
|---|---|---|
| **`rule/`（ここ）** | リポジトリは**どうあるべきか**（構造ガバナンス） | 配置・命名・ドキュメント重複禁止 |
| [`guides/`](../guides/) | 人は**どう働くか**（プロセス） | Issue 運用・ブランチ/コミット規約 |
| [`docs/adr/`](../docs/adr/) | **なぜ**その設計か（意思決定の記録） | 構成の採用理由 |

---

## ルール一覧

| ファイル | 扱う対象 |
|---|---|
| [directory-structure.md](./directory-structure.md) | 正典ディレクトリ構成・新規ファイルの置き場所・領域の追加 |
| [documentation.md](./documentation.md) | README / ドキュメントの単一の真実・重複禁止・Diátaxis |
| [naming.md](./naming.md) | ディレクトリ・ファイル・モジュールの命名規約 |
| [maintenance.md](./maintenance.md) | 「きれい」の定義と directory-keeper の監査チェックリスト |

---

## 大原則（5つ)

調査した一般的ベストプラクティスのうち、life-os に効くものだけを採用する。

1. **Screaming Architecture（叫ぶ構造）** — 構造は「何をやるか＝領域」を表す。技術レイヤ（`models/` `services/` 等）でトップを切らない。→ life-os の `domains/`（`task/` `travel/` `media/` `content-sales/` `english/`）が体現。
2. **単一責務（高凝集）** — 1 ディレクトリ＝1 つの変更理由、1 ファイル＝1 概念。関連物は近くにまとめる。
3. **単一の真実（DRY for docs）** — 事実の正本は 1 箇所だけ。**他所では複製せずリンクする**（→ [documentation.md](./documentation.md)）。
4. **規約優先（convention over configuration）** — 領域内は archetype ごとに同じ形を保ち、地図がなくても置き場所が推測できる状態にする。
5. **腐らせない（fitness functions）** — ルールは文章だけにせず、`scripts/check_structure.py`・[`.importlinter`](../.importlinter)・日次 keeper で検査して破綻を防ぐ。

> 個人知識管理（PARA / Johnny.Decimal / Zettelkasten）からは“原則だけ”輸入する：
> 不要物は消すよりまず**アーカイブ**・**深さは浅く一定に**・**1ファイル1概念**・**リンクで繋ぐ**。
> 番号プレフィックス等の流儀はツールと相性が悪いため採用しない。

---

## 新規ファイル・ディレクトリの置き場所（判断フロー）

```
追加したいものは何か？
├─ 特定の生活領域（タスク/旅行/メディア/販売…）に属するコードか？
│    → その領域ディレクトリの内部に置く（archetype に従う）。詳細: directory-structure.md
├─ コードを持たない成果物・資料か？
│    ├─ 「なぜ」の意思決定 → docs/adr/
│    ├─ 人向けの手順・運用ルール（how-to） → guides/
│    ├─ 構造ルール（どうあるべきか） → rule/（ここ）
│    └─ その他の content 領域（例: presentation/） → 専用トップレベル
├─ 開発/運用を補助するスクリプトか？ → scripts/
├─ Claude Code のエージェント/スキルか？ → .claude/agents · .claude/skills
├─ GitHub の設定（Issue/PR/workflow）か？ → .github/
└─ 上記いずれでもない単発ファイルをルート直下に置きたい
     → 原則禁止。置き場所が無いなら設計を見直す（root hygiene: directory-structure.md）
```

新しい**領域（Bounded Context）** を足す手順は [ADR-0002](../docs/adr/0002-modular-monolith-bounded-context.md) に従う（ここでは重複させない）。
