"""Shop screen — buy/sell with CHA-adjusted prices."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, Static

from heresiarch.engine.formulas import calculate_buy_price, calculate_sell_price
from heresiarch.engine.shop import ShopInventory


class ShopScreen(Screen):
    """Buy and sell items with CHA-adjusted pricing."""

    BINDINGS = [
        ("escape", "go_back", "Back"),
        ("b", "switch_buy", "Buy"),
        ("s", "switch_sell", "Sell"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._tab: str = "buy"  # buy | sell
        self._shop: ShopInventory | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="shop-container"):
            yield Static("", id="shop-header")
            yield Label("")

            with Horizontal(id="shop-tabs"):
                yield Button("[b] Buy", id="btn-tab-buy", variant="primary")
                yield Button("[s] Sell", id="btn-tab-sell")

            yield Label("")
            yield Static("", id="shop-items")
            yield Label("")
            yield Label("", id="money-display")
            yield Label("")
            yield Button("Leave Shop", id="btn-leave")

    def on_mount(self) -> None:
        self._init_shop()
        self._refresh()

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

        # Items
        items_display = self.query_one("#shop-items", Static)
        # Clear old action buttons by removing them from parent
        for btn in self.query(".shop-action-btn"):
            btn.remove()

        if self._tab == "buy":
            self._render_buy(items_display)
        else:
            self._render_sell(items_display)

    def _render_buy(self, display: Static) -> None:
        run = self.app.run_state
        if run is None or self._shop is None:
            display.update("[dim]No items available[/dim]")
            return

        cha = run.party.cha
        lines: list[str] = ["[bold]Available Items[/bold]", ""]

        buy_menu = self.app.game_loop.shop_engine.get_buy_menu(self._shop, cha)
        if not buy_menu:
            lines.append("[dim]Nothing for sale[/dim]")
        else:
            parent = display.parent
            for item_id, price in buy_menu:
                item = self.app.game_data.items.get(item_id)
                name = item.name if item else item_id
                desc = item.description if item else ""
                affordable = run.party.money >= price
                price_color = "#44aa44" if affordable else "#cc4444"
                lines.append(f"  {name} — [{price_color}]{price}G[/{price_color}]")
                if desc:
                    lines.append(f"    [dim]{desc}[/dim]")

                if parent and affordable:
                    btn = Button(
                        f"Buy {name} ({price}G)",
                        id=f"buy-{item_id}-{price}",
                        classes="shop-action-btn",
                    )
                    parent.mount(btn, before=self.query_one("#money-display"))

        display.update("\n".join(lines))

    def _render_sell(self, display: Static) -> None:
        run = self.app.run_state
        if run is None:
            display.update("[dim]Nothing to sell[/dim]")
            return

        lines: list[str] = ["[bold]Stash Items[/bold]", ""]

        if not run.party.stash:
            lines.append("[dim]Stash is empty[/dim]")
        else:
            parent = display.parent
            for item_id in run.party.stash:
                item = run.party.items.get(item_id) or self.app.game_data.items.get(item_id)
                if item is None:
                    continue
                sell_price = calculate_sell_price(item.base_price)
                lines.append(f"  {item.name} — [#e6c566]{sell_price}G[/#e6c566]")

                if parent:
                    btn = Button(
                        f"Sell {item.name} ({sell_price}G)",
                        id=f"sell-{item_id}",
                        classes="shop-action-btn",
                    )
                    parent.mount(btn, before=self.query_one("#money-display"))

        display.update("\n".join(lines))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id or ""

        if btn_id == "btn-leave":
            self.app.pop_screen()
            return

        if btn_id == "btn-tab-buy":
            self._tab = "buy"
            self._refresh()
            return

        if btn_id == "btn-tab-sell":
            self._tab = "sell"
            self._refresh()
            return

        if btn_id.startswith("buy-"):
            parts = btn_id.removeprefix("buy-").rsplit("-", 1)
            if len(parts) == 2:
                item_id, price_str = parts
                self._buy_item(item_id, int(price_str))
            return

        if btn_id.startswith("sell-"):
            item_id = btn_id.removeprefix("sell-")
            self._sell_item(item_id)
            return

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
