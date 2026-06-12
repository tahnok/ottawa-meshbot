"""Incoming message model and the context passed to command handlers."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class IncomingMessage:
    """A message received from the mesh, normalized away from transport details.

    channel_idx is None for direct messages and the channel number for
    channel/group messages. sender_key is the sender's public key prefix
    (hex) for direct messages; channel messages may not carry one.

    path_len is the raw value reported by the device: 255 means the message
    arrived directly (zero hops), otherwise it is the number of repeater
    hops. path, when known, is a hex string of repeater node hashes
    (two hex chars per hop, outermost repeater first).
    """

    text: str
    sender_key: str | None = None
    sender_name: str | None = None
    channel_idx: int | None = None
    path_len: int | None = None
    path: str | None = None

    @property
    def is_dm(self) -> bool:
        return self.channel_idx is None

    @property
    def hop_count(self) -> int | None:
        """Number of repeater hops, 0 if received directly, None if unknown."""
        if self.path_len is None:
            return None
        return 0 if self.path_len == 255 else self.path_len

    @property
    def path_description(self) -> str:
        """Human-readable route the message took, e.g. "direct" or "2 hops via a1,b2"."""
        hops = self.hop_count
        if hops is None:
            return "unknown path"
        if hops == 0:
            return "direct"
        label = "hop" if hops == 1 else "hops"
        if self.path:
            route = ",".join(self.path[i : i + 2] for i in range(0, len(self.path), 2))
            return f"{hops} {label} via {route}"
        return f"{hops} {label}"


ReplyFunc = Callable[[str], Awaitable[None]]


@dataclass(frozen=True)
class Context:
    """What a command handler gets to work with."""

    message: IncomingMessage
    command_name: str
    args: str
    _reply: ReplyFunc

    @property
    def is_dm(self) -> bool:
        return self.message.is_dm

    @property
    def sender_name(self) -> str | None:
        return self.message.sender_name

    @property
    def path_description(self) -> str:
        return self.message.path_description

    async def reply(self, text: str) -> None:
        """Send text back where the message came from (DM or channel)."""
        await self._reply(text)
