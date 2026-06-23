import discord
from discord import app_commands
from discord.ext import commands
import datetime
from datetime import datetime as dt, timezone
from typing import Optional

class Mute(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_color = 0x2B2D31

    # ==========================================
    # 🔇 COMMAND: TIMEOUT/MUTE PROTOCOL
    # ==========================================
    @commands.hybrid_command(
        name="mute",
        description="🔇 Temporarily restrict a member from transmitting data and append a server mute matrix tag."
    )
    @app_commands.describe(
        member="The target user identity to put on timeout.",
        duration="Matrix lifetime parameters (e.g., 30m, 2h, 3d). Max threshold is 3d.",
        reason="The formal data validation log reason for this communication restriction."
    )
    @commands.guild_only()
    @commands.has_permissions(moderate_members=True) # 🛡️ แอดมินต้องมีสิทธิ์จัดการสมาชิก
    @commands.bot_has_permissions(moderate_members=True, manage_nicknames=True) # 🤖 บอทต้องมีสิทธิ์จัดการสมาชิกและเปลี่ยนชื่อเล่นด้วย
    async def mute_command(
        self, 
        ctx: commands.Context, 
        member: discord.Member, 
        duration: str,
        *, 
        reason: Optional[str] = "No analytical reason specified by authority."
    ):
        """Executes a temporary restriction matrix against a target node's communication lines."""
        await ctx.defer()

        # 🛑 SECURITY LAYER 1: ป้องกันการปิดปากตัวเอง
        if member.id == ctx.author.id:
            embed_err = discord.Embed(description="❌ **Termination Aborted:** You cannot execute the mute protocol upon your own node signature.", color=0xE74C3C)
            return await ctx.interaction.followup.send(embed=embed_err, ephemeral=True)

        # 🛑 SECURITY LAYER 2: ป้องกันการปิดปากเจ้าของเซิร์ฟเวอร์
        if member.id == ctx.guild.owner_id:
            embed_err = discord.Embed(description="❌ **Termination Aborted:** Target node holds the ultimate ownership matrix key. Action denied.", color=0xE74C3C)
            return await ctx.interaction.followup.send(embed=embed_err, ephemeral=True)

        # 🛑 SECURITY LAYER 3: ตรวจสอบระดับยศของแอดมิน
        if ctx.author.id != ctx.guild.owner_id and ctx.author.top_role <= member.top_role:
            embed_err = discord.Embed(description="❌ **Access Denied:** Your authorization clearance rank is equal to or lower than the target node.", color=0xE74C3C)
            return await ctx.interaction.followup.send(embed=embed_err, ephemeral=True)

        # 🛑 SECURITY LAYER 4: ตรวจสอบระดับยศของบอท
        if member.top_role >= ctx.guild.me.top_role:
            embed_err = discord.Embed(description="❌ **Execution Failure:** Core Mainframe lacks sufficient hierarchical authority over the target's role profile.", color=0xE74C3C)
            return await ctx.interaction.followup.send(embed=embed_err, ephemeral=True)

        # ⏳ ตัวประมวลผลแปลงค่าหน่วยเวลา (รองรับ m, h, d สูงสุด 3 วัน)
        try:
            unit = duration[-1].lower()
            value = int(duration[:-1])
            multipliers = {'m': 60, 'h': 3600, 'd': 86400} # เอาหน่วยวินาที 's' ออกตามสั่ง

            if unit not in multipliers or value <= 0:
                raise ValueError
                
            timeout_seconds = value * multipliers[unit]
        except (ValueError, IndexError):
            embed_err = discord.Embed(
                description="❌ **Invalid Duration Parameter:** Please format lifecycle strings correctly (e.g., `30m`, `3h`, `2d`).",
                color=0xE74C3C
            )
            return await ctx.interaction.followup.send(embed=embed_err, ephemeral=True)

        # 🛑 SECURITY LAYER 5: จำกัดเวลาสูงสุดห้ามเกิน 3 วัน (259,200 วินาที)
        if timeout_seconds > 259200:
            embed_err = discord.Embed(
                description="❌ **Boundary Overflow:** Timeout parameter exceeds the custom threshold matrix of **3 days (3d)**.",
                color=0xE74C3C
            )
            return await ctx.interaction.followup.send(embed=embed_err, ephemeral=True)

        # คำนวณหาวันและเวลาที่จะสิ้นสุดการกักบริเวณ
        until_time = discord.utils.utcnow() + datetime.timedelta(seconds=timeout_seconds)
        end_timestamp = int(until_time.timestamp())

        # 📩 DM NOTIFICATION LOOP
        try:
            dm_embed = discord.Embed(
                title=f"🔇 Communication Silenced: {ctx.guild.name}",
                description="Your data transmission rights have been temporarily suspended.",
                color=0xE74C3C,
                timestamp=dt.now(timezone.utc)
            )
            dm_embed.add_field(name="⏳ Restriction Lift Time", value=f"<t:{end_timestamp}:f> (<t:{end_timestamp}:R>)", inline=False)
            dm_embed.add_field(name="📄 Disciplinary Reason", value=f"> {reason}", inline=False)
            dm_embed.set_footer(text="Automated Restrictions Protocol")
            await member.send(embed=dm_embed)
        except discord.HTTPException:
            pass

        # 🔇 EXECUTION LAYER (สั่ง Timeout และแก้ไขชื่อเล่นเฉพาะเซิร์ฟเวอร์นี้)
        try:
            # 1. จัดการกระบวนการ Timeout ใน Discord API
            await member.timeout(until_time, reason=f"Muted by {ctx.author} | Reason: {reason}")
            
            # 2. จัดการเปลี่ยนชื่อเล่น (เฉพาะในเซิร์ฟเวอร์นี้เท่านั้น)
            # ดึงชื่อปัจจุบันของผู้ใช้มาใช้งาน (ถ้าไม่มีชื่อเล่นให้ใช้ชื่อดิสคอร์ดปกติ)
            current_name = member.display_name
            
            # ตรวจสอบเพื่อไม่ให้เติมคำว่า [Mute] ซ้ำซ้อนหากโดนใบเตือนซ้ำ
            if not current_name.endswith("[Mute]"):
                new_nick = f"{current_name} [Mute]"
                # จำกัดความยาวไม่ให้เกิน 32 ตัวอักษรตามเงื่อนไขของ Discord API
                if len(new_nick) > 32:
                    new_nick = f"{current_name[:25]}... [Mute]"
                
                try:
                    await member.edit(nick=new_nick, reason="System Node Isolation Protocol: Appended [Mute] suffix.")
                except discord.Forbidden:
                    # กรณีบอทไม่มีสิทธิ์เปลี่ยนชื่อคนนั้น (เช่น ยศบอทต่ำกว่า หรือคนนั้นเป็นเจ้าของเซิร์ฟ) ให้ข้ามระบบเปลี่ยนชื่อไป
                    pass

            # 📊 SUCCESS EMBED RESPONSE
            success_embed = discord.Embed(
                title="🔇 Communication Matrix Silenced",
                color=self.embed_color,
                timestamp=dt.now(timezone.utc)
            )
            success_embed.add_field(name="👤 Restricted Node", value=f"{member.mention} (`{member.id}`)", inline=True)
            success_embed.add_field(name="👑 Authorized By", value=f"{ctx.author.mention}", inline=True)
            success_embed.add_field(name="⏳ Active Duration", value=f"`{duration}` (Release <t:{end_timestamp}:R>)", inline=False)
            success_embed.add_field(name="📝 Reason Log Matrix", value=f"```\n{reason}\n```", inline=False)
            
            success_embed.set_thumbnail(url=member.display_avatar.url)
            success_embed.set_footer(text="Sector Data Transmission Locked & Nickname Mutated")

            await ctx.interaction.followup.send(embed=success_embed)

        except discord.HTTPException as e:
            embed_err = discord.Embed(
                description=f"❌ **API Gateway Error:** Failed to execute mute sequence:\n`{str(e)}`",
                color=0xE74C3C
            )
            await ctx.interaction.followup.send(embed=embed_err, ephemeral=True)

    @mute_command.error
    async def mute_command_error(self, ctx: commands.Context, error: commands.CommandError):
        embed = discord.Embed(title="🚨 Clearance Verification Failure", color=0xE74C3C)
        if isinstance(error, commands.MissingPermissions):
            embed.description = "❌ **Access Denied:** You lack `Moderate Members` permission to access the mute protocol."
        elif isinstance(error, commands.BotMissingPermissions):
            embed.description = "❌ **System Fault:** The bot lacks required permissions (`Moderate Members` / `Manage Nicknames`) to enforce this block."
        else:
            embed.description = f"An unexpected error occurred:\n`{str(error)}`"
            
        if ctx.interaction and ctx.interaction.response.is_done():
            await ctx.interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await ctx.send(embed=embed, ephemeral=True)

# 🔌 ฟังก์ชันโหลดโมดูลสำหรับระบบเดินเครื่องบอท
async def setup(bot: commands.Bot):
    await bot.add_cog(Mute(bot))
