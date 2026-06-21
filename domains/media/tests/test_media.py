"""media のスモークテスト（スケルトン）。"""

from media.index import find_by_tag
from media.models import Asset


def test_find_by_tag():
    assets = [
        Asset(id="1", path="a.jpg", tags=["旅行"]),
        Asset(id="2", path="b.jpg", tags=["家族"]),
    ]
    assert [a.id for a in find_by_tag(assets, "旅行")] == ["1"]
