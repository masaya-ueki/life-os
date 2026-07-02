# ジャンル×トピック → 公式ドキュメント被覆表（カバレッジ仕様）

SnowPro Core **COF-C03** の5ジャンルについて、出題すべき主要トピックと、その `source_url`（公式ドキュメント）を対応づけた**網羅性の基準**。#98 のループはこの表の各トピックを最低1問ずつ被覆する。全 URL は HTTP 200 を確認済み（2026-07 時点）。

## docs.snowflake.com トップレベルツリー

| セクション | 概要 | 代表URL |
|---|---|---|
| User Guides（Guides） | 操作・概念を網羅する手順ガイド群（実質的な一次情報源） | https://docs.snowflake.com/en/guides-overview |
| SQL Reference | SQL コマンド／関数／データ型／構文のリファレンス | https://docs.snowflake.com/en/sql-reference-commands |
| Developer | アプリ開発（Snowpark / Native Apps / Streamlit / ドライバ / CLI） | https://docs.snowflake.com/en/developer |
| Reference | データ型・関数・API・ACCOUNT_USAGE 等の参照索引 | https://docs.snowflake.com/en/reference |
| Release Notes | サーバ／クライアント／動作変更（BCR）のリリースノート | https://docs.snowflake.com/en/release-notes/overview |

## 出典選定ルール

概念・機能の**理解**を問う問題は User Guide の overview / intro ページ（`docs.snowflake.com/en/user-guide/...`）を第一候補にする（安定した canonical URL で改廃が少なく、機能全体像を1ページで説明しているため）。特定コマンドの構文・オプション・デフォルト値・必要権限を直接問う場合に限り、SQL Reference（`/sql-reference/sql/<command>`）や ACCOUNT_USAGE の個別ビュー（`/sql-reference/account-usage/<view>`）を出典に使う。**1問=1URL** を原則とし、リダイレクトや 404 になる slug は採用しない。

---

## architecture（AIデータクラウドの機能とアーキテクチャ・31%）

| トピック | source_url |
|---|---|
| 3層アーキテクチャ / キー概念 | https://docs.snowflake.com/en/user-guide/intro-key-concepts |
| Snowflake エディション | https://docs.snowflake.com/en/user-guide/intro-editions |
| Snowsight（Web UI） | https://docs.snowflake.com/en/user-guide/ui-snowsight |
| Snowflake CLI | https://docs.snowflake.com/en/developer-guide/snowflake-cli/index |
| オブジェクト階層（DB→スキーマ→テーブル/ビュー） | https://docs.snowflake.com/en/user-guide/databases |
| 仮想ウェアハウス（概要） | https://docs.snowflake.com/en/user-guide/warehouses-overview |
| 仮想ウェアハウス（概念/種別） | https://docs.snowflake.com/en/user-guide/warehouses |
| マルチクラスタ / スケーリングポリシー | https://docs.snowflake.com/en/user-guide/warehouses-multicluster |
| マイクロパーティション & データクラスタリング | https://docs.snowflake.com/en/user-guide/tables-micro-partitions |
| 永続クエリ結果キャッシュ | https://docs.snowflake.com/en/user-guide/querying-persisted-results |
| コンピュートコスト / クレジット | https://docs.snowflake.com/en/user-guide/credits |
| AI/ML：Snowflake Notebooks | https://docs.snowflake.com/en/user-guide/ui-snowsight/notebooks |
| AI/ML：Streamlit in Snowflake | https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit |
| AI/ML：Snowpark | https://docs.snowflake.com/en/developer-guide/snowpark/index |
| AI/ML：Snowflake Cortex | https://docs.snowflake.com/en/user-guide/snowflake-cortex/overview |

## security（アカウント管理とデータガバナンス・20%）

| トピック | source_url |
|---|---|
| アクセス制御概要（RBAC/DAC・securable object 階層） | https://docs.snowflake.com/en/user-guide/security-access-control-overview |
| アクセス制御権限（privileges） | https://docs.snowflake.com/en/user-guide/security-access-control-privileges |
| システムロール / ベストプラクティス | https://docs.snowflake.com/en/user-guide/security-access-control-considerations |
| 認証：MFA | https://docs.snowflake.com/en/user-guide/security-mfa |
| 認証：SSO / SAML（フェデレーション） | https://docs.snowflake.com/en/user-guide/admin-security-fed-auth-overview |
| 認証：OAuth | https://docs.snowflake.com/en/user-guide/oauth-intro |
| 認証：キーペア認証 | https://docs.snowflake.com/en/user-guide/key-pair-auth |
| ネットワークポリシー | https://docs.snowflake.com/en/user-guide/network-policies |
| 動的データマスキング | https://docs.snowflake.com/en/user-guide/security-column-ddm-intro |
| 列レベルセキュリティ | https://docs.snowflake.com/en/user-guide/security-column-intro |
| 行アクセスポリシー | https://docs.snowflake.com/en/user-guide/security-row-intro |
| オブジェクトタグ付け | https://docs.snowflake.com/en/user-guide/object-tagging |
| タグベースマスキング | https://docs.snowflake.com/en/user-guide/tag-based-masking-policies |
| 暗号化 / キー管理 | https://docs.snowflake.com/en/user-guide/security-encryption-manage |
| Tri-Secret Secure | https://docs.snowflake.com/en/user-guide/security-encryption-tss |
| データリネージ | https://docs.snowflake.com/en/user-guide/ui-snowsight-lineage |
| リソースモニター | https://docs.snowflake.com/en/user-guide/resource-monitors |
| ACCOUNT_USAGE スキーマ | https://docs.snowflake.com/en/sql-reference/account-usage |
| Information Schema | https://docs.snowflake.com/en/sql-reference/info-schema |

## performance（パフォーマンス最適化・クエリ・変換・21%）

| トピック | source_url |
|---|---|
| パフォーマンス最適化（概要） | https://docs.snowflake.com/en/guides-overview-performance |
| Query Profile（実行計画 / spilled bytes） | https://docs.snowflake.com/en/user-guide/ui-query-profile |
| 実行時間の分析 / クエリインサイト | https://docs.snowflake.com/en/user-guide/performance-query-exploring |
| パーティションプルーニング | https://docs.snowflake.com/en/user-guide/tables-clustering-micropartitions |
| ACCOUNT_USAGE：QUERY_HISTORY | https://docs.snowflake.com/en/sql-reference/account-usage/query_history |
| Query Acceleration Service | https://docs.snowflake.com/en/user-guide/query-acceleration-service |
| Search Optimization Service | https://docs.snowflake.com/en/user-guide/search-optimization-service |
| クラスタリングキー | https://docs.snowflake.com/en/user-guide/tables-clustering-keys |
| 自動クラスタリング | https://docs.snowflake.com/en/user-guide/tables-auto-reclustering |
| マテリアライズドビュー | https://docs.snowflake.com/en/user-guide/views-materialized |
| 結果キャッシュ | https://docs.snowflake.com/en/user-guide/querying-persisted-results |
| ウェアハウスのサイジング考慮 | https://docs.snowflake.com/en/user-guide/warehouses-considerations |
| 半構造化データ（VARIANT） | https://docs.snowflake.com/en/user-guide/semistructured-concepts |
| FLATTEN | https://docs.snowflake.com/en/sql-reference/functions/flatten |
| LATERAL | https://docs.snowflake.com/en/sql-reference/constructs/join-lateral |
| 非構造化データ | https://docs.snowflake.com/en/user-guide/unstructured-intro |

## data-loading（データのロード/アンロードと連携・18%）

| トピック | source_url |
|---|---|
| データロード概要 | https://docs.snowflake.com/en/user-guide/data-load-overview |
| ファイル形式（CREATE FILE FORMAT） | https://docs.snowflake.com/en/sql-reference/sql/create-file-format |
| 内部ステージ | https://docs.snowflake.com/en/user-guide/data-load-local-file-system-create-stage |
| 外部ステージ / ストレージ統合（S3） | https://docs.snowflake.com/en/user-guide/data-load-s3-config-storage-integration |
| COPY INTO テーブル（ロード） | https://docs.snowflake.com/en/sql-reference/sql/copy-into-table |
| COPY INTO ロケーション（アンロード） | https://docs.snowflake.com/en/sql-reference/sql/copy-into-location |
| ロード時の考慮 / 検証 / エラー処理 | https://docs.snowflake.com/en/user-guide/data-load-considerations-load |
| Snowpipe | https://docs.snowflake.com/en/user-guide/data-load-snowpipe-intro |
| Snowpipe Streaming | https://docs.snowflake.com/en/user-guide/data-load-snowpipe-streaming-overview |
| Streams（CDC） | https://docs.snowflake.com/en/user-guide/streams-intro |
| Tasks | https://docs.snowflake.com/en/user-guide/tasks-intro |
| Dynamic Tables | https://docs.snowflake.com/en/user-guide/dynamic-tables-about |
| ドライバ & コネクタ | https://docs.snowflake.com/en/developer-guide/drivers |
| API 統合（CREATE API INTEGRATION） | https://docs.snowflake.com/en/sql-reference/sql/create-api-integration |
| Git 統合 | https://docs.snowflake.com/en/developer-guide/git/git-overview |

## data-collaboration（データコラボレーション・10%）

| トピック | source_url |
|---|---|
| データ共有・コラボレーション（概要） | https://docs.snowflake.com/en/guides-overview-sharing |
| Secure Data Sharing（概要） | https://docs.snowflake.com/en/user-guide/data-sharing-intro |
| 共有の作成（プロバイダ / direct share） | https://docs.snowflake.com/en/user-guide/data-sharing-provider |
| 共有データの利用（コンシューマ） | https://docs.snowflake.com/en/user-guide/data-share-consumers |
| リーダーアカウント | https://docs.snowflake.com/en/user-guide/data-sharing-reader-create |
| リスティング（Listings：private/public） | https://docs.snowflake.com/en/collaboration/collaboration-listings-about |
| Snowflake Marketplace | https://docs.snowflake.com/en/user-guide/data-marketplace-intro |
| レプリケーション & フェイルオーバー | https://docs.snowflake.com/en/user-guide/account-replication-intro |
| ゼロコピークローン | https://docs.snowflake.com/en/user-guide/object-clone |
| Time Travel | https://docs.snowflake.com/en/user-guide/data-time-travel |
| Fail-safe | https://docs.snowflake.com/en/user-guide/data-failsafe |
| データクリーンルーム | https://docs.snowflake.com/en/user-guide/cleanrooms/introduction |
| Native Apps Framework | https://docs.snowflake.com/en/developer-guide/native-apps/native-apps-about |
