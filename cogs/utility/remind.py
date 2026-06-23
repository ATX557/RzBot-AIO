import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiosqlite
import time
import os
from typing import Optional

class UtilityRemind(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db_folder = "SQL"
        self.db_path = f"{self.db_folder}/kitsumi_reminders.db"

    def cog_unload(self):
        # Cancel the scheduler loop safely when cog is unloaded
        self.reminder_scheduler.cancel()

    async def cog_load(self):
        """🚀 Initializes the SQL table schema upon loading the cog module."""
        if not os.path.exists(self.db_folder):
            os.makedirs(self.db_folder)
            print(f"[SYSTEM MATRIX] 📁 Folder '{self.db_folder}' generated automatically for reminders node.")

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS reminders_matrix (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    guild_id INTEGER,
                    channel_id INTEGER,
                    message TEXT,
                    trigger_time INTEGER,
                    created_time INTEGER
                )
            """)
            await db.commit()
            
        # ⚡ ย้ายมาเริ่มรันตรงนี้หลังจากมั่นใจว่าฐานข้อมูลถูกสร้างขึ้นเสร็จแล้ว
        if not self.reminder_scheduler.is_running():
            self.reminder_scheduler.start()

    # =======================================================
    # ⏱️ ACTIVE BACKGROUND SCHEDULER TASK LOOP
    # =======================================================
    @tasks.loop(seconds=5.0)
    async def reminder_scheduler(self):
        """Background process ticking every 5 seconds to route expired records to targets."""
        now_ts = int(time.time())
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id, user_id, guild_id, channel_id, message, created_time FROM reminders_matrix WHERE trigger_time <= ?", 
                (now_ts,)
            ) as cursor:
                expired_reminders = await cursor.fetchall()

            if not expired_reminders:
                return

            for row in expired_reminders:
                row_id, user_id, guild_id, channel_id, message, created_time = row
                
                user = self.bot.get_user(user_id) or await self.bot.fetch_user(user_id)
                if not user:
                    # Clean up if user profile is fundamentally deleted/not found from cache matrix
                    await db.execute("DELETE FROM reminders_matrix WHERE id = ?", (row_id,))
                    continue

                # Construct professional Cyberpunk Slate-Dark Alert interface
                alert_embed = discord.Embed(
                    title="⏰ Reminder Alert!",
                    description=f"{user.mention}, your scheduled reminder is firing!",
                    color=0xE67E22,
                    timestamp=discord.utils.utcnow()
                )
                # 🛠️ แก้ไขปัญหา Syntax ตรงนี้ให้เรียบร้อยแล้ว
                alert_embed.add_field(
                    name="📝 You Asked Me To Remind You",
                    value=f"```text\n{message}\n```",
                    inline=False
                )
                alert_embed.add_field(
                    name="🕐 Original Registration",
                    value=f"<t:{created_time}:F> (<t:{created_time}:R>)",
                    inline=False
                )
                alert_embed.set_footer(text="Kitsumi Autonomous Reminder Node")

                # Step 1: Attempt to deliver alert directly via User DMs
                notified = False
                try:
                    await user.send(content=f"⏰ {user.mention} **Direct Dispatch Alert**", embed=alert_embed)
                    notified = True
                except discord.Forbidden:
                    pass  # User DMs closed or blocked by privacy grids

                # Step 2: Fallback routing system — Locate user in a mutual server channel environment
                if not notified:
                    guild = self.bot.get_guild(guild_id)
                    channel = guild.get_channel(channel_id) if guild else None

                    # Try original channel entry first
                    if channel:
                        try:
                            await channel.send(content=user.mention, embed=alert_embed)
                            notified = True
                        except discord.Forbidden:
                            pass

                    # Exhaustive mutual grid fallbacks scanning if original route fails
                    if not notified:
                        for target_guild in self.bot.guilds:
                            member = target_guild.get_member(user_id)
                            if member:
                                # Scan for a clean system/text channel with message delivery rights enabled
                                for fallback_channel in target_guild.text_channels:
                                    permissions = fallback_channel.permissions_for(target_guild.me)
                                    if permissions.send_messages and permissions.embed_links:
                                        try:
                                            await fallback_channel.send(content=f"⏰ {user.mention} (DM Delivery Failed Fallback)", embed=alert_embed)
                                            notified = True
                                            break
                                        except discord.HTTPException:
                                            continue
                            if notified:
                                break

                # Clean up executed record entries instantly
                await db.execute("DELETE FROM reminders_matrix WHERE id = ?", (row_id,))
            
            await db.commit()

    @reminder_scheduler.before_loop
    async def before_scheduler(self):
        await self.bot.wait_until_ready()

    # =======================================================
    # 📝 REMINDER REGISTRATION GATEWAY
    # =======================================================
    @commands.hybrid_command(
        name="remind",
        aliases=["remindme", "reminder"],
        description="⏰ Set a persistent reminder that triggers after a specified duration (Minutes/Hours/Days)."
    )
    @app_commands.describe(
        duration="Time scale configurations: 15m, 2h, 3d (minutes/hours/days)",
        message="The notification payload content the bot will ping you with."
    )
    @commands.guild_only()
    async def remind_command(self, ctx: commands.Context, duration: str, *, message: str):
        """Validates structural parameter horizons and allocates records up to a 3-entry limit ceiling."""
        await ctx.defer()

        try:
            unit = duration[-1].lower()
            value = int(duration[:-1])
            
            # Short-scale tracking restriction (Enforcing strict Minutes/Hours/Days formats)
            multipliers = {
                'm': 60,
                'h': 3600,
                'd': 86400
            }
            
            if unit not in multipliers or value <= 0:
                embed_err = discord.Embed(
                    description="<:No:1517480787744784475> **Invalid Duration Configuration**\nAccepted formats use: `5m` (Minutes), `2h` (Hours), or `1d` (Days).",
                    color=0xE74C3C
                )
                return await ctx.send(embed=embed_err)
            
            seconds = value * multipliers[unit]
            
            # Max boundary limit checks: 7 Days maximum
            if seconds > 604800:
                embed_err = discord.Embed(
                    description="<:No:1517480787744784475> **Duration Boundary Breach:** Maximum processing horizon cannot exceed **7 days**.",
                    color=0xE74C3C
                )
                return await ctx.send(embed=embed_err)

            # --- SECURITY & DATABASE SPAM FIREWALL (MAX 3 TOTAL CHECK) ---
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute(
                    "SELECT COUNT(*) FROM reminders_matrix WHERE user_id = ?", 
                    (ctx.author.id,)
                ) as cursor:
                    count_row = await cursor.fetchone()
                    active_count = count_row[0] if count_row else 0

                if active_count >= 3:
                    embed_limit = discord.Embed(
                        title="🛡️ Active Reminder Boundary Triggered",
                        description=(
                            f"<:No:1517480787744784475> **Request Blocked:** You currently have `{active_count}` active reminders registered globally across this bot's framework.\n"
                            "To optimize system storage allocations, you are limited to a maximum of **3 active reminders** globally."
                        ),
                        color=0xED4245
                    )
                    return await ctx.send(embed=embed_limit)

                now_ts = int(time.time())
                trigger_ts = now_ts + seconds

                # Secure data layout tracking array injection
                await db.execute(
                    "INSERT INTO reminders_matrix (user_id, guild_id, channel_id, message, trigger_time, created_time) VALUES (?, ?, ?, ?, ?, ?)",
                    (ctx.author.id, ctx.guild.id, ctx.channel.id, message, trigger_ts, now_ts)
                )
                await db.commit()

            success_embed = discord.Embed(
                title="⏰ Reminder Set Successfully",
                description=f"I will alert your client node <t:{trigger_ts}:R>.",
                color=0x2ECC71,
                timestamp=discord.utils.utcnow()
            )
            success_embed.add_field(
                name="📝 Reminder Content",
                value=f"```text\n{message}\n```",
                inline=False
            )
            success_embed.add_field(
                name="⏱️ Scheduled Delivery Time",
                value=f"<t:{trigger_ts}:F>",
                inline=False
            )
            success_embed.set_footer(
                text=f"Global Queue Matrix: {active_count + 1}/3 allocated • Managed for {ctx.author.name}",
                icon_url=ctx.author.display_avatar.url
            )
            await ctx.send(embed=success_embed)

        except (ValueError, IndexError):
            embed_err = discord.Embed(
                description="<:No:1517480787744784475> **Invalid Parsing Syntax:** Use standard operational patterns like `?remind 45m Update documentation`.",
                color=0xE74C3C
            )
            await ctx.send(embed=embed_err)
        except Exception as e:
            embed_err = discord.Embed(
                description=f"<:No:1517480787744784475> **System Exception Error Encountered:** `{str(e)}`",
                color=0xE74C3C
            )
            await ctx.send(embed=embed_err)

    # =======================================================
    # 🧹 DYNAMIC GARBAGE COLLECTION PURGING (ล้างขยะ)
    # =======================================================
    @commands.hybrid_command(
        name="unremindall",
        description="🧹 Erase and wipe all your active reminder tracking records from the SQL memory core."
    )
    @commands.guild_only()
    async def unremind_all_command(self, ctx: commands.Context):
        """Deletes all active reminder objects matching the user's ID across the SQL architecture."""
        await ctx.defer()

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM reminders_matrix WHERE user_id = ?", 
                (ctx.author.id,)
            ) as cursor:
                count_row = await cursor.fetchone()
                total_records = count_row[0] if count_row else 0

            if total_records == 0:
                empty_embed = discord.Embed(
                    description="ℹ️ You have no active running reminders registered inside the tracking database matrix.",
                    color=0xF1C40F
                )
                return await ctx.send(embed=empty_embed)

            # Purge the tracking grid immediately
            await db.execute("DELETE FROM reminders_matrix WHERE user_id = ?", (ctx.author.id,))
            await db.commit()

        purge_embed = discord.Embed(
            title="🧹 Database Compaction Successful",
            description=f"Successfully wiped and destroyed `{total_records}` active reminder nodes for your user identity registry.",
            color=0x34495E,
            timestamp=discord.utils.utcnow()
        )
        purge_embed.set_footer(text="Garbage Collection Complete • SQL Nodes Purged")
        await ctx.send(embed=purge_embed)

    # 🛠️ เอาบรรทัดที่ผิดหลักออกเรียบร้อยแล้ว

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """🧹 Clears queued reminders immediately if the target user leaves, is kicked, or is banned from a server context."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM reminders_matrix WHERE user_id = ? AND guild_id = ?", 
                (member.id, member.guild.id)
            ) as cursor:
                count_row = await cursor.fetchone()
                count = count_row[0] if count_row else 0
                
            if count > 0:
                await db.execute("DELETE FROM reminders_matrix WHERE user_id = ? AND guild_id = ?", (member.id, member.guild.id))
                await db.commit()
                print(f"[SQL COMPACTION] Purged {count} orphaned reminders for left/banned user: {member.id} from guild: {member.guild.id}")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        """🧹 Clears entire queues if Kitsumi Bot is removed from a guild environment entirely."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM reminders_matrix WHERE guild_id = ?", 
                (guild.id,)
            ) as cursor:
                count_row = await cursor.fetchone()
                count = count_row[0] if count_row else 0
                
            if count > 0:
                await db.execute("DELETE FROM reminders_matrix WHERE guild_id = ?", (guild.id,))
                await db.commit()
                print(f"[SQL COMPACTION] Purged {count} orphaned reminders because Bot left guild: {guild.id}")


async def setup(bot: commands.Bot):
    await bot.add_cog(UtilityRemind(bot))
