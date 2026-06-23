import discord
from discord.ext import commands
from discord import app_commands
import random
from discord.utils import utcnow

class Coinflip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Core outcomes array
        self.outcomes = ["Heads", "Tails"]

    @commands.hybrid_command(name="coinflip", aliases=["flip", "coin"])
    @commands.guild_only()
    async def coin_flip(self, ctx: commands.Context):
        """🪙 Flip a coin to get an immediate random result of Heads or Tails."""
        await ctx.defer()
        
        # Execute the random outcome simulation
        result = random.choice(self.outcomes)
        
        # Define unique aesthetic details based on the outcome
        if result == "Heads":
            embed_color = 0xF1C40F
            display_text = "🪙 **Heads!** The coin landed face up."
        else:
            embed_color = 0xE67E22
            display_text = "🪙 **Tails!** The coin landed face down."

        # Build the responsive telemetry embed matrix
        embed = discord.Embed(
            title="🪙 Coin Flip Simulator",
            description=display_text,
            color=embed_color,
            timestamp=utcnow()
        )
        
        # Add data metrics
        embed.add_field(name="Outcome Status", value=f"`{result.upper()}`", inline=True)
        embed.add_field(name="Entropy Method", value="`Mersenne Twister PRNG`", inline=True)
        
        embed.set_footer(
            text=f"Flipped by {ctx.author.name} | Physics Simulation Node",
            icon_url=ctx.author.display_avatar.url
        )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Coinflip(bot))
