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
    """

    text: str
    sender_key: str | None = None
    sender_name: str | None = None
    channel_idx: int | None = None

    @property
    def is_dm(self) -> bool:
        return self.channel_idx is None


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

    async def reply(self, text: str) -> None:
        """Send text back where the message came from (DM or channel)."""
        await self._reply(text)
