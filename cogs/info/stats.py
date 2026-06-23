import discord
from discord import app_commands
from discord.ext import commands
import os
import sys
import time
import platform
import psutil
import uuid
from typing import Optional

# ไอคอนและตัวแปรประจำโครงสร้างบอท Kitsumi
DEV_EMOJI = "<a:Dev:1513276345331880048>"
OWNER_EMOJI = "<:1000026559:1513308397519241257>"
COOLDOWN_TIME = 5.0

def make_progress_bar(percentage, size=10):
    filled_parts = round((percentage / 100) * size)
    clamped_filled = max(0, min(size, filled_parts))
    return "■" * clamped_filled + "□" * (size - clamped_filled)


# =======================================================
# 🎛️ STATUS DISCORD COMPONENTS (Dynamic Dropdown Menu)
# =======================================================
class StatusDropdown(discord.ui.Select):
    def __init__(self, bot, user):
        options = [
            discord.SelectOption(
                label="General & Network Stats", 
                value="0", 
                description="Core lifecycle, Uptime, Shard, and network latency.", 
                emoji="📊",
                default=True
            ),
            discord.SelectOption(
                label="System Resources Monitor", 
                value="1", 
                description="Hardware CPU cores, RAM matrix, and process footprints.", 
                emoji="💻"
            ),
            discord.SelectOption(
                label="Top Server Clusters", 
                value="2", 
                description="Highest priority guild associations logged in cache.", 
                emoji="🏆"
            ),
            discord.SelectOption(
                label="Development Operator Team", 
                value="3", 
                description="Systems engineering staff and creators overview.", 
                emoji="🔮"
            ),
            discord.SelectOption(
                 label="Experimental Hub",
                 value="4",
                 description="Additional sandbox telemetry nodes coming soon.",
                 emoji="🔜"
            )
        ]
        super().__init__(
            placeholder="Select an infrastructure matrix category...", 
            min_values=1, 
            max_values=1, 
            options=options,
            custom_id=f"kitsumi_status_select_{uuid.uuid4().hex[:6]}"
        )
        self.bot = bot
        self.user = user

    async def callback(self, interaction: discord.Interaction):
        page_idx = int(self.values[0])

        # ปรับสถานะ Default ไดนามิกเพื่อให้แถบเมนูแสดงหน้าที่เลือกอยู่ปัจจุบัน
        for option in self.options:
            option.default = (option.value == self.values[0])

        cog = self.bot.get_cog("Status")
        if cog:
            embed = await cog.build_status_embed(page_idx, self.user)
            await interaction.response.edit_message(embed=embed, view=self.view)


class StatusDashboardView(discord.ui.View):
    def __init__(self, bot, user):
        super().__init__(timeout=120.0) # แผงควบคุมเปิดทำงาน 2 นาที
        self.bot = bot
        self.user = user
        self.message = None  
        
        # ติดตั้ง Dropdown เมนูเข้าไปในเลย์เอาต์แผงวงจร
        self.add_item(StatusDropdown(bot, user))
        
        # ปุ่มทำลายแผงมอนิเตอร์เพื่อความสะอาดทางเน็ตเวิร์ก
        self.delete_btn = discord.ui.Button(
            label="Delete Dashboard",
            style=discord.ButtonStyle.danger,
            emoji="🗑️",
            custom_id=f"kitsumi_status_delete_{uuid.uuid4().hex[:6]}"
        )
        self.delete_btn.callback = self.delete_callback
        self.add_item(self.delete_btn)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("❌ This interface view is locked to the command owner.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        """⏱️ ปรับปรุงระบบทำลายปุ่มและ Dropdown ให้เป็นสีเทาเมื่อหมดเวลา ป้องกันปุ่มค้าง"""
        for item in self.children:
            item.disabled = True
            if isinstance(item, discord.ui.Button):
                item.label = "Expired Dashboard"
                item.style = discord.ButtonStyle.secondary
            elif isinstance(item, discord.ui.Select):
                item.placeholder = "Control Panel Expired"
                
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    async def delete_callback(self, interaction: discord.Interaction):
        await interaction.message.delete()


# =======================================================
# 📦 COG MODULE INFRASTRUCTURE (ระบบคำสั่งแบบ Hybrid)
# =======================================================
class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}

    def check_cooldown(self, user_id):
        now = time.time()
        if user_id in self.cooldowns:
            expiration = self.cooldowns[user_id] + COOLDOWN_TIME
            if now < expiration:
                return round(expiration - now, 1)
        self.cooldowns[user_id] = now
        return None

    async def build_status_embed(self, page_number, user) -> discord.Embed:
        embed = discord.Embed(timestamp=discord.utils.utcnow())
        
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(
            text=f"Page {page_number + 1}/5 • Powered by RzBot",
            icon_url=user.display_avatar.url
        )

        # ---------------------------------------------------
        # หน้าที่ 1: General & Discord Network Statistics
        # ---------------------------------------------------
        if page_number == 0:
            total_members = sum(g.member_count for g in self.bot.guilds if g.member_count)
            text_channels = sum(len(g.text_channels) for g in self.bot.guilds)
            voice_channels = sum(len(g.voice_channels) for g in self.bot.guilds)
            total_roles = sum(len(g.roles) for g in self.bot.guilds)

            latency = round(self.bot.latency * 1000)
            
            # ป้องกันข้อผิดพลาด Uptime หากไม่ได้ตั้งค่า start_time ไว้ล่วงหน้า
            start_time = getattr(self.bot, 'start_time', discord.utils.utcnow())
            uptime_diff = discord.utils.utcnow() - start_time
            days = uptime_diff.days
            hours, remainder = divmod(uptime_diff.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            embed.title = "📊 Kitsumi Deep Infrastructure Matrix"
            embed.color = 0x5865F2
            embed.description = (
                f"**Core Lifecycle and Socket Connectivity Diagnostics**\n"
                f"🕒 **Bot Uptime:** `{days}d {hours}h {minutes}m {seconds}s`\n"
                f"🔄 **Online Since:** <t:{int(start_time.timestamp())}:F>\n\n"
                f"⚙️ **Network Health:**\n"
                f"> 📡 **WebSocket Latency:** `{latency}ms`\n"
                f"> 🔌 **Shard Response:** `Cluster Node #01` (Global Shard)\n\n"
                f"🏠 **Guild Footprint:**\n"
                f"> 🌐 **Servers Indexed:** `{len(self.bot.guilds):,}` Guilds\n"
                f"> 👥 **Global Accounts:** `{total_members:,}` users\n"
                f"> 💬 **Channels Split:** `{text_channels:,}` Text / `{voice_channels:,}` Voice\n"
                f"> 🎭 **Total Roles:** `{total_roles:,}` entries\n\n"
                f"📦 **Engine Internal:**\n"
                f"> 📚 **Loaded Commands:** `{len(self.bot.commands)}` utilities\n"
                f"> 🐍 **Library Environment:** `discord.py v{discord.__version__}` | Python `{platform.python_version()}`"
            )

        # ---------------------------------------------------
        # หน้าที่ 2: Advanced System Resources Monitor
        # ---------------------------------------------------
        elif page_number == 1:
            cpu_usage = psutil.cpu_percent()
            cpu_cores = psutil.cpu_count()
            
            sv_mem = psutil.virtual_memory()
            total_mem_gb = sv_mem.total / (1024 ** 3)
            used_mem_gb = sv_mem.used / (1024 ** 3)
            ram_percent = sv_mem.percent

            process = psutil.Process(os.getpid())
            bot_ram_mb = process.memory_info().rss / (1024 ** 2)

            cpu_bar = make_progress_bar(cpu_usage)
            ram_bar = make_progress_bar(ram_percent)

            embed.title = "💻 Advanced System Resources & Memory Monitor"
            embed.color = 0x2ECC71 if cpu_usage < 60 else (0xE67E22 if cpu_usage < 85 else 0xE74C3C)
            embed.description = (
                f"🖥️ **Server CPU Load**\n"
                f"> {cpu_bar} `{cpu_usage}%` (Allocated: `{cpu_cores} Threads`)\n\n"
                f"🧠 **Hardware RAM Matrix**\n"
                f"> {ram_bar} `{ram_percent}%` (`{used_mem_gb:.1f}GB` / `{total_mem_gb:.1f}GB`)\n\n"
                f"🤖 **Python Process Footprint (Bot Specific)**\n"
                f"> Total Process RSS Allocation: `{bot_ram_mb:.2f} MB`\n\n"
                f"⚙️ **Operating System Core:**\n"
                f"> Platform Kernel: `{platform.system()} ({platform.machine()})` v`{platform.release()}`"
            )

        # ---------------------------------------------------
        # หน้าที่ 3: Top Servers Rankings
        # ---------------------------------------------------
        elif page_number == 2:
            sorted_guilds = sorted(self.bot.guilds, key=lambda g: g.member_count or 0, reverse=True)[:5]
            
            lines = []
            if not sorted_guilds:
                lines.append("No active guild connections discovered yet.")
            else:
                for idx, guild in enumerate(sorted_guilds):
                    badge = "⭐ " if "VERIFIED" in guild.features else ""
                    lines.append(f"**{idx + 1}.** {badge}{guild.name}\n> ID: `{guild.id}` • 👥 Cache: `{guild.member_count:,}` accounts")

            embed.title = "🏆 Top Server Clusters Discovery"
            embed.color = 0xF1C40F
            embed.description = "*Listing highest priority guild associations logged inside local cache.*\n\n" + "\n\n".join(lines)

        # ---------------------------------------------------
        # หน้าที่ 4: Dev Team Credits
        # ---------------------------------------------------
        elif page_number == 3:
            embed.title = f"{DEV_EMOJI} Development Operator Team"
            embed.color = 0x9B59B6
            embed.description = (
                f"The core network and systems engineering staff responsible for cluster node deployments and backend codebase maintenance.\n\n"
                f"{OWNER_EMOJI} **Lead Systems Architect:**\n"
                f"> Name: **`Rz.xy`**\n"
                f"> Assignment: `Project Owner & Principal Contributor`"
            )

        # ---------------------------------------------------
        # หน้าที่ 5: Test / Soon Page (จัดระเบียบบรรทัดเรียบร้อย)
        # ---------------------------------------------------
        elif page_number == 4:
            embed.title = "⚙️ Experimental Hub Module"
            embed.color = 0x7F8C8D
            embed.description = (
                "**Deployments Status: `PENDING_ARCHITECTURAL_SETUP`**\n"
                "New customized operational features and sandbox telemetry vectors will be mapped into this data slot soon.\n\n"
                "> :3"
            )
            
        return embed

    # =======================================================
    # ⚡ 2-in-1 HYBRID COMMAND UTILITY (?status & /status)
    # =======================================================
    @commands.hybrid_command(
        name="status", 
        with_app_command=True,
        aliases=["stats", "botinfo", "sta", "Status", "Stats", "Botinfo", "Info", "info"],
        description="View bot's advanced live statistics and deep performance matrix! 📊"
    )
    @commands.guild_only()
    async def status_command(self, ctx: commands.Context):
        time_left = self.check_cooldown(ctx.author.id)
        if time_left:
            return await ctx.send(f"⏳ **Calm down!** Please wait **{time_left}** seconds before using this command again.", ephemeral=True)
        
        view = StatusDashboardView(self.bot, ctx.author)
        first_embed = await self.build_status_embed(0, ctx.author)
        
        msg = await ctx.send(embed=first_embed, view=view)
        view.message = msg


async def setup(bot):
    await bot.add_cog(Status(bot))
