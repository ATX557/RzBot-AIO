import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import random
from typing import Optional
from discord.utils import utcnow

class Meme(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._session: Optional[aiohttp.ClientSession] = None
        # Safe array of premium meme-hub subreddits
        self.meme_subreddits = ["memes", "dankmemes", "wholesomememes", "me_irl"]

    async def get_session(self) -> aiohttp.ClientSession:
        """Lazy loads and returns a persistent aiohttp ClientSession."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def cog_unload(self):
        """Ensures the underlying session is closed when the cog unloads."""
        if self._session and not self._session.closed:
            self.bot.loop.create_task(self._session.close())

    @commands.hybrid_command(name="meme", aliases=["getmeme", "memes", "Meme", "Memes"])
    async def meme(self, ctx: commands.Context):
        """🖼️ Fetch a random, hot meme from selected subreddits safely."""
        await ctx.defer()
        
        try:
            # Randomly select a target community node
            target_sub = random.choice(self.meme_subreddits)
            url = f"https://meme-api.com/gimme/{target_sub}"
            
            session = await self.get_session()
            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    return await ctx.send("<:No:1517480787744784475> **API Error:** Unable to reach the remote meme transmission server.")
                
                data = await response.json()
                
                # Extract and enforce safety guardrails (Skip NSFW or Spoilers)
                if data.get("nsfw") or data.get("spoiler"):
                    return await ctx.send("⚠️ **Content Blocked:** Fetched a meme marked as unsafe. Please try running the command again.")
                
                meme_title = data.get("title", "Untitled Meme")
                meme_url = data.get("url")
                post_link = data.get("postLink", "https://reddit.com")
                upvotes = data.get("ups", 0)
                author = data.get("author", "Unknown")
                
                if not meme_url:
                    return await ctx.send("<:No:1517480787744784475> **Data Error:** Received invalid payload structure from endpoint.")

                # Design Responsive Media Embed Structure
                embed = discord.Embed(
                    title=f"✨ {meme_title}",
                    url=post_link,
                    color=0xE74C3C,  # Vibrant Reddit Orange-Red
                    timestamp=utcnow()
                )
                
                # Inject image payload safely
                embed.set_image(url=meme_url)
                
                # Render metadata stats
                embed.add_field(name="🌐 Send by", value=f"r/{target_sub}", inline=True)
                
                embed.set_footer(
                    text=f"Posted by u/{author}｜Up {upvotes:,}",
                    icon_url="https://www.redditstatic.com/desktop2x/img/favicon/apple-icon-57x57.png"
                )
                
                await ctx.send(embed=embed)
                
        except aiohttp.ClientError:
            await ctx.send("❌ **Network Topology Error:** Connection timed out while downloading media data.")
        except Exception as e:
            await ctx.send(f"❌ **System Exception:** Internal runtime error encountered: `{type(e).__name__}`")

async def setup(bot):
    await bot.add_cog(Meme(bot))
      
