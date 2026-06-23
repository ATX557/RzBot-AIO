import discord
from discord import app_commands
from discord.ext import commands
import time
from datetime import datetime, timezone

class UtilityUptime(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # ล็อกเวลาเริ่มต้นระบบ (Boot Time) ทันทีเมื่อโมดูลถูกโหลดเข้าสู่ตัวบอท
        self.boot_time = time.time()

    @commands.hybrid_command(
        name="uptime",
        aliases=["runtime"],
        description="📡 Display the continuous active runtime metrics of the bot core."
    )
    @commands.guild_only()
    async def uptime_command(self, ctx: commands.Context):
        """Calculates total system runtime elapsed since the current boot sequence."""
        await ctx.defer()

        # 1. คำนวณหาความแตกต่างระหว่างเวลาปัจจุบันกับเวลาที่บอทรันระบบ
        current_time = time.time()
        uptime_seconds = int(current_time - self.boot_time)

        # 2. ทำการแยกหน่วยวินาทีออกเป็น วัน, ชั่วโมง, นาที และวินาที (Duration Parsing)
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        # 3. จัดการฟอร์แมตข้อความการแสดงผลเพื่อความเรียบร้อย
        uptime_string = ""
        if days > 0:
            uptime_string += f"`{days}d` "
        if hours > 0 or days > 0:
            uptime_string += f"`{hours}h` "
        if minutes > 0 or hours > 0 or days > 0:
            uptime_string += f"`{minutes}m` "
        uptime_string += f"`{seconds}s`"

        # 4. แปลง Timestamp ของเวลารันระบบเพื่อให้แสดงผลเป็นแบบสากลของ Discord
        boot_timestamp = int(self.boot_time)

        # 5. ประกอบร่างแผงควบคุมสไตล์ Cybernetic Node Interface
        embed = discord.Embed(
            title="📡 Core System Telemetry",
            description="The central computing core is currently fully functional and operational.",
            color=0x3498DB,
            timestamp=discord.utils.utcnow()
        )
        
        embed.add_field(
            name="⏱️ Operational Uptime",
            value=f"> {uptime_string}",
            inline=False
        )
        embed.add_field(
            name="🚀 Core Boot Sequence Init",
            value=f"> ↳ <t:{boot_timestamp}:F>\n> *Initialized: <t:{boot_timestamp}:R>*",
            inline=False
        )
        embed.add_field(
            name="📶 API Latency",
            value=f"> ↳ `{round(self.bot.latency * 1000, 2)} ms`",
            inline=True
        )
        embed.add_field(
            name="🛡️ System Status",
            value="> ↳ `🟢 ONLINE`",
            inline=True
        )

        embed.set_footer(
            text=f"Requested by {ctx.author.name}",
            icon_url=ctx.author.display_avatar.url
        )

        # ส่งแผงควบคุมความเร็วและสถานะกลับไปยังแชนเนลห้องแชท
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(UtilityUptime(bot))
