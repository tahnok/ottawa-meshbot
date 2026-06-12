"""Command registration and lookup."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .context import Context

CommandHandler = Callable[["Context"], Awaitable[str | None]]


@dataclass
class Command:
    """A named command and the coroutine that handles it."""

    name: str
    handler: CommandHandler
    help: str = ""
    aliases: tuple[str, ...] = ()


@dataclass
class CommandRegistry:
    """Holds commands and resolves names (including aliases) to them."""

    _commands: dict[str, Command] = field(default_factory=dict)
    _lookup: dict[str, Command] = field(default_factory=dict)

    def register(self, command: Command) -> None:
        for name in (command.name, *command.aliases):
            key = name.lower()
            if key in self._lookup:
                raise ValueError(f"command name {name!r} is already registered")
        self._commands[command.name.lower()] = command
        for name in (command.name, *command.aliases):
            self._lookup[name.lower()] = command

    def get(self, name: str) -> Command | None:
        return self._lookup.get(name.lower())

    def all(self) -> list[Command]:
        """All registered commands, sorted by name (aliases excluded)."""
        return sorted(self._commands.values(), key=lambda c: c.name)
