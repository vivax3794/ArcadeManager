import hikari
import lightbulb
from loguru import logger

from src import constants

plugin = lightbulb.Plugin("Suggestions", include_datastore=False)


@plugin.listener(hikari.MessageCreateEvent)
async def event_message(event: hikari.MessageCreateEvent) -> None:
    if event.message.channel_id == constants.Channels.SUGGESTIONS:
        logger.debug("adding reactions")
        await event.message.add_reaction("👍")
        await event.message.add_reaction("👎")


@plugin.command
@lightbulb.command("test", "just a quick test")
@lightbulb.implements(lightbulb.SlashCommand)
async def tixtax_command(ctx: lightbulb.Context) -> None:
    await ctx.respond("I pushed this code to github, but I never manually restarted the bot!")
