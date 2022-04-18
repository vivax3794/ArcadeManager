import sys
from typing import TYPE_CHECKING, TypeVar, overload

import decouple

if TYPE_CHECKING:
    T = TypeVar("T")

    @overload
    def config(name: str) -> str:
        ...

    @overload
    def config(name: str, default: T) -> str | T:
        ...

    @overload
    def config(name: str, cast: type[T]) -> T | None:
        ...

    @overload
    def config(name: str, cast: type[T], default: T) -> T:
        ...

    def config():  # type: ignore
        ...

else:
    DOTENV_PATH = sys.argv[1] if len(sys.argv) >= 2 else ".env"
    config = decouple.Config(decouple.RepositoryEnv(DOTENV_PATH))


GUILD_ID = config("GUILD_ID", cast=int)


class Secrets:
    DISCORD = config("DISCORD_TOKEN")
    JWT = config("ARCADE_JWT", default=None)


class Channels:
    SUGGESTIONS = config("SUGGESTIONS_CHANNEL", cast=int, default=0)
    STARS = config("STARS_CHANNEL", cast=int, default=0)
