import discord
from discord.ext import commands
from discord import app_commands
from typing import List, Optional
from discord.utils import utcnow

class TicTacToeButton(discord.ui.Button):
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.gray, label="\u200b", row=y)
        self.x = x
        self.y = y
    
    async def callback(self, interaction: discord.Interaction):
        view: TicTacToeView = self.view
        
        # Check if it's the player's turn
        if interaction.user != view.current_player:
            await interaction.response.send_message(
                f"❌ It's not your turn! Wait for {view.current_player.mention}",
                ephemeral=True
            )
            return
        
        # Make the move
        if view.board[self.y][self.x] == 0:
            view.board[self.y][self.x] = view.current_mark
            
            # Update button
            self.label = view.get_symbol(view.current_mark)
            self.style = discord.ButtonStyle.blurple if view.current_mark == 1 else discord.ButtonStyle.green
            self.disabled = True
            
            # Check for winner
            winner = view.check_winner()
            if winner:
                await view.end_game(interaction, winner)
            elif view.is_board_full():
                await view.end_game(interaction, 0)  # Draw
            else:
                # Switch player
                view.current_mark = 2 if view.current_mark == 1 else 1
                view.current_player = view.player2 if view.current_mark == 2 else view.player1
                
                embed = view.create_game_embed()
                await interaction.response.edit_message(embed=embed, view=view)
        else:
            await interaction.response.send_message("❌ That spot is already taken!", ephemeral=True)


class TicTacToeView(discord.ui.View):
    def __init__(self, player1: discord.Member, player2: discord.Member):
        super().__init__(timeout=120.0)
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.current_mark = 1  # 1 for X, 2 for O
        self.board = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        
        # Create 3x3 grid of buttons
        for y in range(3):
            for x in range(3):
                self.add_item(TicTacToeButton(x, y))
    
    def get_symbol(self, mark: int) -> str:
        if mark == 1:
            return "❌"
        elif mark == 2:
            return "⭕"
        return "\u200b"
    
    def create_game_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🎮 Tic-Tac-Toe",
            description=f"**Current Turn:** {self.current_player.mention} ({self.get_symbol(self.current_mark)})",
            color=0x5865F2,
            timestamp=utcnow()
        )
        
        # Create visual board
        board_visual = ""
        for row in self.board:
            row_str = " │ ".join(self.get_symbol(cell) if cell != 0 else "⬜" for cell in row)
            board_visual += row_str + "\n"
            board_visual += "━━━━━━━━━━━\n" if row != self.board[-1] else ""
        
        embed.add_field(
            name="Game Board",
            value=board_visual,
            inline=False
        )
        
        embed.add_field(name=f"{self.get_symbol(1)} Player 1", value=self.player1.mention, inline=True)
        embed.add_field(name=f"{self.get_symbol(2)} Player 2", value=self.player2.mention, inline=True)
        
        return embed
    
    def check_winner(self) -> Optional[int]:
        # Check rows
        for row in self.board:
            if row[0] == row[1] == row[2] != 0:
                return row[0]
        
        # Check columns
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] != 0:
                return self.board[0][col]
        
        # Check diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != 0:
            return self.board[0][0]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != 0:
            return self.board[0][2]
        
        return None
    
    def is_board_full(self) -> bool:
        for row in self.board:
            if 0 in row:
                return False
        return True
    
    async def end_game(self, interaction: discord.Interaction, winner: int):
        for item in self.children:
            item.disabled = True
        
        if winner == 0:  # Draw
            embed = discord.Embed(
                title="🤝 It's a Draw!",
                description="The board is full! No one wins this time.",
                color=0x95A5A6,
                timestamp=utcnow()
            )
        else:
            winner_player = self.player1 if winner == 1 else self.player2
            embed = discord.Embed(
                title=f"🎉 {winner_player.name} Wins!",
                description=f"{winner_player.mention} ({self.get_symbol(winner)}) is the champion!",
                color=0x57F287,
                timestamp=utcnow()
            )
        
        # Show final board
        board_visual = ""
        for row in self.board:
            row_str = " │ ".join(self.get_symbol(cell) if cell != 0 else "⬜" for cell in row)
            board_visual += row_str + "\n"
        
        embed.add_field(name="Final Board", value=board_visual, inline=False)
        
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        self.stop()


class TicTacToe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name="tictactoe", aliases=["ttt"])
    @commands.guild_only()
    async def tictactoe(self, ctx: commands.Context, opponent: discord.Member):
        """🎮 Play Tic-Tac-Toe with another player!
        
        Parameters:
        - opponent: The player you want to challenge
        """
        if opponent.bot:
            return await ctx.send("❌ You can't play against bots!")
        
        if opponent == ctx.author:
            return await ctx.send("❌ You can't play against yourself!")
        
        view = TicTacToeView(ctx.author, opponent)
        embed = view.create_game_embed()
        
        await ctx.send(
            content=f"{ctx.author.mention} vs {opponent.mention}",
            embed=embed,
            view=view
        )


async def setup(bot):
    await bot.add_cog(TicTacToe(bot))
