import asyncio
import io
import time
from typing import Any

import aiohttp
import hikari
import lightbulb
import miru
import typing_extensions
from lightbulb.ext import tasks
from loguru import logger
from PIL import Image, ImageDraw

from src import constants

CHECK_URL = "https://arcade-placement-tool.herokuapp.com/get/starsToCheck"
REJECT_URL = "https://arcade-placement-tool.herokuapp.com/reject/starsChecked"
ACCEPT_URL = "https://arcade-placement-tool.herokuapp.com/verified/toStarField"
COLORS = [
    "#f73693",
    "#4392a0",
    "#1172b2",
    "#edd45a",
    "#b403a8",
    "#7e15af",
    "#ba2362",
    "#06aa19",
    "#aaf96d",
    "#2a8791",
    "#5ad117",
    "#bf8209",
    "#099b88",
    "#ac1804",
    "#52ce61",
    "#4dcc68",
    "#9a43a5",
    "#1250b5",
    "#a0b709",
    "#d0ed12",
    "#8e1531",
    "#2daeb5",
    "#24ad38",
    "#df33b0",
    "#fce54e",
]


plugin = lightbulb.Plugin("StarVerification", include_datastore=True)


class VerificationView(miru.View):
    def __init__(self, data: dict[str, object], embed: hikari.Embed) -> None:
        super().__init__(timeout=None)
        self.data = data
        self.embed = embed

    def set_embed_fields(self, ctx: miru.Context) -> None:
        self.embed.set_author(name=ctx.user.username, icon=ctx.user.avatar_url)
        timestamp = int(time.time())
        self.embed.description = f"last interacted with: <t:{timestamp}:t> (<t:{timestamp}:R>)"

    async def send_star_data(self, url: str, ctx: miru.Context) -> None:
        async with plugin.d.session.post(url, json=self.data) as resp:
            logger.debug(await resp.text())


class AcceptDenyView(VerificationView):
    @miru.button(label="accept", style=hikari.ButtonStyle.SUCCESS)
    async def accept_button(self, button: miru.Button[typing_extensions.Self], ctx: miru.Context) -> None:
        assert self.message is not None

        self.set_embed_fields(ctx)
        self.embed.color = hikari.Color.from_hex_code("#ffff00")
        await ctx.edit_response(embeds=[self.embed], components=[])

        await self.send_star_data(ACCEPT_URL, ctx)

        self.embed.color = hikari.Color.from_hex_code("#00ff00")
        self.clear_items()
        self.stop()

        new_view = ResendView(self.data, self.embed)
        await ctx.edit_response(embeds=[self.embed], components=new_view.build())
        new_view.start(self.message)

    @miru.button(label="reject", style=hikari.ButtonStyle.DANGER)
    async def reject_button(self, button: miru.Button[typing_extensions.Self], ctx: miru.Context) -> None:
        self.set_embed_fields(ctx)
        await self.send_star_data(REJECT_URL, ctx)

        self.embed.color = hikari.Color.from_hex_code("#ff0000")
        self.clear_items()
        self.stop()

        await ctx.edit_response(embeds=[self.embed], components=[3])


class ResendView(VerificationView):
    @miru.button(label="resend", style=hikari.ButtonStyle.PRIMARY)
    async def accept_button(self, button: miru.Button[typing_extensions.Self], ctx: miru.Context) -> None:
        self.set_embed_fields(ctx)
        self.embed.color = hikari.Color.from_hex_code("#ffff00")
        await ctx.edit_response(embeds=[self.embed], components=[])

        await self.send_star_data(ACCEPT_URL, ctx)

        self.embed.color = hikari.Color.from_hex_code("#00ff00")
        await ctx.edit_response(embeds=[self.embed], components=self.build())


@tasks.task(s=5)
async def check_for_newstars() -> None:
    logger.debug("checking for new stars to verify.")
    async with plugin.d.session.post(CHECK_URL) as resp:
        data = await resp.json()

    if len(data["stars"]) != 0:
        logger.warning("NEW STARS!")
        await asyncio.gather(post_new_stars(data), check_for_newstars())


async def post_new_stars(data: dict[str, Any]) -> None:
    user = data["senderTuid"]

    embed = hikari.Embed(title=f"NEW STARS: {user}", color=hikari.Color.from_hex_code("#ffff00"))
    embed.add_field("star count", str(len(data["stars"])))
    message = await plugin.bot.rest.create_message(
        constants.Channels.STARS,
        embed=embed,
    )

    embed.set_image(render_stars(data["stars"]))
    embed.color = hikari.Color.from_hex_code("#aaaaaa")

    data = {"jwt": constants.Secrets.JWT, "stars": data["stars"], "twitchId": user}
    view = AcceptDenyView(data, embed)
    await message.edit(
        embed=embed,
        components=view.build(),
    )
    view.start(message)


def render_stars(stars: list[dict[str, float]]) -> io.BytesIO:
    img = Image.new("RGB", (1000, 510))
    draw = ImageDraw.Draw(img)

    for star in stars:
        x, y, type_ = star["x"], star["y"], int(star["currentStar"])
        x = int(x * 1000)
        y = int(y * 510)
        color = COLORS[type_]
        logger.debug(f"drawing ({x}, {y}) with color {color}")
        draw.rectangle(((x, y), (x + 5, y + 5)), fill=color)

    output = io.BytesIO()
    img.save(output, "PNG")
    output.seek(0)
    return output


@plugin.listener(hikari.ShardReadyEvent)
async def event_ready(event: hikari.ShardReadyEvent) -> None:
    logger.debug("READY")
    plugin.d.session = aiohttp.ClientSession()
    logger.debug("starting task")
    check_for_newstars.start()
