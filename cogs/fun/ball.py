import discord
from discord.ext import commands
from discord import app_commands
import random
from discord.utils import utcnow

class Magic8Ball(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        self.positive_responses = [
            "It is certain.",
            "It is decidedly so.",
            "Without a doubt.",
            "Yes, definitely.",
            "You may rely on it.",
            "As I see it, yes.",
            "Most likely.",
            "Outlook good."
        ]
        
        self.neutral_responses = [
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again."
        ]
        
        self.negative_responses = [
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful."
        ]

    @commands.hybrid_command(name="8ball", aliases=["eightball", "ask"])
    @app_commands.describe(question="The question you want to ask the Magic 8-Ball")
    @commands.guild_only()
    async def eight_ball(self, ctx: commands.Context, *, question: str):
        """🔮 Consult the Magic 8-Ball for cosmic guidance."""
        await ctx.defer()
        
        # Select category and define UI aesthetics
        category = random.choice(["positive", "neutral", "negative"])
        
        if category == "positive":
            answer = random.choice(self.positive_responses)
            embed_color = 0x2ECC71  # Success Green
        elif category == "neutral":
            answer = random.choice(self.neutral_responses)
            embed_color = 0xF1C40F  # Warning Yellow
        else:
            answer = random.choice(self.negative_responses)
            embed_color = 0xE74C3C  # Danger Red

        # Construct the response embed
        embed = discord.Embed(
            title="🔮 Magic 8-Ball Oracle",
            color=embed_color,
            timestamp=utcnow()
        )
        
        embed.add_field(name="❓ Your Question:", value=f"*{question}*", inline=False)
        embed.add_field(name="🎱 8-Ball Prediction:", value=f"**{answer}**", inline=False)
        
        embed.set_footer(
            text=f"Requested by {ctx.author.name} | Future is uncertain.", 
            icon_url=ctx.author.display_avatar.url
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Magic8Ball(bot))
