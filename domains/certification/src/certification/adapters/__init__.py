"""certification アダプタ層 — 外部世界との境界（リポジトリ・認証・HTTP）。

- ``repository`` … JSON ファイル + インメモリのリポジトリ実装（ポートを満たす）
- ``security``   … パスワードハッシュ（stdlib のみ）
- ``api``        … FastAPI HTTP アダプタ（オプション依存 `api` が必要）
"""
