"""Shop screen — buy/sell with CHA-adjusted prices."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Label, OptionList, Static
from textual.widgets.option_list import Option

from heresiarch.engine.formulas import calculate_sell_price
from heresiarch.engine.shop import ShopInventory


class ShopScreen(Screen):
    """Buy and sell items with CHA-adjusted pricing."""

    CSS = """
    #shop-container {
        height: 100%;
        padding: 1 2;
    }
    #shop-tabs {
        height: auto;
        margin-bottom: 1;
    }
    #shop-items {
        height: auto;
        max-height: 16;
        margin-bottom: 1;
    }
    #item-detail {
        height: auto;
        min-height: 3;
        padding: 0 1;
        border: tall #333355;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("backspace", "go_back", "Back"),
        ("b", "switch_buy", "Buy"),
        ("s", "switch_sell", "Sell"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._tab: str = "buy"  # buy | sell
        self._shop: ShopInventory | None = None
        self._item_keys: list[tuple[str, int]] = []  # (item_id, price) for buy; (item_id, sell_price) for sell

    def compose(self) -> ComposeResult:
        with Vertical(id="shop-container"):
            yield Static("", id="shop-header")
            with Horizontal(id="shop-tabs"):
                yield Button("[b] Buy", id="btn-tab-buy", variant="primary")
                yield Button("[s] Sell", id="btn-tab-sell")
            yield OptionList(id="shop-items")
            yield Static("", id="item-detail")
            yield Label("", id="money-display")
            yield Button("[ESC] Leave Shop", id="btn-leave")
        yield Footer()

    def on_mount(self) -> None:
        self._init_shop()
        self._refresh()
        self.query_one("#shop-items", OptionList).focus()

    def _init_shop(self) -> None:
        run = self.app.run_state
        if run is None or run.current_zone_id is None:
            return

        zone = self.app.game_data.zones.get(run.current_zone_id)
        if zone is None:
            return

        self._shop = ShopInventory(
            available_items=list(zone.shop_item_pool),
            zone_level=zone.zone_level,
        )

    def _refresh(self) -> None:
        run = self.app.run_state
        if run is None:
            return

        # Header
        zone_name = ""
        if run.current_zone_id:
            zone = self.app.game_data.zones.get(run.current_zone_id)
            zone_name = zone.name if zone else run.current_zone_id
        self.query_one("#shop-header", Static).update(f"[bold]Shop[/bold] — {zone_name}")

        # Money
        self.query_one("#money-display", Label).update(
            f"Money: [bold #e6c566]{run.party.money}G[/bold #e6c566]"
        )

        # Tab highlighting
        buy_btn = self.query_one("#btn-tab-buy", Button)
        sell_btn = self.query_one("#btn-tab-sell", Button)
        buy_btn.variant = "primary" if self._tab == "buy" else "default"
        sell_btn.variant = "primary" if self._tab == "sell" else "default"

        # Populate item list
        item_list = self.query_one("#shop-items", OptionList)
        item_list.clear_options()
        self._item_keys = []

        if self._tab == "buy":
            self._populate_buy(item_list, run)
        else:
            self._populate_sell(item_list, run)

        # Clear detail when switching tabs
        self.query_one("#item-detail", Static).update("")
        item_list.focus()

    def _populate_buy(self, item_list: OptionList, run) -> None:
        if self._shop is None:
            return

        cha = run.party.cha
        buy_menu = self.app.game_loop.shop_engine.get_buy_menu(self._shop, cha)
        if not buy_menu:
            item_list.add_option(Option("[dim]Nothing for sale[/dim]"))
            self._item_keys.append(("", 0))
            return

        for item_id, price in buy_menu:
            item = self.app.game_data.items.get(item_id)
            name = item.name if item else item_id
            affordable = run.party.money >= price
            price_color = "#44aa44" if affordable else "#cc4444"
            label = f"{name} — [{price_color}]{price}G[/{price_color}]"
            if not affordable:
                label += " [dim](can't afford)[/dim]"
            item_list.add_option(Option(label))
            self._item_keys.append((item_id, price))

    def _populate_sell(self, item_list: OptionList, run) -> None:
        if not run.party.stash:
            item_list.add_option(Option("[dim]Stash is empty[/dim]"))
            self._item_keys.append(("", 0))
            return

        for item_id in run.party.stash:
            item = run.party.items.get(item_id) or self.app.game_data.items.get(item_id)
            if item is None:
                continue
            sell_price = calculate_sell_price(item.base_price)
            item_list.add_option(Option(f"{item.name} — [#e6c566]{sell_price}G[/#e6c566]"))
            self._item_keys.append((item_id, sell_price))

    def on_option_list_option_highlighted(self, event: OptionList.OptionHighlighted) -> None:
        """Show item detail on highlight."""
        if event.option_list.id != "shop-items":
            return
        idx = event.option_index
        if idx < 0 or idx >= len(self._item_keys):
            return

        item_id, price = self._item_keys[idx]
        if not item_id:
            self.query_one("#item-detail", Static).update("")
            return

        item = self.app.game_data.items.get(item_id)
        if item is None:
            return

        lines: list[str] = [f"[bold]{item.name}[/bold]"]
        if item.description:
            lines.append(f"  {item.description}")
        if item.scaling:
            lines.append(f"  Scaling: {item.scaling.scaling_type.value} ({item.scaling.stat.value})")
        if item.flat_stat_bonus:
            bonuses = ", ".join(f"{k}+{v}" for k, v in item.flat_stat_bonus.items() if v != 0)
            if bonuses:
                lines.append(f"  Bonuses: {bonuses}")
        if item.granted_ability_id:
            ability = self.app.game_data.abilities.get(item.granted_ability_id)
            aname = ability.name if ability else item.granted_ability_id
            lines.append(f"  Grants: {aname}")

        self.query_one("#item-detail", Static).update("\n".join(lines))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Buy or sell on Enter."""
        if event.option_list.id != "shop-items":
            return
        idx = event.option_index
        if idx < 0 or idx >= len(self._item_keys):
            return

        item_id, price = self._item_keys[idx]
        if not item_id:
            return

        if self._tab == "buy":
            self._buy_item(item_id, price)
        else:
            self._sell_item(item_id)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        match event.button.id:
            case "btn-leave":
                self.app.pop_screen()
            case "btn-tab-buy":
                self.action_switch_buy()
            case "btn-tab-sell":
                self.action_switch_sell()

    def _buy_item(self, item_id: str, price: int) -> None:
        run = self.app.run_state
        if run is None:
            return
        try:
            new_party = self.app.game_loop.shop_engine.buy_item(
                run.party, item_id, price
            )
            self.app.run_state = run.model_copy(update={"party": new_party})
        except ValueError:
            pass
        self._refresh()

    def _sell_item(self, item_id: str) -> None:
        run = self.app.run_state
        if run is None:
            return
        try:
            new_party = self.app.game_loop.shop_engine.sell_item(run.party, item_id)
            self.app.run_state = run.model_copy(update={"party": new_party})
        except ValueError:
            pass
        self._refresh()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    def action_switch_buy(self) -> None:
        self._tab = "buy"
        self._refresh()

    def action_switch_sell(self) -> None:
        self._tab = "sell"
        self._refresh()
