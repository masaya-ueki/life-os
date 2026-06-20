"""content_sales のスモークテスト（スケルトン）。"""

from content_sales.application import register_product


def test_register_product():
    product = register_product("My CLI Tool")
    assert product.name == "My CLI Tool"
    assert product.id
