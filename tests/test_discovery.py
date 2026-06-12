"""Tests for auto-discovery of command modules."""

import importlib
import types

import pytest

from ottawa_meshbot import MeshBot
from ottawa_meshbot.cli import build_bot
from ottawa_meshbot.commands import iter_command_module_names, load_commands


def test_every_command_module_defines_register() -> None:
    for name in iter_command_module_names():
        module = importlib.import_module(f"ottawa_meshbot.commands.{name}")
        assert callable(getattr(module, "register", None)), (
            f"{module.__name__} must define register(bot)"
        )


def test_load_commands_loads_all_modules() -> None:
    loaded = load_commands(MeshBot())
    assert loaded == iter_command_module_names()
    assert {"ping", "echo", "roll"} <= set(loaded)


def test_no_name_collisions_across_command_files() -> None:
    # CommandRegistry raises ValueError on duplicates; a clean load proves
    # no two files claim the same command name or alias.
    load_commands(MeshBot())


def test_build_bot_exposes_all_commands() -> None:
    bot = build_bot()
    for name in ("help", "ping", "echo", "roll", "dice"):
        assert bot.registry.get(name) is not None


def test_module_without_register_hook_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import ottawa_meshbot.commands as commands_pkg

    monkeypatch.setattr(commands_pkg, "iter_command_module_names", lambda: ["broken"])
    monkeypatch.setattr(
        commands_pkg.importlib, "import_module", lambda name: types.ModuleType(name)
    )
    with pytest.raises(TypeError, match="must define register"):
        load_commands(MeshBot())
