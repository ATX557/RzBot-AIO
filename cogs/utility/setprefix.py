import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
import os
from typing import Optional

class SetPrefix(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_color = 0x2B2D31

    # ==========================================
    # ⚙️ COMMAND: SETPREFIX PROTOCOL (MONGO SYNC)
    # ==========================================
    @commands.hybrid_command(
        name="setprefix",
        description="⚙️ Permanently modify the bot's command signature prefix using MongoDB cluster grid."
    )
    @app_commands.describe(
        new_prefix="The new character token or string to act as command trigger (e.g., !, $, rz!). Max 5 chars."
    )
    @commands.guild_only()
    @commands.has_permissions(administrator=True) # 🛡️ สิทธิ์ระดับแอดมินสูงสุด
    async def setprefix_command(self, ctx: commands.Context, new_prefix: str):
        """Reconfigures the command execution prefix and pushes data records to Mongo Cloud."""
        await ctx.defer()

        # 🛑 SECURITY CHECK 1: จำกัดความยาว Prefix ไม่เกิน 5 ตัวอักษร
        if len(new_prefix) > 5:
            embed_err = discord.Embed(
                description="<:No:1517480787744784475> **Validation Fault:** The prefix token length cannot exceed **5 characters** boundary.",
                color=0xE74C3C
            )
            return await ctx.send(embed=embed_err, ephemeral=True)

        # 🛑 SECURITY CHECK 2: ห้ามใช้ช่องว่างเป็น Prefix
        if " " in new_prefix:
            embed_err = discord.Embed(
                description="<:No:1517480787744784475> **Validation Fault:** Command prefixes cannot contain empty space characters.",
                color=0xE74C3C
            )
            return await ctx.send(embed=embed_err, ephemeral=True)

        # 📡 DATABASE CONNECTION LAYER (ดึงคอลเลกชันกิลด์จากมอนโก)
        try:
            # ดึงฐานข้อมูลจากตัวแปรบอทหลัก
            db = self.bot.db
            prefixes_collection = db["guild_prefixes"]

            guild_id = str(ctx.guild.id)
            current_prefix = await self.bot.get_prefix(ctx.message)

            # ทำการ Upsert (ถ้ามีอยู่แล้วให้แก้ไข ถ้ายังไม่มีให้สร้างใหม่) ลงฐานข้อมูล Cloud
            await prefixes_collection.update_one(
                {"guild_id": guild_id},
                {"$set": {
                    "prefix": new_prefix,
                    "updated_at": datetime.now(timezone.utc),
                    "updated_by": str(ctx.author.id)
                }},
                upsert=True
            )

            # ⚙️ SUCCESS EMBED GENERATION
            success_embed = discord.Embed(
                title="⚙️ Save Set Prefix",
                color=self.embed_color,
                timestamp=datetime.now(timezone.utc)
            )
            success_embed.add_field(name="🌐 Server Sector", value=f"{ctx.guild.name}", inline=True)
            success_embed.add_field(name="👑 Reconfigured By", value=f"{ctx.author.mention}", inline=True)
            success_embed.add_field(
                name="📡 Database State Shift", 
                value=f"Old Trigger: `{current_prefix}`\nNew Cluster Trigger: **`{new_prefix}`**", 
                inline=False
            )
            success_embed.add_field(
                name="💡 Operational Example",
                value=f"To call help protocol now, use: `{new_prefix}help`",
                inline=False
            )
            success_embed.set_footer(text="MongoDB Cluster State: Synced & Active")

            await ctx.send(embed=success_embed)

        except Exception as e:
            # 🚨 ดักจับกรณีฐานข้อมูลขัดข้อง
            embed_err = discord.Embed(
                title="🚨 Database Gateway Crash",
                description=f"Failed to synchronize state records with MongoDB Atlas Cluster:\n`{str(e)}`",
                color=0xE74C3C
            )
            await ctx.send(embed=embed_err, ephemeral=True)

    @setprefix_command.error
    async def setprefix_command_error(self, ctx: commands.Context, error: commands.CommandError):
        embed = discord.Embed(title="🚨 Clearance Verification Failure", color=0xE74C3C)
        if isinstance(error, commands.MissingPermissions):
            embed.description = "<:No:1517480787744784475> **Access Denied:** You lack `Administrator` authority key tokens to change mainframe configurations."
        else:
            embed.description = f"An unexpected system exception occurred:\n`{str(error)}`"
        await ctx.send(embed=embed, ephemeral=True)


# ==========================================
# 📡 DYNAMIC PREFIX PROCESSOR (สำหรับนำไปใช้ใน main.py)
# ==========================================
# คุณสามารถก๊อปฟังก์ชันภายนอกนี้ หรือวิธีคิดนี้ไปแปะในไฟล์หลัก (main.py) 
# ตรงจุดที่ตั้งค่าคำสั่งบอท เพื่อให้บอทอ่านค่าจากมอนโกทุกครั้งที่มีคนส่งข้อความ Prefix
async def determine_prefix(bot: commands.Bot, message: discord.Message) -> str:
    """Dynamic prefix loader for text commands routing through MongoDB."""
    if not message.guild:
        return os.getenv("BOT_PREFIX", "?") # คืนค่าเริ่มต้นจาก .env ถ้าพิมพ์ใน DM
        
    try:
        db = bot.db
        data = await db["guild_prefixes"].find_one({"guild_id": str(message.guild.id)})
        if data and "prefix" in data:
            return data["prefix"]
    except Exception:
        pass
        
    return os.getenv("BOT_PREFIX", "?") # คืนค่าเริ่มต้นจาก .env หากเกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล


# 🔌 ฟังก์ชันโหลดโมดูลสำหรับระบบเดินเครื่องบอท
async def setup(bot: commands.Bot):
    await bot.add_cog(SetPrefix(bot))
