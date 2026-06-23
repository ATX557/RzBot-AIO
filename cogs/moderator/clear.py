import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
from typing import Optional

class Clear(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_color = 0x2B2D31

    # ==========================================
    # 🧹 COMMAND: ADVANCED PURGE/CLEAR PROTOCOL
    # ==========================================
    @commands.hybrid_command(
        name="clear",
        description="🧹 Purge messages dynamically based on filters (All, Users, or Bots)."
    )
    @app_commands.describe(
        amount="The total number of messages to scan. Max: 200 (Leave blank to purge all up to 200).",
        target_type="Select filtration mode: 'all' (Police Purge), 'user' (Human nodes), or 'bot' (AI nodes).",
        user="Optional target user profile. (Only applicable if target_type is set to 'user')."
    )
    @app_commands.choices(target_type=[
        app_commands.Choice(name="🚨 All Messages (Police Purge)", value="all"),
        app_commands.Choice(name="👤 Human Users Only", value="user"),
        app_commands.Choice(name="🤖 All Bot Automations", value="bot")
    ])
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True) # 🛡️ แอดมินต้องมีสิทธิ์จัดการข้อความ
    @commands.bot_has_permissions(manage_messages=True) # 🤖 บอทต้องมีสิทธิ์จัดการข้อความด้วย
    async def clear_command(
        self, 
        ctx: commands.Context, 
        amount: Optional[int] = None, # เปลี่ยนเป็น Optional และ Default เป็น None เพื่อไม่บังคับใส่
        target_type: str = "all", 
        user: Optional[discord.Member] = None
    ):
        """Scans the designated text channel registry and purges data matching filters."""
        await ctx.defer(ephemeral=True)

        # ⚙️ หากผู้ใช้ไม่ได้ระบุจำนวน (None) บอทจะตั้งค่าเริ่มต้นให้ลบสูงสุด 200 ข้อความทันที
        if amount is None:
            amount = 200

        # 🛑 จำกัดขอบเขตความปลอดภัย (อัปเกรดสูงสุดเป็น 200 ข้อความ)
        if amount <= 0 or amount > 200:
            embed_err = discord.Embed(
                description="<:No:1517480787744784475> **Boundary Error:** Please specify a purge quantum amount between **1 and 200** messages.",
                color=0xE74C3C
            )
            return await ctx.interaction.followup.send(embed=embed_err, ephemeral=True)

        # ⚙️ ตัวประมวลผลคัดกรองข้อความ (Filtration Logic Engine)
        def purge_filter(msg: discord.Message) -> bool:
            if target_type == "bot":
                return msg.author.bot
            elif target_type == "user":
                if user:
                    return msg.author.id == user.id
                else:
                    return not msg.author.bot
            # โหมด 'all' ลบทุกข้อความ
            return True

        # 🧹 EXECUTION LAYER (สั่งการลบข้อความล้างข้อมูล)
        try:
            # เพิ่ม +1 ในระบบหลังบ้านเพื่อชดเชยกรณีเรียกผ่าน Prefix Command
            search_amount = amount if ctx.interaction else amount + 1
            
            deleted = await ctx.channel.purge(limit=search_amount, check=purge_filter)
            
            # หักลบข้อความคำสั่งออกจากการรายงานผล (กรณีเป็น Prefix Command)
            actual_deleted = len(deleted)
            if not ctx.interaction and actual_deleted > 0:
                actual_deleted = max(0, actual_deleted - 1)

            # จัดเรียงข้อความสรุปผลการกวาดล้าง
            success_embed = discord.Embed(
                title="🧹 Data Purge Sequence Concluded",
                color=self.embed_color,
                timestamp=datetime.now(timezone.utc)
            )
            
            # แปรเปลี่ยนคำอธิบายตามโหมดที่เลือกใช้งาน
            if target_type == "all":
                mode_str = "🚨 Total Grid Purge (Police Wipe)"
            elif target_type == "bot":
                mode_str = "🤖 All Bot Nodes Purged"
            else:
                mode_str = f"👤 Target User: {user.mention}" if user else "👤 All Human Nodes Purged"

            success_embed.add_field(name="📊 Operation Mode", value=mode_str, inline=True)
            success_embed.add_field(name="🗑️ Purged Records", value=f"`{actual_deleted}` messages removed", inline=True)
            success_embed.set_footer(text="Channel Log Integrity Cleared")

            # ส่งการแจ้งเตือนกลับหลัง Defer ต้องใช้ interaction.followup
            await ctx.interaction.followup.send(embed=success_embed, ephemeral=True)

        except discord.HTTPException as e:
            embed_err = discord.Embed(
                description=f"<:No:1517480787744784475> **API Gateway Error:** Failed to execute purge sequence due to Discord restrictions:\n`{str(e)}`",
                color=0xE74C3C
            )
            await ctx.interaction.followup.send(embed=embed_err, ephemeral=True)

    @clear_command.error
    async def clear_command_error(self, ctx: commands.Context, error: commands.CommandError):
        embed = discord.Embed(title="🚨 Clearance Verification Failure", color=0xE74C3C)
        if isinstance(error, commands.MissingPermissions):
            embed.description = "<:No:1517480787744784475> **Access Denied:** You lack `Manage Messages` permission to trigger the clear protocol."
        elif isinstance(error, commands.BotMissingPermissions):
            embed.description = "<:No:1517480787744784475> **System Fault:** The bot lacks `Manage Messages` matrix rights to delete logs."
        else:
            embed.description = f"An unexpected error occurred:\n`{str(error)}`"
            
        if ctx.interaction and ctx.interaction.response.is_done():
            await ctx.interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await ctx.send(embed=embed, ephemeral=True)

# 🔌 ฟังก์ชันโหลดโมดูลสำหรับระบบเดินเครื่องบอท
async def setup(bot: commands.Bot):
    await bot.add_cog(Clear(bot))
