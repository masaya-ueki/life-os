"""content_sales アプリケーション層 — ユースケース（スケルトン）。"""

from __future__ import annotations

from content_sales.domain import Product


def register_product(name: str) -> Product:
    return Product.create(name)
