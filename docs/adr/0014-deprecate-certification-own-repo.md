# ADR-0014: certification 領域を廃止し独立リポジトリへ移管する

- **ステータス**: `承認済み`
- **決定日**: 2026-08-01
- **決定者**: masaya_ueki
- **関連タスク**: -
- **置き換え**: [ADR-0011](./0011-certification-react-frontend-serverless.md)・[ADR-0012](./0012-certification-question-authoring-system.md)

---

## コンテキスト

[ADR-0011](./0011-certification-react-frontend-serverless.md) で `domains/certification` を React フロント + Python(FastAPI) + サーバレスのフルスタック領域として導入し、[ADR-0012](./0012-certification-question-authoring-system.md) で問題作成をスキル＋登録サブエージェント＋整合性テストゲートの仕組みに整備した。

certification は life-os 内で唯一 TS/Node ツールチェーン・独自デプロイ（Terraform/Lambda）・専用 CI ジョブを持つ領域で、他領域（Python 中心の Modular Monolith）とは運用形態が異なっていた。この領域が独立リポジトリへ昇格したことで、life-os 側にその実体を残す理由がなくなった。

## 決定事項

**`domains/certification` 領域、および関連する `docker/Dockerfile.certification`（`compose.yaml` の `cert-backend`/`cert-frontend` サービス含む）、`.claude/skills/cert-question-authoring/`、`.claude/agents/snowpro-question-author.md`、CI の certification 専用ジョブ（frontend ビルド確認・Terraform 構文検証）を life-os から削除する。** 今後の certification の開発は独立リポジトリ側で行う。

## 検討した選択肢

### 選択肢A: 領域を全削除する（採用）

- **メリット**: 実体が別リポジトリに移った以上、life-os 側の重複コード・専用 CI・専用 Docker イメージの保守コストがゼロになる。uv workspace member 数が減り `.importlinter` のコントラクト数も減るため、境界検査がシンプルになる。
- **デメリット**: life-os のコミット履歴からしか過去の実装を追えなくなる（履歴自体は残るため復元は可能）。

### 選択肢B: 参照用に残しつつ CI から除外する（不採用）

- **メリット**: コードが手元に残るので参照しやすい。
- **デメリット**: 実体が別リポジトリにある以上、life-os 側のコピーは更新されず即座に陳腐化する。「どちらが正か」の二重管理になり、[rule/directory-structure.md](../../rule/directory-structure.md) の R-STRUCT-7（不要物はアーカイブまたは削除）にも反する。
- **不採用理由**: 陳腐化したコードを置き続ける理由がない。

## 結果・トレードオフ

- **削除対象**: `domains/certification/`（`frontend/`・`infra/`・`data/` の生成物・成果物含む）、`docker/Dockerfile.certification`、`.claude/skills/cert-question-authoring/`、`.claude/agents/snowpro-question-author.md`。
- **設定からの除去**: `pyproject.toml`（uv workspace member・dependencies・sources）・`uv.lock`（`uv lock` で再生成）・`.importlinter`（`certification` root package と関連コントラクト）・`compose.yaml`（`cert-backend`/`cert-frontend` サービス）・`.github/workflows/ci.yml`（`frontend`/`terraform` ジョブ）から certification 関連の記述を除去した。
- **ラベルの扱い**: `system: certification` ラベルは [Issue 運用ルール](../../guides/development-policy/issue-operation-rules.md) の一覧から除去し、`scripts/setup-github-labels.sh` の廃止済みラベル（`--cleanup` 対象）に移した。
- **ADR の扱い**: [ADR-0011](./0011-certification-react-frontend-serverless.md)・[ADR-0012](./0012-certification-question-authoring-system.md) は削除せず `置き換え済み` として履歴に残す（[docs/adr/README.md の運用ルール](./README.md#adr-のステータス管理)）。
- **今後**: certification の開発・運用は独立リポジトリ側の責務とし、本 ADR の範囲外とする。

## 関連ドキュメント・リンク

- [ADR-0011](./0011-certification-react-frontend-serverless.md) — certification に React フロントとサーバレスを導入（本 ADR により置き換え）
- [ADR-0012](./0012-certification-question-authoring-system.md) — 問題作成のスキル＋サブエージェント体制（本 ADR により置き換え）
- [ADR-0009](./0009-group-domains-under-domains-dir.md) — 領域を `domains/` 配下にまとめる方針（certification もこの対象だった）
- [ADR-0013](./0013-deprecate-presentation-adopt-claude-design.md) — 同種の領域廃止判断の先例（presentation 領域の廃止）
