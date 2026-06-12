import pytest

from ottawa_meshbot import Command, MeshBot
from ottawa_meshbot.context import IncomingMessage


def dm(text: str) -> IncomingMessage:
    return IncomingMessage(text=text, sender_key="abcd1234", sender_name="alice")


def channel_msg(text: str, idx: int = 0) -> IncomingMessage:
    return IncomingMessage(text=text, sender_name="alice", channel_idx=idx)


class ReplyRecorder:
    def __init__(self):
        self.replies: list[str] = []

    async def __call__(self, text: str) -> None:
        self.replies.append(text)


@pytest.fixture
def bot():
    return MeshBot()


@pytest.fixture
def reply():
    return ReplyRecorder()


class TestParse:
    def test_command_with_args(self, bot):
        assert bot.parse("!echo hello world") == ("echo", "hello world")

    def test_command_without_args(self, bot):
        assert bot.parse("!ping") == ("ping", "")

    def test_surrounding_whitespace(self, bot):
        assert bot.parse("  !ping  ") == ("ping", "")

    def test_non_command_text(self, bot):
        assert bot.parse("hello there") is None

    def test_bare_prefix(self, bot):
        assert bot.parse("!") is None

    def test_custom_prefix(self):
        bot = MeshBot(prefix="/")
        assert bot.parse("/ping") == ("ping", "")
        assert bot.parse("!ping") is None


class TestRegistration:
    def test_decorator_registers_command(self, bot):
        @bot.command("ping", help="pong back")
        async def ping(ctx):
            return "pong"

        command = bot.registry.get("ping")
        assert command is not None
        assert command.help == "pong back"

    def test_aliases_resolve_to_same_command(self, bot):
        @bot.command("weather", aliases=("wx",))
        async def weather(ctx):
            return "sunny"

        assert bot.registry.get("wx") is bot.registry.get("weather")

    def test_lookup_is_case_insensitive(self, bot):
        @bot.command("ping")
        async def ping(ctx):
            return "pong"

        assert bot.registry.get("PING") is not None

    def test_duplicate_name_rejected(self, bot):
        @bot.command("ping")
        async def ping(ctx):
            return "pong"

        with pytest.raises(ValueError):

            @bot.command("ping")
            async def ping2(ctx):
                return "pong2"

    def test_alias_colliding_with_existing_name_rejected(self, bot):
        @bot.command("ping")
        async def ping(ctx):
            return "pong"

        with pytest.raises(ValueError):
            bot.add_command(Command(name="other", handler=ping, aliases=("ping",)))


class TestDispatch:
    async def test_returned_string_is_sent_as_reply(self, bot, reply):
        @bot.command("ping")
        async def ping(ctx):
            return "pong"

        handled = await bot.dispatch(dm("!ping"), reply)
        assert handled
        assert reply.replies == ["pong"]

    async def test_handler_can_reply_directly(self, bot, reply):
        @bot.command("multi")
        async def multi(ctx):
            await ctx.reply("one")
            await ctx.reply("two")

        await bot.dispatch(dm("!multi"), reply)
        assert reply.replies == ["one", "two"]

    async def test_args_are_passed_to_handler(self, bot, reply):
        @bot.command("echo")
        async def echo(ctx):
            return ctx.args

        await bot.dispatch(dm("!echo hello world"), reply)
        assert reply.replies == ["hello world"]

    async def test_non_command_text_is_ignored(self, bot, reply):
        handled = await bot.dispatch(dm("just chatting"), reply)
        assert not handled
        assert reply.replies == []

    async def test_unknown_command_is_ignored(self, bot, reply):
        handled = await bot.dispatch(dm("!nosuchthing"), reply)
        assert not handled
        assert reply.replies == []

    async def test_handler_returning_none_sends_nothing(self, bot, reply):
        @bot.command("quiet")
        async def quiet(ctx):
            return None

        handled = await bot.dispatch(dm("!quiet"), reply)
        assert handled
        assert reply.replies == []

    async def test_handler_exception_is_caught_and_reported(self, bot, reply):
        @bot.command("boom")
        async def boom(ctx):
            raise RuntimeError("kaboom")

        handled = await bot.dispatch(dm("!boom"), reply)
        assert handled
        assert reply.replies == ["Sorry, !boom hit an error."]

    async def test_channel_messages_handled_by_default(self, bot, reply):
        @bot.command("ping")
        async def ping(ctx):
            return "pong"

        handled = await bot.dispatch(channel_msg("!ping"), reply)
        assert handled
        assert reply.replies == ["pong"]

    async def test_channel_messages_ignored_when_disabled(self, reply):
        bot = MeshBot(respond_in_channels=False)

        @bot.command("ping")
        async def ping(ctx):
            return "pong"

        handled = await bot.dispatch(channel_msg("!ping"), reply)
        assert not handled
        assert reply.replies == []

    async def test_context_exposes_sender_and_dm_flag(self, bot, reply):
        seen = {}

        @bot.command("who")
        async def who(ctx):
            seen["sender"] = ctx.sender_name
            seen["is_dm"] = ctx.is_dm

        await bot.dispatch(dm("!who"), reply)
        assert seen == {"sender": "alice", "is_dm": True}


class TestHelp:
    async def test_help_lists_commands_with_descriptions(self, bot, reply):
        @bot.command("ping", help="Check liveness")
        async def ping(ctx):
            return "pong"

        await bot.dispatch(dm("!help"), reply)
        assert len(reply.replies) == 1
        text = reply.replies[0]
        assert "!help - List available commands" in text
        assert "!ping - Check liveness" in text
