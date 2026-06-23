import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
from typing import Optional
import motor.motor_asyncio
import uuid # ใช้สร้าง Unique ID สำหรับประวัติเตือนแต่ละรายการ

ERROR="<:No:1517480787744784475>"

class Warn(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_color = 0x2B2D31
        
        # 📊 MONGODB CONNECTION (ใช้โครงสร้างร่วมกับระบบหลักของคุณ)
        self.mongo_client = motor.motor_asyncio.AsyncIOMotorClient("mongodb+srv://FeroX:Devs@feroxmongo02.ata40kl.mongodb.net/?appName=FeroXMongo02")
        self.db = self.mongo_client["discord_bot_mainframe"]
        self.warn_collection = self.db["warns"]

    # ==========================================
    # ⚠️ COMMAND: WARN PROTOCOL
    # ==========================================
    @commands.hybrid_command(
        name="warn",
        description="⚠️ Issue a formal disciplinary warning and log infraction data to the database."
    )
    @app_commands.describe(
        member="The target user identity to receive the warning infraction.",
        reason="The formal data validation log reason for this disciplinary infraction."
    )
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True) # 🛡️ แอดมินต้องมีสิทธิ์จัดการข้อความขึ้นไป
    async def warn_command(
        self, 
        ctx: commands.Context, 
        member: discord.Member, 
        *, 
        reason: Optional[str] = "No analytical reason specified by authority."
    ):
        """Executes a formal warning infraction against a target node, broadcasting to DM."""
        await ctx.defer()

        # 🛑 SECURITY LAYER 1: ป้องกันการเตือนตัวเอง
        if member.id == ctx.author.id:
            embed_err = discord.Embed(
                description=f"{ERROR} **Termination Aborted:** You cannot execute the warn protocol upon your own node signature.",
                color=0xE74C3C
            )
            return await ctx.interaction.followup.send(embed=embed_err, ephemeral=True)

        # 🛑 SECURITY LAYER 2: ป้องกันการเตือนบอท
        if member.bot:
            embed_err = discord.Embed(
                description=f"{ERROR} **Termination Aborted:** Target node is an artificial automation unit. Action denied.",
                color=0xE74C3C
            )
            return await ctx.interaction.followup.send(embed=embed_err, ephemeral=True)

        # 🛑 SECURITY LAYER 3: ตรวจสอบระดับยศของแอดมิน
        if ctx.author.id != ctx.guild.owner_id and ctx.author.top_role <= member.top_role:
            embed_err = discord.Embed(
                description=f"{ERROR} **Access Denied:** Your authorization clearance rank is equal to or lower than the target node.",
                color=0xE74C3C
            )
            return await ctx.interaction.followup.send(embed=embed_err, ephemeral=True)

        # 📩 DM NOTIFICATION LOOP
        dm_delivered = True
        try:
            dm_embed = discord.Embed(
                title=f"⚠️ Formal Infraction Notice: {ctx.guild.name}",
                description="Your profile signature has received an official disciplinary warning.",
                color=0xE67E22,
                timestamp=datetime.now(timezone.utc)
            )
            dm_embed.add_field(name="📄 Infraction Reason", value=f"> {reason}", inline=False)
            dm_embed.set_footer(text="Please review the network protocols to prevent further lockdown actions.")
            await member.send(embed=dm_embed)
        except discord.HTTPException:
            dm_delivered = False 

        # 💾 DATABASE STORAGE: บันทึกข้อมูลประวัติลง MongoDB
        warn_id = str(uuid.uuid4())[:8] # สร้างไอดีบันทึกความผิดสั้น ๆ 8 หลัก
        warn_data = {
            "_id": warn_id,
            "guild_id": ctx.guild.id,
            "user_id": member.id,
            "moderator_id": ctx.author.id,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc)
        }
        await self.warn_collection.insert_one(warn_data)

        # 📊 FETCH TOTAL WARNS: นับจำนวนครั้งทั้งหมดที่เคยโดนเตือนในเซิร์ฟเวอร์นี้
        total_warns = await self.warn_collection.count_documents({"guild_id": ctx.guild.id, "user_id": member.id})

        # 📺 CONSOLE LOGGING
        print(f"[WARN REGISTERED] Guild: {ctx.guild.name} | Target: {member} | Count: {total_warns} | Reason: {reason}")

        # 📊 SUCCESS EMBED RESPONSE
        success_embed = discord.Embed(
            title="⚠️ Disciplinary Infraction Registered",
            color=self.embed_color,
            timestamp=datetime.now(timezone.utc)
        )
        success_embed.add_field(name="👤 Warned Node", value=f"{member.mention} (`{member.id}`)", inline=True)
        success_embed.add_field(name="👑 Authorized By", value=f"{ctx.author.mention}", inline=True)
        success_embed.add_field(name="📈 Warning Count Matrix", value=f"`{total_warns}` infractions logged", inline=True)
        
        dm_status = "✅ Successfully transmitted to node DM." if dm_delivered else f"{ERROR} Transmit failed (User DM locked)."
        success_embed.add_field(name="📡 DM Gateway Status", value=f"`{dm_status}`", inline=False)
        success_embed.add_field(name="📝 Reason Log Matrix", value=f"```\n{reason}\n```", inline=False)
        
        success_embed.set_thumbnail(url=member.display_avatar.url)
        success_embed.set_footer(text=f"Sector Warning Matrix Logged | Case ID: #{warn_id}")

        # เปลี่ยนเป็นใช้ followup.send เพื่อความเสถียรหลังจากการ Defer
        await ctx.interaction.followup.send(embed=success_embed)

    @warn_command.error
    async def warn_command_error(self, ctx: commands.Context, error: commands.CommandError):
        embed = discord.Embed(title="🚨 Clearance Verification Failure", color=0xE74C3C)
        if isinstance(error, commands.MissingPermissions):
            embed.description = f"{ERROR} **Access Denied:** You lack `Manage Messages` permission to execute the warning protocol."
        else:
            embed.description = f"An unexpected error occurred:\n`{str(error)}`"
            
        if ctx.interaction and ctx.interaction.response.is_done():
            await ctx.interaction.followup.send(embed=embed, ephemeral=True)
        else:
            await ctx.send(embed=embed, ephemeral=True)

# 🔌 ฟังก์ชันโหลดโมดูลสำหรับระบบเดินเครื่องบอท
async def setup(bot: commands.Bot):
    await bot.add_cog(Warn(bot))
