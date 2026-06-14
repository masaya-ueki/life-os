"""travel のスモークテスト（スケルトン）。"""

from travel.index import wishlist
from travel.models import Destination


def test_wishlist_excludes_visited():
    destinations = [
        Destination(id="1", name="京都", visited=True),
        Destination(id="2", name="沖縄", visited=False),
    ]
    assert [d.name for d in wishlist(destinations)] == ["沖縄"]
