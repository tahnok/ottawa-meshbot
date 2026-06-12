"""The bot's commands — one module per command.

Each module in this package must define::

    def register(bot: MeshBot) -> None: ...

and is discovered and loaded automatically by load_commands(). To add a
command, drop a new file in this directory; there is no central list to
edit. Modules whose names start with an underscore are skipped, so shared
helpers can live in e.g. _util.py.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil

from ..bot import MeshBot

logger = logging.getLogger(__name__)


def iter_command_module_names() -> list[str]:
    """Names of all command modules in this package, sorted."""
    return sorted(
        info.name
        for info in pkgutil.iter_modules(__path__)
        if not info.name.startswith("_")
    )


def load_commands(bot: MeshBot) -> list[str]:
    """Import every command module and call its register(bot).

    Returns the module names that were loaded. Fails fast: a module that
    does not define a callable ``register`` raises TypeError, import errors
    propagate, and duplicate command names raise ValueError (from
    CommandRegistry). A broken command file should stop the bot from
    starting, not be skipped silently.
    """
    loaded: list[str] = []
    for name in iter_command_module_names():
        module = importlib.import_module(f"{__name__}.{name}")
        register = getattr(module, "register", None)
        if not callable(register):
            raise TypeError(
                f"command module {module.__name__!r} must define register(bot)"
            )
        register(bot)
        loaded.append(name)
        logger.debug("loaded command module %s", name)
    return loaded
