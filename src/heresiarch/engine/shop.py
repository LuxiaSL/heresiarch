"""Shop system: buy/sell items with CHA-modulated pricing."""

from __future__ import annotations

from pydantic import BaseModel, Field

from heresiarch.engine.formulas import calculate_buy_price, calculate_sell_price
from heresiarch.engine.models.items import Item
from heresiarch.engine.models.party import STASH_LIMIT, Party


class ShopInventory(BaseModel):
    """A zone's shop state."""

    available_items: list[str] = Field(default_factory=list)
    zone_level: int = 1


class ShopEngine:
    """Resolves buy/sell transactions."""

    def __init__(self, item_registry: dict[str, Item]):
        self.item_registry = item_registry

    def get_buy_menu(
        self,
        shop: ShopInventory,
        party_cha: int,
    ) -> list[tuple[str, int]]:
        """Returns list of (item_id, adjusted_price) for items in shop."""
        menu: list[tuple[str, int]] = []
        for item_id in shop.available_items:
            item = self.item_registry.get(item_id)
            if item and item.base_price > 0:
                price = calculate_buy_price(item.base_price, party_cha)
                menu.append((item_id, price))
        return menu

    def buy_item(
        self,
        party: Party,
        item_id: str,
        price: int,
    ) -> Party:
        """Execute purchase. Returns updated Party copy."""
        if party.money < price:
            raise ValueError(
                f"Insufficient funds: have {party.money}, need {price}"
            )
        if len(party.stash) >= STASH_LIMIT:
            raise ValueError(
                f"Stash is full ({len(party.stash)}/{STASH_LIMIT})"
            )

        item = self.item_registry.get(item_id)
        if item is None:
            raise ValueError(f"Unknown item: {item_id}")

        new_stash = list(party.stash) + [item_id]
        new_items = dict(party.items)
        new_items[item_id] = item

        return party.model_copy(
            update={
                "money": party.money - price,
                "stash": new_stash,
                "items": new_items,
            }
        )

    def sell_item(
        self,
        party: Party,
        item_id: str,
    ) -> Party:
        """Sell item from stash. Returns updated Party copy."""
        if item_id not in party.stash:
            raise ValueError(f"Item '{item_id}' not in stash")

        item = self.item_registry.get(item_id) or party.items.get(item_id)
        if item is None:
            raise ValueError(f"Unknown item: {item_id}")

        sell_price = calculate_sell_price(item.base_price)
        new_stash = list(party.stash)
        new_stash.remove(item_id)

        return party.model_copy(
            update={
                "money": party.money + sell_price,
                "stash": new_stash,
            }
        )
