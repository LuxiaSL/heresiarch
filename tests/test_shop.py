"""Tests for shop system: pricing, buy/sell transactions."""

import pytest

from heresiarch.engine.formulas import calculate_buy_price, calculate_sell_price
from heresiarch.engine.models.items import EquipSlot, Item
from heresiarch.engine.models.party import Party
from heresiarch.engine.shop import STASH_LIMIT, ShopEngine, ShopInventory


def _test_item(item_id: str = "test_sword", base_price: int = 100) -> Item:
    return Item(
        id=item_id,
        name="Test Sword",
        slot=EquipSlot.WEAPON,
        base_price=base_price,
    )


def _test_registry() -> dict[str, Item]:
    return {
        "test_sword": _test_item("test_sword", 100),
        "test_armor": Item(
            id="test_armor",
            name="Test Armor",
            slot=EquipSlot.ARMOR,
            base_price=200,
        ),
        "free_item": Item(
            id="free_item",
            name="Free Item",
            slot=EquipSlot.ACCESSORY_1,
            base_price=0,
        ),
    }


class TestBuyPrice:
    def test_no_cha(self) -> None:
        assert calculate_buy_price(100, cha=0) == 100

    def test_cha_100(self) -> None:
        # 1.0 - 0.005 * 100 = 0.5 -> 100 * 0.5 = 50
        assert calculate_buy_price(100, cha=100) == 50

    def test_cha_clamped_high(self) -> None:
        # CHA=200 -> 1.0 - 1.0 = 0.0, but clamped to 0.5
        assert calculate_buy_price(100, cha=200) == 50

    def test_cha_negative_clamped(self) -> None:
        # Negative CHA would increase price, but clamped to 1.5
        # CHA=-200 -> 1.0 + 1.0 = 2.0, clamped to 1.5
        assert calculate_buy_price(100, cha=-200) == 150


class TestSellPrice:
    def test_sell_ratio(self) -> None:
        # 15% of 100 = 15
        assert calculate_sell_price(100) == 15

    def test_sell_minimum(self) -> None:
        # Very cheap item still sells for at least 1
        assert calculate_sell_price(1) >= 1


class TestBuyMenu:
    def test_menu_shows_adjusted_prices(self) -> None:
        registry = _test_registry()
        shop = ShopInventory(available_items=["test_sword", "test_armor"])
        engine = ShopEngine(registry)
        menu = engine.get_buy_menu(shop, party_cha=0)
        assert len(menu) == 2
        assert ("test_sword", 100) in menu
        assert ("test_armor", 200) in menu

    def test_menu_excludes_free_items(self) -> None:
        registry = _test_registry()
        shop = ShopInventory(available_items=["test_sword", "free_item"])
        engine = ShopEngine(registry)
        menu = engine.get_buy_menu(shop, party_cha=0)
        assert len(menu) == 1  # free_item excluded

    def test_menu_excludes_unknown_items(self) -> None:
        registry = _test_registry()
        shop = ShopInventory(available_items=["test_sword", "nonexistent"])
        engine = ShopEngine(registry)
        menu = engine.get_buy_menu(shop, party_cha=0)
        assert len(menu) == 1


class TestBuyTransaction:
    def test_buy_success(self) -> None:
        registry = _test_registry()
        engine = ShopEngine(registry)
        party = Party(money=1000)
        new_party = engine.buy_item(party, "test_sword", price=100)
        assert new_party.money == 900
        assert "test_sword" in new_party.stash
        assert "test_sword" in new_party.items

    def test_buy_insufficient_funds(self) -> None:
        registry = _test_registry()
        engine = ShopEngine(registry)
        party = Party(money=50)
        with pytest.raises(ValueError, match="Insufficient funds"):
            engine.buy_item(party, "test_sword", price=100)

    def test_buy_stash_full(self) -> None:
        registry = _test_registry()
        engine = ShopEngine(registry)
        party = Party(money=1000, stash=["x"] * STASH_LIMIT)
        with pytest.raises(ValueError, match="full"):
            engine.buy_item(party, "test_sword", price=100)

    def test_buy_unknown_item(self) -> None:
        registry = _test_registry()
        engine = ShopEngine(registry)
        party = Party(money=1000)
        with pytest.raises(ValueError, match="Unknown item"):
            engine.buy_item(party, "nonexistent", price=100)


class TestSellTransaction:
    def test_sell_success(self) -> None:
        registry = _test_registry()
        engine = ShopEngine(registry)
        party = Party(
            money=100,
            stash=["test_sword"],
            items={"test_sword": registry["test_sword"]},
        )
        new_party = engine.sell_item(party, "test_sword")
        assert new_party.money == 115  # 100 + 15% of 100
        assert "test_sword" not in new_party.stash

    def test_sell_not_in_stash(self) -> None:
        registry = _test_registry()
        engine = ShopEngine(registry)
        party = Party(money=100)
        with pytest.raises(ValueError, match="not in stash"):
            engine.sell_item(party, "test_sword")
