"""content_sales ドメイン層（スケルトン）。"""

from __future__ import annotations

from dataclasses import dataclass

from shared.ids import new_id


@dataclass
class Product:
    """販売物（スケルトン）。"""

    id: str
    name: str

    @classmethod
    def create(cls, name: str) -> "Product":
        return cls(id=new_id(), name=name)
