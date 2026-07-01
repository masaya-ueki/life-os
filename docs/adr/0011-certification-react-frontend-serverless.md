# ADR-0011: certification 領域に React フロントとサーバレスを導入する

- **ステータス**: `承認済み`
- **決定日**: 2026-07-01
- **決定者**: masaya-ueki
- **関連タスク**: #82, #83

> 採番メモ: `0010` は既存の2ファイルで重複使用済みのため、本 ADR は `0011` を採番する
> （Issue #82/#83 の本文では便宜上「ADR-0010」と記載しているが、実体は本 ADR-0011）。

---

## コンテキスト

Issue #82 で個人用の資格取得学習サイトを新領域 `certification` として構築する。要件は
Web（PC・スマホ）からアクセスする SPA・Notion 風 UI・単一ユーザー認証・出題/採点/問題集で、
本リポジトリで**初のデプロイ可能なフルスタック Web アプリ**になる。

これまでの life-os は [ADR-0002](./0002-modular-monolith-bounded-context.md) で「実装は Python 中心で統一」
と定めており、フロントエンド（React/TS）・HTTP サーバ・クラウドデプロイの前例がない。
また要件当初は「DB は S3 + Iceberg、サーバは ECS（普段停止・ログイン時起動）」が挙がっていたが、
利用者は本人1名で、トランザクショナルな認証・学習履歴を扱う。ここで構造的な判断が必要になる。

## 決定事項

1. `certification` 領域のフロントを **React（Vite）** で実装し、`domains/certification/frontend/` に置く。
2. バックエンドは Python（アーキタイプA / DDD）とし、**FastAPI** を adapters 層の HTTP アダプタとして追加する（`certification` のオプション依存 `api`）。
3. デプロイは **サーバレス（API Gateway + AWS Lambda + DynamoDB）** を採用し、Terraform で管理する（`domains/certification/infra/`）。ECS + S3 Iceberg は採用しない。
4. MVP はローカル（docker compose）で完結させ、AWS への適用は後続フェーズ（#82 P5）とする。

## 検討した選択肢

### 選択肢A: React フロント + Python(FastAPI) + サーバレス（採用）

- **メリット**: 要件（SPA・レスポンシブ・Notion 風）に素直。バックエンドは既存の Python/uv workspace・DDD 慣習に載る。サーバレスは待機コストがほぼ $0 で、単一ユーザーの散発利用に最適。「普段停止・起動」の運用が不要になり、ECS の「ログイン前に起動できない」鶏卵問題が消える。DynamoDB は認証・学習履歴のキーバリュー参照に十分。
- **デメリット**: 本リポジトリ初の TS/Node ツールチェーンが入る（import-linter の対象外＝Python 境界とは別管理）。Lambda のコールドスタート。

### 選択肢B: ECS 常時停止 + S3 Iceberg（不採用）

- **メリット**: データ系資格（SnowPro 等）の学習と技術スタックが揃い、学習効果はある。
- **デメリット**: Iceberg はクエリエンジン（Athena/Spark 等）前提の分析用テーブル形式で、単一ユーザーの認証・出題履歴のような小さなトランザクショナル参照に不向き。ECS は「普段停止・ログイン時起動」に前段の常時起動コンポーネントが必要（鶏卵問題）。総じて MVP には過剰。
- **不採用理由**: 待機コスト・運用複雑性・データモデル不整合。要件「まずは簡易でOK」に反する。

### 選択肢C: フロントも Python（サーバサイドレンダリング）（不採用）

- **メリット**: 言語を Python に統一でき ADR-0002 と無矛盾。
- **デメリット**: 「React を使いたい」という明示要件に反する。Notion 風のインタラクティブ UI を SSR で作るのは非効率。
- **不採用理由**: 要件（React）と体験の両面で劣る。

## 結果・トレードオフ

- ADR-0002 の「Python 中心」を、**フロントは領域内の `frontend/` に限定**する形で部分的に緩和する。バックエンド・領域境界（`.importlinter`）は従来どおり Python で統一を維持する。
- import-linter は Python のみを対象とするため、フロントの依存管理は npm/Vite 側の責務として分離する。`frontend/` は workspace member（`domains/certification`）内のサブディレクトリで、`scripts/check_structure.py` の C-DOMAIN（domains/ 直下は member のみ）にも抵触しない。
- リポジトリ・secret への平文パスワードや AWS 認証情報の混入を禁止する。認証は環境変数＋ハッシュ（PBKDF2, stdlib）で扱う。
- 将来 Lambda のコールドスタートやコストが問題化した場合、コンテナ（App Runner 等）への移行を別 ADR で検討する。

## 関連ドキュメント・リンク

- [ADR-0002 Modular Monolith × Bounded Context](./0002-modular-monolith-bounded-context.md)
- [ADR-0009 領域を domains/ 配下に集約](./0009-group-domains-under-domains-dir.md)
- [domains/certification/README.md](../../domains/certification/README.md)
- Issue #82（ProductBacklog）, #83（本 ADR）
