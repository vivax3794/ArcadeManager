import hikari
import lightbulb
import miru
from lightbulb.ext import tasks

from src import constants, plugins

intents = hikari.Intents.GUILD_MESSAGES
bot = lightbulb.BotApp(token=constants.Secrets.DISCORD, intents=intents)
tasks.load(bot)
miru.load(bot)
plugins.load_plugins(bot)