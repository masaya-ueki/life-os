# タスク汎用セット定義

> PBI 配下にまとめて Task を作るための「汎用セット」定義。
> `scrum-notion-task-set` サブエージェントが参照する。新しいセットは今後この下に追記していく運用（エージェント本体にはハードコードしない）。
>
> 各 Task の入力パラメータ・固定値・自動判定ルールは [`scrum-notion-task`](../../../../.claude/skills/scrum-notion-task/SKILL.md) に従う。ここでは各セットの構成（Task 名と既定 Category）のみを定義する。

## 機能追加

| # | Task Name | Category（既定） |
|---|---|---|
| 1 | 影響調査 | task |
| 2 | 設計 | task |
| 3 | 製造・テスト | task |
| 4 | レビュー | task |
| 5 | レビュー指摘反映 | task |
| 6 | リリース準備 | task |
| 7 | リリース | task |

> Category の既定値はすべて `task`。個別に `todo` / `meeting` にしたい場合は作成時のヒアリングで上書きする。
