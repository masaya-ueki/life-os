---
name: 調査 Issue
about: 技術調査・原因特定・要件調査などの調査目的の Issue
title: "investigate({scope}): {タイトル}"
labels: "investigation,task"
assignees: ""
---

<!--
## Issue タイトル命名規則（調査 Issue）

調査 Issue は `investigate` type を使用してください。

  investigate({scope}): {タイトル}

### ラベル
本テンプレートでは `investigation` + `task` ラベルが自動付与されます。
追加で **system ラベル**（推奨・0〜複数件）を付与してください。

### scope 一覧（system ラベルと一致）
| scope          | 対象                          |
|----------------|-------------------------------|
| task           | タスク管理                    |
| common         | 横断的・共通基盤              |
| content-sales  | 自作ツール等の販売管理        |
| deps           | 依存パッケージ                |

### タイトル例
- investigate(task): タスク一覧の表示が遅くなる原因調査
- investigate(common): データ保存形式の選定調査
- investigate(content-sales): 販売プラットフォーム連携方法の調査

詳細: [`guides/development-policy/issue-operation-rules.md`](../../guides/development-policy/issue-operation-rules.md)
-->

## 背景

<!-- この調査が必要になった経緯や状況を記載してください -->



## 課題

<!-- 何を調査するのか、調査の目的を具体的に記載してください -->



## 影響範囲

<!-- 調査対象のコンポーネント・ファイル・機能を記載してください -->

-

## 内容

<!-- 調査方法・調査手順・調査した内容をフリーフォーマットで記載してください -->
<!-- ※ 調査 Issue のため、対応方針の理由記載は不要です -->

### 調査方法

<!-- どのように調査するか -->



### 調査詳細

<!-- 調査した内容・ログ・資料など -->



## 結果

<!-- 調査完了後に記載 / 調査結果・判明した事実・次のアクションを記載してください -->
