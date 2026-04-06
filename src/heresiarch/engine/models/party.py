"""Party model: active roster, reserve, stash."""

from pydantic import BaseModel, Field

from .items import Item
from .jobs import CharacterInstance


class Party(BaseModel):
    """The player's party state."""

    active: list[str] = Field(default_factory=list)
    reserve: list[str] = Field(default_factory=list)
    characters: dict[str, CharacterInstance] = Field(default_factory=dict)
    stash: list[str] = Field(default_factory=list)
    items: dict[str, Item] = Field(default_factory=dict)
    money: int = 0
    cha: int = 0
