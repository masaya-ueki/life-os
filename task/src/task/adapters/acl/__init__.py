"""task の Anti-Corruption Layer（腐敗防止層）。

他領域を参照する場合、相手の ``public`` だけをここで受け取り、
task のドメイン用語へ翻訳する。これにより他領域の都合が
task のモデルへ侵入するのを防ぐ（ADR-0002 / Context Map）。

現状、他領域への依存は無い（スケルトン）。
"""
