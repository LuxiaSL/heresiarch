"""MCP server: exposes Heresiarch as tool-use interface for AI agents.

Run with:
    python -m heresiarch.agent.server
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from heresiarch.agent.session import AgentError, GameSession

# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------

server = Server("heresiarch")

# Resolve data path relative to the heresiarch package, not CWD
_PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # src/heresiarch/agent -> heresiarch/
_DATA_PATH = _PACKAGE_ROOT / "data"
session = GameSession(data_path=_DATA_PATH)

# Auto-load autosave if it exists
try:
    _saves_dir = session._notes_path.parent / "agent_saves"
    if (_saves_dir / "autosave.json").exists():
        session.load_run("autosave")
except Exception:
    pass  # Start fresh if autoload fails


def _ok(text: str) -> list[TextContent]:
    return [TextContent(type="text", text=text)]


def _err(text: str) -> list[TextContent]:
    return [TextContent(type="text", text=f"ERROR: {text}")]


def _call(fn: Any, *args: Any, **kwargs: Any) -> list[TextContent]:
    """Call a session method, catching AgentError for clean error messages."""
    try:
        result = fn(*args, **kwargs)
        return _ok(result)
    except AgentError as e:
        return _err(str(e))


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

TOOLS: list[Tool] = [
    # Run management
    Tool(
        name="new_run",
        description="Start a new playthrough. Pick a name and starting job.",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Character name"},
                "job_id": {
                    "type": "string",
                    "description": "Starting job: einherjar, berserker, martyr, onmyoji",
                },
                "seed": {
                    "type": "integer",
                    "description": "RNG seed for deterministic runs. Random if omitted.",
                },
            },
            "required": ["name", "job_id"],
        },
    ),
    Tool(
        name="get_state",
        description="Get current state summary adapted to the current game phase.",
        inputSchema={"type": "object", "properties": {}},
    ),

    # Zone navigation
    Tool(
        name="list_zones",
        description="Show available zones with details.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="enter_zone",
        description="Enter a zone to begin fighting encounters. Full heals party first.",
        inputSchema={
            "type": "object",
            "properties": {
                "zone_id": {"type": "string", "description": "Zone to enter"},
            },
            "required": ["zone_id"],
        },
    ),
    Tool(
        name="leave_zone",
        description="Exit current zone. Progress is saved for re-entry.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="get_zone_status",
        description="Show current zone progress, encounter history, party HP.",
        inputSchema={"type": "object", "properties": {}},
    ),

    # Combat
    Tool(
        name="fight",
        description="Start the next encounter in the current zone.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="submit_decisions",
        description=(
            "Submit one round of combat decisions for all living player characters. "
            "Each character needs: mode (normal/cheat/survive), action (ability_id or 'use_item'), "
            "target (combatant_id). To use an item instead of attacking, set action to 'use_item' "
            "with item_id and target fields — this costs the character's action for the round."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "decisions": {
                    "type": "object",
                    "description": (
                        "Keyed by combatant_id. Each value: "
                        '{"mode": "normal"|"cheat"|"survive", '
                        '"action": "ability_id" or "use_item", "target": "combatant_id", '
                        '"item_id": "item_id" (only with use_item), '
                        '"ap_spend": int, '
                        '"cheat_extras": [{"ability": "id", "target": "id"}], '
                        '"partial_actions": [{"ability": "id", "target": "id"}]}'
                    ),
                    "additionalProperties": {"type": "object"},
                },
            },
            "required": ["decisions"],
        },
    ),
    Tool(
        name="get_combat_state",
        description="Re-fetch current combat state without advancing.",
        inputSchema={"type": "object", "properties": {}},
    ),

    # Post-combat
    Tool(
        name="pick_loot",
        description="Select which dropped items to keep. Pass [] to take nothing.",
        inputSchema={
            "type": "object",
            "properties": {
                "item_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Item IDs to keep from the loot drops.",
                },
            },
            "required": ["item_ids"],
        },
    ),

    # Recruitment
    Tool(
        name="inspect_candidate",
        description="Get detailed info about the recruitment candidate. Detail level depends on party CHA.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="recruit",
        description="Accept or decline the recruitment candidate.",
        inputSchema={
            "type": "object",
            "properties": {
                "accept": {"type": "boolean", "description": "true to recruit, false to decline"},
            },
            "required": ["accept"],
        },
    ),

    # Party management
    Tool(
        name="party_status",
        description="Full party detail view with stats, equipment, abilities, XP progress.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="equip",
        description="Equip an item from stash onto a character. Old item in slot returns to stash.",
        inputSchema={
            "type": "object",
            "properties": {
                "character_id": {"type": "string"},
                "item_id": {"type": "string", "description": "Item from stash"},
                "slot": {
                    "type": "string",
                    "description": "WEAPON, ARMOR, ACCESSORY_1, or ACCESSORY_2",
                },
            },
            "required": ["character_id", "item_id", "slot"],
        },
    ),
    Tool(
        name="unequip",
        description="Remove equipment from a slot back to stash.",
        inputSchema={
            "type": "object",
            "properties": {
                "character_id": {"type": "string"},
                "slot": {"type": "string"},
            },
            "required": ["character_id", "slot"],
        },
    ),
    Tool(
        name="swap_roster",
        description="Swap characters between active and reserve. Provide active_id, reserve_id, or both.",
        inputSchema={
            "type": "object",
            "properties": {
                "active_id": {"type": "string", "description": "Active member to bench"},
                "reserve_id": {"type": "string", "description": "Reserve member to promote"},
            },
        },
    ),
    Tool(
        name="use_scroll",
        description="Use a teach scroll to permanently teach an ability to a character.",
        inputSchema={
            "type": "object",
            "properties": {
                "item_id": {"type": "string"},
                "character_id": {"type": "string"},
            },
            "required": ["item_id", "character_id"],
        },
    ),
    Tool(
        name="use_consumable",
        description="Use a consumable item (potion, etc.) on a character.",
        inputSchema={
            "type": "object",
            "properties": {
                "item_id": {"type": "string"},
                "character_id": {"type": "string"},
            },
            "required": ["item_id", "character_id"],
        },
    ),
    Tool(
        name="mc_swap_job",
        description="Change the MC's job to mimic a recruited party member's job.",
        inputSchema={
            "type": "object",
            "properties": {
                "job_id": {"type": "string"},
            },
            "required": ["job_id"],
        },
    ),

    # Shopping
    Tool(
        name="shop_browse",
        description="View zone shop inventory with CHA-adjusted prices.",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="shop_buy",
        description="Purchase an item from the zone shop.",
        inputSchema={
            "type": "object",
            "properties": {
                "item_id": {"type": "string"},
            },
            "required": ["item_id"],
        },
    ),
    Tool(
        name="shop_sell",
        description="Sell an item from stash.",
        inputSchema={
            "type": "object",
            "properties": {
                "item_id": {"type": "string"},
            },
            "required": ["item_id"],
        },
    ),

    # Game knowledge
    Tool(
        name="lookup_job",
        description="Look up a job's growth, abilities, and role.",
        inputSchema={
            "type": "object",
            "properties": {"job_id": {"type": "string"}},
            "required": ["job_id"],
        },
    ),
    Tool(
        name="lookup_ability",
        description="Look up an ability's effects, damage, cooldown, targeting.",
        inputSchema={
            "type": "object",
            "properties": {"ability_id": {"type": "string"}},
            "required": ["ability_id"],
        },
    ),
    Tool(
        name="lookup_item",
        description="Look up an item's scaling, bonuses, and properties.",
        inputSchema={
            "type": "object",
            "properties": {"item_id": {"type": "string"}},
            "required": ["item_id"],
        },
    ),
    Tool(
        name="lookup_enemy",
        description="Look up an enemy's archetype, stats, action table, and drops.",
        inputSchema={
            "type": "object",
            "properties": {"enemy_id": {"type": "string"}},
            "required": ["enemy_id"],
        },
    ),
    Tool(
        name="lookup_zone",
        description="Look up a zone's encounters, shop, and unlock requirements.",
        inputSchema={
            "type": "object",
            "properties": {"zone_id": {"type": "string"}},
            "required": ["zone_id"],
        },
    ),
    Tool(
        name="lookup_formula",
        description=(
            "Look up a game formula. Topics: damage, res_gate, hp, xp, "
            "bonus_actions, shop_pricing, overstay, cheat_survive, scaling_types"
        ),
        inputSchema={
            "type": "object",
            "properties": {"topic": {"type": "string"}},
            "required": ["topic"],
        },
    ),

    # Analytics
    Tool(
        name="get_battle_record",
        description="Get run combat statistics (encounters, damage, ability usage).",
        inputSchema={"type": "object", "properties": {}},
    ),
    Tool(
        name="get_run_summary",
        description="Comprehensive end-of-run report with full analytics.",
        inputSchema={"type": "object", "properties": {}},
    ),

    # Notes
    Tool(
        name="save_note",
        description="Save a named note that persists across runs. Use to record strategies, enemy patterns, and lessons learned.",
        inputSchema={
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Note name (e.g. 'alpha_slime', 'zone_01_strategy')"},
                "content": {"type": "string", "description": "Note content"},
            },
            "required": ["key", "content"],
        },
    ),
    Tool(
        name="read_notes",
        description="Read all saved notes from previous runs.",
        inputSchema={"type": "object", "properties": {}},
    ),

    # Save/Load
    Tool(
        name="save_run",
        description="Save current run to disk. Survives server restarts.",
        inputSchema={
            "type": "object",
            "properties": {
                "slot": {"type": "string", "description": "Save slot name. Default: 'autosave'"},
            },
        },
    ),
    Tool(
        name="load_run",
        description="Load a saved run from disk.",
        inputSchema={
            "type": "object",
            "properties": {
                "slot": {"type": "string", "description": "Save slot name. Default: 'autosave'"},
            },
        },
    ),
    Tool(
        name="list_saves",
        description="List available save files.",
        inputSchema={"type": "object", "properties": {}},
    ),
]


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

@server.list_tools()
async def list_tools() -> list[Tool]:
    return TOOLS


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    match name:
        # Run management
        case "new_run":
            return _call(session.new_run, arguments["name"], arguments["job_id"], arguments.get("seed"))
        case "get_state":
            return _call(session.get_state)

        # Zone navigation
        case "list_zones":
            return _call(session.list_zones)
        case "enter_zone":
            return _call(session.enter_zone, arguments["zone_id"])
        case "leave_zone":
            return _call(session.leave_zone)
        case "get_zone_status":
            return _call(session.get_zone_status)

        # Combat
        case "fight":
            return _call(session.fight)
        case "submit_decisions":
            return _call(session.submit_decisions, arguments["decisions"])
        case "get_combat_state":
            return _call(session.get_combat_state)

        # Post-combat
        case "pick_loot":
            return _call(session.pick_loot, arguments["item_ids"])

        # Recruitment
        case "inspect_candidate":
            return _call(session.inspect_candidate)
        case "recruit":
            return _call(session.recruit, arguments["accept"])

        # Party management
        case "party_status":
            return _call(session.party_status)
        case "equip":
            return _call(session.equip, arguments["character_id"], arguments["item_id"], arguments["slot"])
        case "unequip":
            return _call(session.unequip, arguments["character_id"], arguments["slot"])
        case "swap_roster":
            return _call(session.swap_roster, arguments.get("active_id"), arguments.get("reserve_id"))
        case "use_scroll":
            return _call(session.use_scroll, arguments["item_id"], arguments["character_id"])
        case "use_consumable":
            return _call(session.use_consumable, arguments["item_id"], arguments["character_id"])
        case "mc_swap_job":
            return _call(session.mc_swap_job, arguments["job_id"])

        # Shopping
        case "shop_browse":
            return _call(session.shop_browse)
        case "shop_buy":
            return _call(session.shop_buy, arguments["item_id"])
        case "shop_sell":
            return _call(session.shop_sell, arguments["item_id"])

        # Game knowledge
        case "lookup_job":
            return _call(session.lookup_job, arguments["job_id"])
        case "lookup_ability":
            return _call(session.lookup_ability, arguments["ability_id"])
        case "lookup_item":
            return _call(session.lookup_item, arguments["item_id"])
        case "lookup_enemy":
            return _call(session.lookup_enemy, arguments["enemy_id"])
        case "lookup_zone":
            return _call(session.lookup_zone, arguments["zone_id"])
        case "lookup_formula":
            return _call(session.lookup_formula, arguments["topic"])

        # Analytics
        case "get_battle_record":
            return _call(session.get_battle_record)
        case "get_run_summary":
            return _call(session.get_run_summary)

        # Notes
        case "save_note":
            return _call(session.save_note, arguments["key"], arguments["content"])
        case "read_notes":
            return _call(session.read_notes)

        # Save/Load
        case "save_run":
            return _call(session.save_run, arguments.get("slot", "autosave"))
        case "load_run":
            return _call(session.load_run, arguments.get("slot", "autosave"))
        case "list_saves":
            return _call(session.list_saves)

        case _:
            return _err(f"Unknown tool: {name}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        init_options = server.create_initialization_options()
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
