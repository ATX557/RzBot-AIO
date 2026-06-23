import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone
from typing import Optional

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.embed_color = 0x2B2D31

    @commands.hybrid_command(
        name="kick",
        description="🥾 Expel a disruptive member from the server network sector (Admin/Kick Restricted)."
    )
    @app_commands.describe(
        member="The target user identity to kick from the guild matrix.",
        reason="The formal data validation log reason for this disciplinary expulsion."
    )
    @commands.guild_only()
    @commands.has_permissions(kick_members=True) # 🛡️ ตรวจสอบสิทธิ์ผู้ใช้
    @commands.bot_has_permissions(kick_members=True) # 🤖 ตรวจสอบสิทธิ์บอท
    async def kick_command(self, ctx: commands.Context, member: discord.Member, *, reason: Optional[str] = "No analytical reason specified by authority."):
        """Executes the Kick execution protocol against a specific target infrastructure node."""
        
        # ลบ ctx.defer() ออก เพื่อให้ใช้ ctx.send(ephemeral=True) ได้อย่างสมบูรณ์แบบและไม่เกิดข้อผิดพลาด

        # 🛑 SECURITY LAYER 1: ป้องกันการเตะตัวเอง
        if member.id == ctx.author.id:
            embed_err = discord.Embed(
                description="<:No:1517480787744784475> **Termination Aborted:** You cannot execute the kick protocol upon your own node signature.",
                color=0xE74C3C
            )
            return await ctx.send(embed=embed_err, ephemeral=True)

        # 🛑 SECURITY LAYER 2: ป้องกันการเตะเจ้าของเซิร์ฟเวอร์
        if member.id == ctx.guild.owner_id:
            embed_err = discord.Embed(
                description="<:No:1517480787744784475> **Termination Aborted:** Target node holds the ultimate ownership matrix key. Action denied.",
                color=0xE74C3C
            )
            return await ctx.send(embed=embed_err, ephemeral=True)

        # 🛑 SECURITY LAYER 3: ตรวจสอบความลำดับชั้นของยศ (Role Hierarchy) ผู้ใช้
        if ctx.author.id != ctx.guild.owner_id and ctx.author.top_role <= member.top_role:
            embed_err = discord.Embed(
                description="<:No:1517480787744784475> **Access Denied:** Your authorization clearance rank is equal to or lower than the target node.",
                color=0xE74C3C
            )
            return await ctx.send(embed=embed_err, ephemeral=True)

        # 🛑 SECURITY LAYER 4: ตรวจสอบยศบอท
        if member.top_role >= ctx.guild.me.top_role:
            embed_err = discord.Embed(
                description="<:No:1517480787744784475> **Execution Failure:** Core Mainframe lack sufficient hierarchical authority over the target's role profile.",
                color=0xE74C3C
            )
            return await ctx.send(embed=embed_err, ephemeral=True)

        # 📩 DM NOTIFICATION LOOP
        try:
            dm_embed = discord.Embed(
                title=f"🛰️ Network Connection Terminated: {ctx.guild.name}",
                description="You have been officially expelled from the server sector network.",
                color=0xE74C3C,
                timestamp=datetime.now(timezone.utc)
            )
            dm_embed.add_field(name="📄 Disciplinary Reason", value=f"> {reason}", inline=False)
            dm_embed.set_footer(text="Automated Justice Protocol Framework")
            await member.send(embed=dm_embed)
        except discord.HTTPException:
            pass # ถ้าบล็อก DM ให้ข้ามไปขั้นตอนการเตะทันที

        # 🥾 EXECUTION LAYER
        try:
            await member.kick(reason=f"Action requested by {ctx.author} | Reason: {reason}")
            
            # แก้ไขจุด Syntax Error ตรง Reason Log Matrix แล้ว
            success_embed = discord.Embed(
                title="🥾 Disciplinary Expulsion Registered",
                color=self.embed_color,
                timestamp=datetime.now(timezone.utc)
            )
            success_embed.add_field(name="👤 Expelled Node", value=f"{member.mention} (`{member.id}`)", inline=True)
            success_embed.add_field(name="👑 Authorized By", value=f"{ctx.author.mention}", inline=True)
            success_embed.add_field(name="📝 Reason Log Matrix", value=f"```\n{reason}\n```", inline=False)
            success_embed.set_thumbnail(url=member.display_avatar.url)
            success_embed.set_footer(text="Sector Mainframe Security Restored")

            await ctx.send(embed=success_embed)

        except discord.HTTPException as e:
            embed_err = discord.Embed(
                description=f"<:No:1517480787744784475> **API Gateway Error:** Failed to execute expulsion sequence due to Discord anomaly:\n`{str(e)}`",
                color=0xE74C3C
            )
            await ctx.send(embed=embed_err, ephemeral=True)

    # ==========================================
    # 🚨 LOCAL ERROR COG GATEWAY
    # ==========================================
    @kick_command.error
    async def kick_command_error(self, ctx: commands.Context, error: commands.CommandError):
        embed = discord.Embed(title="🚨 Clearance Verification Failure", color=0xE74C3C)
        
        if isinstance(error, commands.MissingPermissions):
            embed.description = "<:No:1517480787744784475> **Access Denied:** You lack the necessary `Kick Members` clearance matrix tokens to execute this security protocol."
        elif isinstance(error, commands.BotMissingPermissions):
            embed.description = "<:No:1517480787744784475> **System Fault:** The bot mainframe lacks the `Kick Members` authorization role inside this cluster grid."
        else:
            embed.description = f"An unexpected processing exception was intercepted:\n`{str(error)}`"
            
        await ctx.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
