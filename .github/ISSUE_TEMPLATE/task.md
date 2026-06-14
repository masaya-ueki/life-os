---
name: Task Issue
about: ProductBacklog の各フェーズの作業、または単発の保守・修正タスク
title: "{type}({scope}): {タイトル}"
labels: ""
assignees: ""
---

<!--
## この Issue の使い方

この Issue は「Task Issue」として、具体的な作業内容を管理します。

### ラベルの選択（必須）

以下の組み合わせでラベルを付与してください。

#### 1. 種別ラベル（必須・1 件）

| ラベル | 用途 |
|-------|------|
| `bug` | バグ修正対応（type: fix と併用）|
| `task` | 一般タスク（feat / design / docs / chore / refactor / test / ci / perf / investigate と併用）|
| `on-hold` | 保留中の Issue（一時的に作業停止する場合に付与）|

#### 2. type ラベル（必須・1 件）

タイトルの type と同じものを 1 件付与（例: `type: feat`）

#### 3. system ラベル（推奨・0〜複数件）

対象領域を 0〜複数件付与（例: `system: task`, `system: content-sales`）

#### 4. 補助ラベル（必要時）

- ProductBacklog Issue（親 Issue）の Sub-issue として作成する場合: 補助ラベル不要
- 単発タスク・1日以内の保守作業で ProductBacklog が不要な場合: `no-product-backlog` ラベルを付与

詳細: [`guides/development-policy/issue-operation-rules.md`](../../guides/development-policy/issue-operation-rules.md)

### Issue タイトル命名規則

Conventional Commits と同じ形式を使用してください。

  {type}({scope}): {タイトル}

### type 一覧
| type       | 用途                                                   |
|------------|--------------------------------------------------------|
| design     | 設計フェーズの作業（データ構造設計・画面設計など）     |
| feat       | 新機能の追加（実装フェーズ）                           |
| fix        | バグ修正                                               |
| test       | テストの追加・修正（テストフェーズ）                   |
| docs       | ドキュメントの追加・更新                               |
| refactor   | リファクタリング                                       |
| chore      | ビルド設定・ツール・依存関係                           |
| perf       | パフォーマンス改善                                     |
| ci         | CI/CD 設定の変更                                       |

### scope 一覧（system ラベルと一致）
| scope          | 対象                          |
|----------------|-------------------------------|
| task           | タスク管理                    |
| common         | 横断的・共通基盤              |
| content-sales  | 自作ツール等の販売管理        |
| deps           | 依存パッケージ                |

### タイトル例
- design(task): タスク管理のデータ構造設計
- feat(task): タスク並び替え機能を追加
- feat(content-sales): 販売記録の登録フォームを追加
- fix(task): 完了タスクが再表示される不具合を修正
- chore(deps): 依存パッケージを更新（単発 → no-product-backlog）
-->

## 背景

<!-- この Issue が生まれた経緯や状況を記載してください -->



## 課題

<!-- 現状の問題点や達成したいことを具体的に記載してください -->



## 影響範囲

<!-- 変更によって影響を受けるコンポーネント・ファイル・機能を記載してください -->

-

## 内容

<!-- 対応内容・改善内容をフリーフォーマットで記載してください -->
<!-- 【必須】なぜその対応方針にしたのか、理由を必ず記載してください -->

### 対応方針

<!-- 採用する方針と、その方針を選んだ理由 -->



### 対応詳細

<!-- 具体的な作業内容 -->



## 結果

<!-- Issue クローズ後に記載 / 対応の結果・確認内容を記載してください -->
