import discord
from discord.ext import commands
from discord import app_commands
import random
from discord.utils import utcnow

class RPSButton(discord.ui.Button):
    def __init__(self, choice: str, emoji: str):
        super().__init__(style=discord.ButtonStyle.blurple, label=choice, emoji=emoji)
        self.choice = choice
    
    async def callback(self, interaction: discord.Interaction):
        view: RPSView = self.view
        
        if interaction.user != view.ctx.author:
            await interaction.response.send_message("❌ This isn't your game!", ephemeral=True)
            return
        
        if view.answered:
            await interaction.response.send_message("⏱️ You already made your choice!", ephemeral=True)
            return
        
        view.answered = True
        
        # Bot makes choice
        bot_choice = random.choice(["Rock", "Paper", "Scissors"])
        player_choice = self.choice
        
        # Determine winner
        result = view.determine_winner(player_choice, bot_choice)
        
        # Create result embed
        embed = discord.Embed(
            title="🎮 Rock Paper Scissors - Result",
            color=0x5865F2,
            timestamp=utcnow()
        )
        
        # Add visual representation
        choice_emoji = {
            "Rock": "🪨",
            "Paper": "📄",
            "Scissors": "✂️"
        }
        
        embed.add_field(
            name=f"👤 {interaction.user.display_name}",
            value=f"{choice_emoji[player_choice]} **{player_choice}**",
            inline=True
        )
        
        embed.add_field(
            name="🆚",
            value="_ _",
            inline=True
        )
        
        embed.add_field(
            name=f"🤖 {view.ctx.bot.user.display_name}",
            value=f"{choice_emoji[bot_choice]} **{bot_choice}**",
            inline=True
        )
        
        if result == "win":
            embed.description = "🎉 **You Win!** Congratulations!"
            embed.color = 0x57F287
        elif result == "lose":
            embed.description = "😔 **You Lose!** Better luck next time!"
            embed.color = 0xED4245
        else:
            embed.description = "🤝 **It's a Tie!** Great minds think alike!"
            embed.color = 0x95A5A6
        
        embed.set_footer(text=f"Player: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        
        # Disable all buttons
        for item in view.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=view)
        view.stop()


class RPSView(discord.ui.View):
    def __init__(self, ctx: commands.Context):
        super().__init__(timeout=30.0)
        self.ctx = ctx
        self.answered = False
        
        # Add choice buttons
        self.add_item(RPSButton("Rock", "🪨"))
        self.add_item(RPSButton("Paper", "📄"))
        self.add_item(RPSButton("Scissors", "✂️"))
    
    def determine_winner(self, player: str, bot: str) -> str:
        if player == bot:
            return "tie"
        
        winning_combos = {
            "Rock": "Scissors",
            "Paper": "Rock",
            "Scissors": "Paper"
        }
        
        if winning_combos[player] == bot:
            return "win"
        return "lose"
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        self.stop()


class RPS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name="rps")
    @commands.guild_only()
    async def rps(self, ctx: commands.Context):
        """🪨📄✂️ Play Rock Paper Scissors against the bot!"""
        embed = discord.Embed(
            title="🎮 Rock Paper Scissors",
            description="Choose your weapon! Will you win against me?",
            color=0x5865F2,
            timestamp=utcnow()
        )
        
        embed.add_field(
            name="How to Play",
            value=(
                "🪨 **Rock** beats Scissors\n"
                "📄 **Paper** beats Rock\n"
                "✂️ **Scissors** beats Paper"
            ),
            inline=False
        )
        
        embed.set_footer(text=f"Player: {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        
        view = RPSView(ctx)
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(RPS(bot))
