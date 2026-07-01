"""certification — 資格取得学習サイト Bounded Context（アーキタイプA）。

他領域からは ``certification.public`` のみを参照する（ADR-0002）。
内部は軽量ヘキサゴナル構成:
- ``domain``      … エンティティ・値オブジェクト・ドメインサービス（純粋ロジック）
- ``application`` … ユースケース（認証・出題・採点・問題集）
- ``adapters``    … リポジトリ・セキュリティ・FastAPI HTTP アダプタ

設計判断（React フロント + サーバレス）は docs/adr/0011 を参照。
"""
