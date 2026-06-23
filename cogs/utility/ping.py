import discord
from discord.ext import commands
import time

# =======================================================
# 📦 COG MODULE INFRASTRUCTURE FOR LATENCY CHECK
# =======================================================
class PingCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="ping",
        with_app_command=True,
        description="Check the current response latency and WebSocket handshake speed of the bot. 🏓"
    )
    @commands.guild_only()
    async def ping_command(self, ctx: commands.Context):
        """Measures network gateway latency and application engine performance"""
        # Capture the high-resolution start time counter before sending the message
        start_time = time.perf_counter()
        
        # Acknowledge the interaction with a temporary localized loading response
        interaction_msg = await ctx.send("📡 *Establishing secure handshake with Discord Gateway...*", ephemeral=True)
        
        # Calculate the internal processing delay (REST API latency)
        end_time = time.perf_counter()
        api_latency = round((end_time - start_time) * 1000)
        
        # Fetch the native WebSocket heartbeat shard latency
        websocket_latency = round(self.bot.latency * 1000)
        
        # Evaluate network connection health threshold and assign status bars
        if websocket_latency < 80:
            latency_rating = "🟢 Excellent Network Synergy"
        elif websocket_latency < 180:
            latency_rating = "🟡 Average Connection Response"
        else:
            latency_rating = "🔴 High Network Congestion Warning"

        # Construct premium technical dark slate embed layout
        embed = discord.Embed(
            title="🏓 RzBot Network • Connection Latency Metrics",
            description="Diagnostic statistics analyzing the connection packet data flow to the Discord Cluster.",
            color=0x2B2D31,
            timestamp=discord.utils.utcnow()
        )
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        embed.add_field(
            name="📡 Gateway Handshake (WebSocket)", 
            value=f"> ↳ `{websocket_latency} ms`", 
            inline=True
        )
        embed.add_field(
            name="💻 Message Processing (REST API)", 
            value=f"> ↳ `{api_latency} ms`", 
            inline=True
        )
        embed.add_field(
            name="📊 Operational Connection Health", 
            value=f"> ↳ **{latency_rating}**", 
            inline=False
        )
        
        embed.set_footer(text=f"Requested by {ctx.author.name} • Infrastructure Live")

        # Edit the initial loading text to show the final premium metric embed matrix
        await interaction_msg.edit(content=None, embed=embed)


async def setup(bot):
    await bot.add_cog(PingCommand(bot))
      
