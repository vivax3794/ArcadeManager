import lightbulb
from loguru import logger

from src import constants
from src.ext import codebreaker, stars, suggestions, tixtax

PLUGINS: dict[lightbulb.Plugin, list[tuple[bool, str]]] = {
    suggestions.plugin: [(constants.Channels.SUGGESTIONS != 0, "suggestions channel not defined.")],
    stars.plugin: [
        (constants.Secrets.JWT is not None, "JWT not defined."),
        (constants.Channels.STARS != 0, "Stars verification channel not defined."),
    ],
    codebreaker.plugin: [],
    tixtax.plugin: [],
}


def load_plugins(bot: lightbulb.BotApp) -> None:
    for plugin, checks in PLUGINS.items():
        errors: list[str] = []

        for check, error in checks:
            if not check:
                errors.append(error)

        if errors:
            logger.error(f"[plugin] cant load: {plugin.name}")
            for error in errors:
                logger.error(f"\t{error}")
        else:
            bot.add_plugin(plugin)
            logger.info(f"[plugin] loaded: {plugin.name}")
