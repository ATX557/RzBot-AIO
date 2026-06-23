import discord
from discord.ext import commands
from discord import app_commands
import aiosqlite
import time
import os
from typing import Optional

# =======================================================
# 🎛️ DISCORD BUTTONS VIEW FOR AFK MATRIX
# =======================================================
class AFKView(discord.ui.View):
    def __init__(self, cog, user: discord.Member, reason: str):
        super().__init__(timeout=60)  # Interactivity expires after 60 seconds
        self.cog = cog
        self.user = user
        self.reason = reason
        self.message = None  # Holds reference to the message for timeout cleanups

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Enforces restriction matrix: only the command initiator can interact."""
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ You cannot configure someone else's AFK status.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        """⏳ Clean up the interactive menu upon expiration to avoid floating components."""
        if self.message:
            try:
                await self.message.edit(content="⏳ **Timeout:** AFK setup menu has expired.", embed=None, view=None)
            except Exception:
                pass

    # 🌐 Option 1: Worldwide Scope
    @discord.ui.button(label="Worldwide", style=discord.ButtonStyle.blurple, emoji="🌐")
    async def worldwide_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        now_ts = int(time.time())
        # guild_id = 0 acts as the universal constant for global tracking across all networks
        async with aiosqlite.connect(self.cog.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO afk_matrix (user_id, guild_id, reason, afk_since) VALUES (?, ?, ?, ?)",
                (self.user.id, 0, self.reason, now_ts)
            )
            await db.commit()

        self.stop()
        await interaction.response.edit_message(content="🟩 **Worldwide Telemetry Synced:** Your global AFK status is now active.", embed=None, view=None)
        
        embed = discord.Embed(
            title="😴 Global AFK Mode Activated",
            description=f"{self.user.mention} is now AFK (Worldwide): **{self.reason}**\n*Status broadcasted into the cybernetic network.*",
            color=0x3498db,
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Activated by {self.user.name}", icon_url=self.user.display_avatar.url)
        await interaction.channel.send(embed=embed)

    # 🏠 Option 2: Server-Specific Scope
    @discord.ui.button(label="Server Only", style=discord.ButtonStyle.success, emoji="🏠")
    async def server_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        now_ts = int(time.time())
        async with aiosqlite.connect(self.cog.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO afk_matrix (user_id, guild_id, reason, afk_since) VALUES (?, ?, ?, ?)",
                (self.user.id, interaction.guild_id, self.reason, now_ts)
            )
            await db.commit()

        self.stop()
        await interaction.response.edit_message(content="🟩 **Server Telemetry Synced:** Your local AFK status is active in this server.", embed=None, view=None)
        
        embed = discord.Embed(
            title="😴 Server AFK Mode Activated",
            description=f"{self.user.mention} is now AFK (Server Only): **{self.reason}**\n*Status logged into the local guild registry.*",
            color=0x2ecc71,
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Activated by {self.user.name}", icon_url=self.user.display_avatar.url)
        await interaction.channel.send(embed=embed)

    # ❌ Option 3: Abort Process
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger, emoji="<:No:1517480787744784475>")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.edit_message(content="🟥 **Operation Aborted:** AFK setup has been canceled.", embed=None, view=None)


# =======================================================
# 😴 MAIN AFK COG CORE ENGINE
# =======================================================
class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_folder = "SQL" 
        self.db_path = f"{self.db_folder}/kitsumi_afk.db"

    async def cog_load(self):
        """🚀 Initializes database directories and structure upon loading the extension."""
        if not os.path.exists(self.db_folder):
            os.makedirs(self.db_folder)
            print(f"[SYSTEM MATRIX] 📁 Folder '{self.db_folder}' not found. Automatically created via core structure layout.")

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS afk_matrix (
                    user_id INTEGER,
                    guild_id INTEGER,
                    reason TEXT,
                    afk_since INTEGER,
                    PRIMARY KEY (user_id, guild_id)
                )
            """)
            await db.commit()

    # =======================================================
    # 😴 SET AFK COMMAND MODE (HYBRID)
    # =======================================================
    @commands.hybrid_command(
        name="afk",
        aliases=["setafk", "sleep"],
        description="😴 Enter AFK status with interactive scope mapping options."
    )
    @app_commands.describe(reason="Provide the reason for entering isolation mode.")
    @commands.guild_only()
    async def afk_command(self, ctx: commands.Context, *, reason: Optional[str] = "AFK"):
        """Dispatches an interactive UI matrix for scope allocation."""
        
        guide_embed = discord.Embed(
            title="📊 AFK Scope Configuration Matrix",
            description=f"Hello {ctx.author.mention}, please select the operational scope for your AFK status.\n\n"
                        f"**Reason:** `{reason}`\n\n"
                        f"**Button Function Guide:**\n"
                        f"🌐 **Worldwide**\n"
                        f"└ Globally tracks your presence. The bot will trigger alerts across **all mutual servers**.\n\n"
                        f"🏠 **Server Only**\n"
                        f"└ Restricts telemetry to this server only. Interacting elsewhere remains unaffected.\n\n"
                        f"<:No:1517480787744784475> **Cancel**\n"
                        f"└ Immediate abort. Discards configurations and leaves matrix clean.",
            color=0x95A5A6
        )
        guide_embed.set_footer(text="This interactive selection matrix will expire in 60 seconds.")
        
        view = AFKView(cog=self, user=ctx.author, reason=reason)
        
        # Context-aware dispatch handles hybrid routing seamlessly (Ephemeral for slash context)
        view.message = await ctx.send(embed=guide_embed, view=view, ephemeral=True)

    # =======================================================
    # 📡 DETECT MESSAGE & DISMANTLE AFK
    # =======================================================
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Intercepts communication arrays to drop active matrices or broadcast alert tags."""
        if message.author.bot or not message.guild:
            return
            
        if message.content.startswith(("/", "!", ".")):
            return

        guild_id = message.guild.id
        author_id = message.author.id
        now_ts = int(time.time())

        async with aiosqlite.connect(self.db_path) as db:
            # 1. Evaluate sender status across local server tracking or global indices (guild_id = 0)
            async with db.execute(
                "SELECT reason, afk_since, guild_id FROM afk_matrix WHERE user_id = ? AND (guild_id = ? OR guild_id = 0)", 
                (author_id, guild_id)
            ) as cursor:
                author_afk = await cursor.fetchone()

            if author_afk:
                reason, afk_since, matched_guild = author_afk
                
                # 🧹 Instant garbage collection prevents SQL overhead or response delay
                await db.execute("DELETE FROM afk_matrix WHERE user_id = ? AND guild_id = ?", (author_id, matched_guild))
                await db.commit()

                duration_secs = max(0, now_ts - afk_since)
                hours, remainder = divmod(duration_secs, 3600)
                minutes, seconds = divmod(remainder, 60)
                
                time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m {seconds}s"

                embed_back = discord.Embed(
                    title="👋 Welcome Back!",
                    description=f"{message.author.mention} is no longer AFK.\nYou were away for **{time_str}**",
                    color=0x2ECC71
                )
                await message.channel.send(embed=embed_back, delete_after=6)

            # 2. Monitor pings or mentions aimed at currently isolated accounts
            if message.mentions:
                for target_user in message.mentions:
                    if target_user.id == author_id:
                        continue
                        
                    async with db.execute(
                        "SELECT reason, afk_since FROM afk_matrix WHERE user_id = ? AND (guild_id = ? OR guild_id = 0)", 
                        (target_user.id, guild_id)
                    ) as cursor:
                        target_afk = await cursor.fetchone()

                    if target_afk:
                        t_reason, t_since, _ = target_afk
                        embed_notify = discord.Embed(
                            description=f"💤 {target_user.mention} is currently AFK: **{t_reason}**\n*Active since: <t:{t_since}:R>*",
                            color=0x95A5A6
                        )
                        await message.channel.send(embed=embed_notify, delete_after=6)

    # ==========================================
    # 🧹 SYSTEM GARBAGE COLLECTION PURGE
    # ==========================================
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Purges telemetry data instantly when a user breaks sync with a server."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT 1 FROM afk_matrix WHERE user_id = ? AND guild_id = ?", (member.id, member.guild.id)) as cursor:
                exists = await cursor.fetchone()
                
            if exists:
                await db.execute("DELETE FROM afk_matrix WHERE user_id = ? AND guild_id = ?", (member.id, member.guild.id))
                await db.commit()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        """Wipes localized data matrices if the application is removed from a server."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM afk_matrix WHERE guild_id = ?", (guild.id,)) as cursor:
                count = await cursor.fetchone()
                
            if count and count[0] > 0:
                await db.execute("DELETE FROM afk_matrix WHERE guild_id = ?", (guild.id,))
                await db.commit()


async def setup(bot):
    await bot.add_cog(AFK(bot))
