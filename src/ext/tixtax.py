from typing import Generic, Protocol, TypeVar
import typing_extensions

import hikari
import lightbulb
import miru
from loguru import logger


class Emoji:
    SEPERATOR = ":white_small_square:"
    EDGE_PLAYER_ONE = ":small_blue_diamond:"
    EDGE_PLAYER_TWO = ":small_red_triangle:"
    EDGE_SELECTED = ":yellow_circle:"
    NO_PLAYER = ":black_large_square:"
    PLAYER_ONE = ":blue_square:"
    PLAYER_TWO = ":red_square:"


plugin = lightbulb.Plugin("TixTax")


class SupportsPlayer(Protocol):
    def player(self) -> int | None:
        ...


B = TypeVar("B", bound=SupportsPlayer)


class Board(Generic[B]):
    def __init__(self, grid: list[list[B]]) -> None:
        self.grid = grid

    def player(self) -> int | None:
        player_grid = [[v.player() for v in row] for row in self.grid]

        # check for wins

        # === ROWS
        for row in player_grid:
            if len(set(row)) == 1 and row[0] is not None:
                return row[0]

        # === COLLUMS
        for x in range(3):
            col = [row[x] for row in player_grid]
            if len(set(col)) == 1 and col[0] is not None:
                return col[0]

        # === DIAGONAL
        dig1 = [player_grid[0][0], player_grid[1][1], player_grid[2][2]]
        dig2 = [player_grid[0][2], player_grid[1][1], player_grid[2][0]]

        if len(set(dig1)) == 1 and dig1[0] is not None:
            return dig1[0]

        if len(set(dig2)) == 1 and dig2[0] is not None:
            return dig2[0]

    def full(self) -> bool:
        return all(cell.player() is not None for row in self.grid for cell in row)

    def __getitem__(self, position: tuple[int, int]) -> B:
        return self.grid[position[1]][position[0]]


class PlayerValue:
    def __init__(self):
        self.value: int | None = None  # random.choice([None, 1, 2])

    def player(self) -> int | None:
        return self.value

    def emote(self) -> str:
        if self.value is None:
            return Emoji.NO_PLAYER
        elif self.value == 1:
            return Emoji.PLAYER_ONE
        elif self.value == 2:
            return Emoji.PLAYER_TWO
        else:
            raise ValueError(f"unknown player value: {self.value}")


class Game:
    def __init__(self, player_one: int, player_two: int) -> None:
        self.player_one = player_one
        self.player_two = player_two
        self.current_turn = player_one
        self.selected_board: tuple[int, int] | None = None

        outer_board: list[list[Board[PlayerValue]]] = []
        for _ in range(3):
            outer_row: list[Board[PlayerValue]] = []
            for _ in range(3):
                inner_board: list[list[PlayerValue]] = []
                for _ in range(3):
                    inner_row: list[PlayerValue] = []
                    for _ in range(3):
                        inner_row.append(PlayerValue())
                    inner_board.append(inner_row)
                outer_row.append(Board(inner_board))
            outer_board.append(outer_row)
        self.board = Board(outer_board)

    def render_board(self) -> hikari.Embed:
        render_outer_grid: list[str] = []
        for outer_row in self.board.grid:
            edges: list[list[str]] = []
            for left, right in zip(outer_row, outer_row[1:]):
                edge: list[str] = []
                if self.selected_board is not None and left == self.board[self.selected_board]:
                    edge.append(Emoji.EDGE_SELECTED)
                elif left.player() == 1:
                    edge.append(Emoji.EDGE_PLAYER_ONE)
                elif left.player() == 2:
                    edge.append(Emoji.EDGE_PLAYER_TWO)

                if self.selected_board is not None and right == self.board[self.selected_board]:
                    edge.append(Emoji.EDGE_SELECTED)
                elif right.player() == 1:
                    edge.append(Emoji.EDGE_PLAYER_ONE)
                elif right.player() == 2:
                    edge.append(Emoji.EDGE_PLAYER_TWO)

                if len(edge) == 0:
                    edge = [Emoji.SEPERATOR, Emoji.SEPERATOR]
                elif len(edge) == 1:
                    edge *= 2

                edges.append(edge)
            # logger.debug(edges)

            render_outer_row: list[str] = []
            for inner_row in range(3):
                parts = ["".join(player.emote() for player in board.grid[inner_row]) for board in outer_row]
                render_outer_row.append(
                    parts[0] + edges[0][inner_row % 2] + parts[1] + edges[1][inner_row % 2] + parts[2]
                )
            render_outer_grid.append("\n".join(render_outer_row))

        seperators: list[str] = []
        for offset in range(2):
            parts: list[str] = []
            for col in range(3):
                top, bottom = self.board[col, offset], self.board[col, offset + 1]

                edge_vals: list[str] = []
                if self.selected_board is not None and top == self.board[self.selected_board]:
                    edge_vals.append(Emoji.EDGE_SELECTED)
                elif top.player() == 1:
                    edge_vals.append(Emoji.EDGE_PLAYER_ONE)
                elif top.player() == 2:
                    edge_vals.append(Emoji.EDGE_PLAYER_TWO)

                if self.selected_board is not None and bottom == self.board[self.selected_board]:
                    edge_vals.append(Emoji.EDGE_SELECTED)
                elif bottom.player() == 1:
                    edge_vals.append(Emoji.EDGE_PLAYER_ONE)
                elif bottom.player() == 2:
                    edge_vals.append(Emoji.EDGE_PLAYER_TWO)

                if len(edge_vals) == 0:
                    edge_vals = [Emoji.SEPERATOR, Emoji.SEPERATOR]
                elif len(edge_vals) == 1:
                    edge_vals *= 2

                parts.append(edge_vals[0] + edge_vals[1] + edge_vals[0])
            seperators.append(Emoji.SEPERATOR.join(parts))

        message = "\n".join(
            [
                render_outer_grid[0],
                seperators[0],
                render_outer_grid[1],
                seperators[1],
                render_outer_grid[2],
            ]
        )
        embed_color = "#0000ff" if self.current_turn == self.player_one else "#ff0000"
        title = f"<@{self.player_one}> ({Emoji.PLAYER_ONE}) vs <@{self.player_two}> ({Emoji.PLAYER_TWO})"
        return hikari.Embed(
            description=title + "\n" + message,
            color=hikari.Color.from_hex_code(embed_color),
        )

    def moves(self) -> list[list[tuple[bool, int | None]]]:
        if self.selected_board is not None:
            board = self.board[self.selected_board]
            return [[(p.player() is None, p.player()) for p in row] for row in board.grid]
        else:
            return [
                [(not (c.full() or c.player() is not None), c.player()) for c in row]
                for row in self.board.grid
            ]

    def button_clicked(self, pos: tuple[int, int]) -> None:
        if self.selected_board is not None:
            board = self.board[self.selected_board]
            player = 1 if self.current_turn == self.player_one else 2
            board[pos].value = player
            self.current_turn = self.player_two if self.current_turn == self.player_one else self.player_one

            if self.board[pos].player() is not None:
                self.selected_board = None
            else:
                self.selected_board = pos

        else:
            self.selected_board = pos


class SelectionButton(miru.Button["GameView"]):
    def __init__(self, player: int | None, active: bool, pos: tuple[int, int]) -> None:
        super().__init__(label="select", row=pos[1])
        self.pos = pos
        self.active = active
        self.player = player
        self.recalc_styles()

    @property
    def game(self) -> Game:
        return self.view.game

    def recalc_styles(self):
        if self.player is None:
            style = hikari.ButtonStyle.SECONDARY
        elif self.player == 1:
            style = hikari.ButtonStyle.PRIMARY
        elif self.player == 2:
            style = hikari.ButtonStyle.DANGER
        else:
            raise ValueError(f"Invalid player: {self.player}")

        self.style = style
        self.disabled = not self.active

    async def callback(self, context: miru.Context) -> None:
        logger.debug(f"YOU PRESSED BUTTON {self.pos}")
        self.game.button_clicked(self.pos)

        if self.game.board.player() is not None:
            # WE HAVE A WINNER
            winner = (
                self.game.player_one
                if self.game.current_turn == self.game.player_two
                else self.game.player_two
            )
            await context.edit_response(
                f"player <@{winner}> WON!",
                embed=self.game.render_board(),
                components=[],
            )
            self.view.stop()
            return

        self.view.recalc_buttons()
        await context.edit_response(embed=self.game.render_board(), components=self.view.build())


class GameView(miru.View):
    def __init__(self, game: Game) -> None:
        super().__init__(timeout=15 * 60)
        self.game = game
        self.add_buttons()

    async def on_timeout(self) -> None:
        if self.message is None:
            raise TypeError("Message is None")

        await self.message.edit(
            "Sorry, the game timed out.",
            components=[],
        )

    async def view_check(self, context: miru.Context) -> bool:
        if context.user.id != self.game.current_turn:
            await context.respond("hey wait for your turn", flags=hikari.MessageFlag.EPHEMERAL)
            return False
        return True

    def add_buttons(self) -> None:
        for y, row in enumerate(self.game.moves()):
            for x, (active, player) in enumerate(row):
                self.add_item(SelectionButton(player, active, (x, y)))

    def recalc_buttons(self) -> None:
        moves = self.game.moves()
        for button in self.children:
            if not isinstance(button, SelectionButton):
                raise TypeError(f"Expected SelectionButton, got {type(button)}")

            active, player = moves[button.pos[1]][button.pos[0]]
            button.player = player
            button.active = active
            button.recalc_styles()



class InviteView(miru.View):
    def __init__(self, player_one: int, target: int) -> None:
        super().__init__(timeout=5 * 60)
        self.player_one = player_one
        self.target = target
    
    async def on_timeout(self) -> None:
        if self.message is None:
            raise TypeError("Message is None")

        await self.message.edit(
            "Sorry, the invnite timed out.",
            components=[],
        )

    async def view_check(self, context: miru.Context) -> bool:
        if context.user.id != self.target:
            await context.respond("that button is not for you!", flags=hikari.MessageFlag.EPHEMERAL)
            return False
        return True

    @miru.button(label="Accept", style=hikari.ButtonStyle.SUCCESS)
    async def accept_button(self, button: miru.Button[typing_extensions.Self], ctx: miru.Context) -> None:
        if self.message is None:
            raise TypeError("Message is None")

        self.stop()
        
        game = Game(self.player_one, self.target)
        view = GameView(game)
        await ctx.edit_response("", embed=game.render_board(), components=view.build())
        view.start(self.message)

    @miru.button(label="Decline", style=hikari.ButtonStyle.DANGER)
    async def decline_button(self, button: miru.Button[typing_extensions.Self], ctx: miru.Context) -> None:
        self.stop()
        await ctx.edit_response("oh they declined :(", components=[])



class OpenInviteView(miru.View):
    def __init__(self, player_one: int) -> None:
        super().__init__(timeout=10 * 60)
        self.player_one = player_one
    
    async def on_timeout(self) -> None:
        if self.message is None:
            raise TypeError("Message is None")

        await self.message.edit(
            "Sorry, the invnite timed out.",
            components=[],
        )

    @miru.button(label="Play", style=hikari.ButtonStyle.SUCCESS)
    async def play_button(self, button: miru.Button[typing_extensions.Self], ctx: miru.Context) -> None:
        if self.message is None:
            raise TypeError("Message is None")

        self.stop()
        
        game = Game(self.player_one, ctx.user.id)
        view = GameView(game)
        await ctx.edit_response("", embed=game.render_board(), components=view.build())
        view.start(self.message)

@plugin.command
@lightbulb.option("target", "who do you want to play against?", type=hikari.User, required=False)
@lightbulb.command("tixtax", "play some tixtax!")
@lightbulb.implements(lightbulb.SlashCommand)
async def tixtax_command(ctx: lightbulb.Context) -> None:
    if ctx.options.target is None:
        view = OpenInviteView(ctx.user.id)
        response = await ctx.respond(
            f"{ctx.user.mention} wants to play tixtax with somebody!",
            components=view.build(),
        )
    else:
        view = InviteView(ctx.user.id, ctx.options.target.id)
        response = await ctx.respond(
            f"<@{ctx.options.target.id}>, {ctx.user.mention} wants to play tixtax with you!",
            components=view.build(),
            user_mentions=True
        )
    view.start(await response.message())
