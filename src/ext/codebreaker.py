from __future__ import annotations

import random
import typing_extensions

import hikari
import lightbulb
import miru
from loguru import logger

LORE_TEXT = """
Oh no! vivax was doing his usual poking around at random stuff, this time our loved hero was messing with a electronic lock.
Good news (maybe not for who lives here) vivax managed exploit the lock and break in!
Now vivax discoverd that the door cant be opened from the inside at night, so now they are stuck!

That is where you come in, you arrive at the scene and discover mess of wires connected to a lock.
Besides the lock you see two displays, apperantly with a bit of hacking vivax managed to extract hints about the actual code whenever they enter a wrong one!

Can you help our local hacker get free and avoid prison?
"""
INSTRUCTIONS = """

:white_check_mark: Means the amount of numbers in the correct spot
:left_right_arrow: Means amount of correct numbers in the wrong spots

**remmember:** A pin code can have duplicate digits!
"""


class NumberButton(miru.Button["Codebreaker"]):
    def __init__(self, row: int, number: int) -> None:
        super().__init__(style=hikari.ButtonStyle.PRIMARY, label=str(number), row=row)
        self.number = str(number)

    async def callback(self, context: miru.Context) -> None:
        await self.view.button_clicked(context, self.number)

class Codebreaker(miru.View):
    def __init__(self, code: str, user_id: int) -> None:
        super().__init__(timeout=None)
        logger.debug(f"CODE IS {code}")
        self.code = code
        self.user_id = user_id
        self.current_output = INSTRUCTIONS
        self.current_input = ""
        self.moves = 0

    async def view_check(self, context: miru.Context) -> bool:
        result = context.user.id == self.user_id
        if result is False:
            await context.respond("hey dont do that", flags=hikari.MessageFlag.EPHEMERAL)
        return result

    def disable(self):
        for child in self.children:
            child.disabled = True

    async def button_clicked(self, ctx: miru.Context, number: str) -> None:
        self.current_input += number

        if self.current_input == self.code:
            self.moves += 1
            self.current_output += (
                f"\n`{self.current_input}` - **CORRECT**\n\nyou solved it in **{self.moves}** moves!"
            )
            self.disable()
            await ctx.edit_response(self.current_output, components=[])
            self.stop()
            return

        elif len(self.current_input) == len(self.code):
            self.moves += 1
            correct_spots = sum(a == b for a, b in zip(self.current_input, self.code))
            correct_numbers = (
                sum(min(self.current_input.count(a), self.code.count(a)) for a in set(self.current_input))
                - correct_spots
            )

            self.current_output += f"\n`{self.current_input}` - `{correct_spots}`:white_check_mark:  `{correct_numbers}`:left_right_arrow:"
            self.current_input = ""

        await ctx.edit_response(self.current_output + "\n**INPUT:**`" + self.current_input + "`")

    button_1 = NumberButton(0, 1)
    button_2 = NumberButton(0, 2)
    button_3 = NumberButton(0, 3)
    button_4 = NumberButton(1, 4)
    button_5 = NumberButton(1, 5)
    button_6 = NumberButton(1, 6)
    button_7 = NumberButton(2, 7)
    button_8 = NumberButton(2, 8)
    button_9 = NumberButton(2, 9)

    @miru.button(label="QUIT", style=hikari.ButtonStyle.DANGER, row=3)
    async def quit_button(self, button: miru.Button[typing_extensions.Self], ctx: miru.Context) -> None:
        self.current_output += f"\n\ncode was `{self.code}`"
        self.disable()
        await ctx.edit_response(self.current_output, components=[])
        self.stop()


plugin = lightbulb.Plugin("Codebreaker", include_datastore=False)


@plugin.command
@lightbulb.option("length", "length of code", type=int, min_value=1)
@lightbulb.command("codebreaker", "play some code breaker!")
@lightbulb.implements(lightbulb.SlashCommand)
async def codebreaker_command(ctx: lightbulb.Context) -> None:
    view = Codebreaker("".join(random.choices("123456789", k=ctx.options.length)), ctx.user.id)
    reponse = await ctx.respond(
        hikari.ResponseType.MESSAGE_CREATE,
        LORE_TEXT + INSTRUCTIONS,
        components=view.build(),
    )
    view.start(await reponse.message())
