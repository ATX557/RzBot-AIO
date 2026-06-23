import discord
from discord.ext import commands
from discord import app_commands
from typing import List, Optional
from discord.utils import utcnow

class Connect4Button(discord.ui.Button):
    def __init__(self, column: int):
        super().__init__(style=discord.ButtonStyle.blurple, label=str(column + 1), row=0)
        self.column = column
    
    async def callback(self, interaction: discord.Interaction):
        view: Connect4View = self.view
        
        # Security Guardrail: Check if it's the player's turn
        if interaction.user != view.current_player:
            await interaction.response.send_message(
                f"❌ It's not your turn! Wait for {view.current_player.mention}",
                ephemeral=True
            )
            return
        
        # Try to place piece in column
        row = view.drop_piece(self.column)
        
        if row == -1:
            self.disabled = True  # Safeguard: Disable button immediately if full
            await interaction.response.edit_message(view=view)
            return
            
        # If the top row (0) of this column is now filled, disable this button
        if view.board[0][self.column] != 0:
            self.disabled = True
        
        # Check game status
        winner = view.check_winner(row, self.column)
        if winner:
            await view.end_game(interaction, winner)
        elif view.is_board_full():
            await view.end_game(interaction, 0)  # Draw
        else:
            # Switch turn safely
            view.current_player = view.player2 if view.current_player == view.player1 else view.player1
            embed = view.create_game_embed()
            await interaction.response.edit_message(embed=embed, view=view)


class Connect4View(discord.ui.View):
    def __init__(self, player1: discord.Member, player2: discord.Member):
        super().__init__(timeout=120.0) # 2 minutes per action
        self.player1 = player1
        self.player2 = player2
        self.current_player = player1
        self.message: Optional[discord.Message] = None
        
        # Board setup: 6 rows x 7 columns (0=empty, 1=player1, 2=player2)
        self.board = [[0 for _ in range(7)] for _ in range(6)]
        
        # Core Matrix buttons
        for col in range(7):
            self.add_item(Connect4Button(col))
        
        # Forfeit technical node
        forfeit_button = discord.ui.Button(
            label="Forfeit",
            style=discord.ButtonStyle.red,
            emoji="🏳️",
            row=1
        )
        forfeit_button.callback = self.forfeit_callback
        self.add_item(forfeit_button)
        
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Prevent spectating users from interacting with components
        if interaction.user not in [self.player1, self.player2]:
            await interaction.response.send_message("❌ You are not a participant in this game session.", ephemeral=True)
            return False
        return True
    
    async def forfeit_callback(self, interaction: discord.Interaction):
        winner = self.player2 if interaction.user == self.player1 else self.player1
        
        embed = discord.Embed(
            title=f"🏳️ {interaction.user.name} Forfeited!",
            description=f"{winner.mention} wins the match by forfeit!",
            color=0xE74C3C,
            timestamp=utcnow()
        )
        
        for item in self.children:
            item.disabled = True
            
        embed.add_field(name="Final Board Layout", value=self.get_board_visual(), inline=False)
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()
    
    def drop_piece(self, column: int) -> int:
        for row in range(5, -1, -1):
            if self.board[row][column] == 0:
                self.board[row][column] = 1 if self.current_player == self.player1 else 2
                return row
        return -1
    
    def get_board_visual(self) -> str:
        emojis = {0: "⚫", 1: "🔴", 2: "🟡"}
        visual = "".join("".join(emojis[cell] for cell in row) + "\n" for row in self.board)
        return visual + "1️⃣2️⃣3️⃣4️⃣5️⃣6️⃣7️⃣"
    
    def create_game_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title="🎮 Connect 4 Session",
            description=f"🔵 **Active Turn:** {self.current_player.mention}",
            color=0x5865F2,
            timestamp=utcnow()
        )
        embed.add_field(name="Game Board", value=self.get_board_visual(), inline=False)
        embed.add_field(name="🔴 Player 1", value=self.player1.mention, inline=True)
        embed.add_field(name="🟡 Player 2", value=self.player2.mention, inline=True)
        embed.set_footer(text="Select a column node to drop your piece.")
        return embed
    
    def check_winner(self, row: int, col: int) -> Optional[int]:
        player = self.board[row][col]
        directions = [(0, 1), (1, 0), (1, 1), (1, -1)] # Horizontal, Vertical, Diagonals
        
        for dr, dc in directions:
            count = 1
            # Positive direction
            r, c = row + dr, col + dc
            while 0 <= r < 6 and 0 <= c < 7 and self.board[r][c] == player:
                count += 1
                r += dr
                c += dc
            # Negative direction
            r, c = row - dr, col - dc
            while 0 <= r < 6 and 0 <= c < 7 and self.board[r][c] == player:
                count += 1
                r -= dr
                c -= dc
                
            if count >= 4:
                return player
        return None
    
    def is_board_full(self) -> bool:
        return all(self.board[0][col] != 0 for col in range(7))
    
    async def end_game(self, interaction: discord.Interaction, winner: int):
        for item in self.children:
            item.disabled = True
            
        if winner == 0:
            embed = discord.Embed(
                title="🤝 Match Settled: Draw!",
                description="The game grid is completely filled. Stalemate reached.",
                color=0x95A5A6,
                timestamp=utcnow()
            )
        else:
            winner_member = self.player1 if winner == 1 else self.player2
            token = "🔴" if winner == 1 else "🟡"
            embed = discord.Embed(
                title=f"🎉 Victory: {winner_member.name}!",
                description=f"{winner_member.mention} {token} successfully aligned 4 tokens!",
                color=0x57F287,
                timestamp=utcnow()
            )
            
        embed.add_field(name="Final Board Layout", value=self.get_board_visual(), inline=False)
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()
        
    async def on_timeout(self):
        """Handle inactive game sessions cleanly."""
        for item in self.children:
            item.disabled = True
        
        if self.message:
            embed = discord.Embed(
                title="⏱️ Game Terminated: Timeout",
                description="The session expired due to player inactivity.",
                color=0x2F3136,
                timestamp=utcnow()
            )
            embed.add_field(name="Last Known Board", value=self.get_board_visual(), inline=False)
            try:
                await self.message.edit(embed=embed, view=self)
            except discord.HTTPException:
                pass
        self.stop()


class Connect4(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name="connect4", aliases=["c4"])
    @app_commands.describe(opponent="The user context node you want to challenge")
    @commands.guild_only()
    async def connect4(self, ctx: commands.Context, opponent: discord.Member):
        """🎮 Challenge another user to a standard match of Connect 4."""
        if opponent.bot:
            return await ctx.send("❌ Operation denied: AI bots cannot participate in matrix games.")
        
        if opponent == ctx.author:
            return await ctx.send("❌ Operation denied: Self-play sessions are invalid.")
        
        view = Connect4View(ctx.author, opponent)
        embed = view.create_game_embed()
        
        # Save message reference for the timeout cleanup
        view.message = await ctx.send(
            content=f"⚔️ **Match Initiated:** {ctx.author.mention} 🔴 vs 🟡 {opponent.mention}",
            embed=embed,
            view=view
        )

async def setup(bot):
    await bot.add_cog(Connect4(bot))
