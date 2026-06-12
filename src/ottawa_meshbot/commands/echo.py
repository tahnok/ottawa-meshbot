"""!echo — repeat back whatever you send."""

from ottawa_meshbot import Context, MeshBot


def register(bot: MeshBot) -> None:
    @bot.command("echo", help="Repeat back whatever you send")
    async def echo(ctx: Context) -> str:
        return ctx.args or "(nothing to echo)"
