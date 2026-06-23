import discord
from discord.ext import commands
from discord import app_commands
import datetime

# --- HOW TO REGISTER THIS IN YOUR MAIN COG SYSTEM ---
# This utilizes discord.ext.commands.Cog and commands.hybrid_command
# Ensure your bot variable is configured with both intents.message_content and intents.guilds enabled.

class InviteUtility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="inviteinfo",
        aliases=["ii", "inv"], 
        description="Fetch, analyze, and decode metadata from any provided Discord server invite link."
    )
    @app_commands.describe(link="The complete Discord invite link or code to investigate (e.g., https://discord.gg/xyz)")
    @commands.guild_only()
    async def inviteinfo(self, ctx: commands.Context, link: str):
        """
        Hybrid Execution Pipeline:
        Supports Prefix triggers (e.g., !inviteinfo, !ii, !inv) 
        and Slash Interactions (/inviteinfo) transparently.
        """
        # Acknowledge immediately to prevent gateway timeout across both Slash and Prefix pipelines
        await ctx.defer()

        # Extract clean raw code from the input string if the user entered a full URL path
        invite_code = link.split('/')[-1].strip()

        try:
            # Fetch data packages directly from the Discord Core Gateway Infrastructure
            invite = await self.bot.fetch_invite(invite_code, with_counts=True)
            
            guild = invite.guild
            if not guild:
                raise Exception("The targeted invite link points to an isolated node or group chat.")

            # Extrapolate server structural metadata parameters
            server_name = guild.name
            server_id = guild.id
            active_presence = invite.approximate_presence_count or 0
            total_registry = invite.approximate_member_count or 0
            
            # Calculate cluster configuration parameters
            ver_level = str(guild.verification_level).upper()
            
            # แปลงรายการ Features ของเซิร์ฟเวอร์ให้ออกมาเป็นข้อความที่สอดคล้องและสวยงาม
            features_list = [str(f).replace("_", " ").upper() for f in guild.features[:4]]
            feature_nodes = "\n".join([f"- {f}" for f in features_list]) if features_list else "- STANDARD INSTANCE FLAGS"
            
            # Compile channel analytics segment
            channel_name = invite.channel.name if invite.channel else "UNKNOWN GATEWAY"
            channel_type = str(invite.channel.type).upper() if invite.channel else "GENERIC"

            # ดึงข้อมูลผู้สร้างลิงก์ (Inviter Node Tracking) เพื่อความแม่นยำในการระบุสิทธิ์ที่มาของช่องทาง
            if invite.inviter:
                inviter_display = f"• **Creator:** {invite.inviter.mention} (`{invite.inviter.id}`)"
            else:
                inviter_display = "• **Creator:** `[SYSTEM AUTOMATED / PARTNER ARCHIVE]`"

            # Construct high-tier neon matrix architecture dashboard embed
            info_embed = discord.Embed(
                title="🛰️ Discord Link Infrastructure Decoded",
                description=f"Successfully extracted core metadata matrices from target sector: `{invite_code}`",
                color=0x00f2ff # Signature Matrix Neon Blue
            )

            # 1. SERVER CORE METADATA NODE
            info_embed.add_field(
                name="🌐 TARGET SERVER LOGISTICS",
                value=(
                    f"• **Identity Name:** `{server_name}`\n"
                    f"• **Network ID:** `{server_id}`\n"
                    f"• **Verification:** `LEVEL {ver_level}`"
                ),
                inline=False
            )

            # 2. REALTIME POPULATION MATRIX (LIVE COUNTS)
            info_embed.add_field(
                name="📊 TELEMETRY POPULATION DISPATCH",
                value=(
                    f"```ini\n"
                    f"[Online Presence] = {active_presence:,} users\n"
                    f"[Total Registry]  = {total_registry:,} members\n"
                    f"```"
                ),
                inline=False
            )

            # 3. INTERFACE LINK GATEWAY LOCATION & INVITER
            # ย้ายข้อมูลมาจัดบรรทัดแบ่งฝั่งและใส่ข้อมูลผู้สร้างลิงก์ลงในหน้านี้ให้ถูกต้องตามหมวดหมู่
            info_embed.add_field(
                name="🚪 GATEWAY ENTRY & CREATOR",
                value=(
                    f"• **Target Channel:** `#{channel_name}`\n"
                    f"• **Structure Type:** `{channel_type}`\n"
                    f"{inviter_display}"
                ),
                inline=False
            )

            # 4. SYSTEM FEATURES TIER LIST
            # จัดรูปแบบข้อความฟีเจอร์เด่นด้วยกล่องข้อความโครงสร้างพิเศษให้อ่านแยกบรรทัดชัดเจน
            info_embed.add_field(
                name="⚙️ INSTANCE ARCHITECTURE FLAGS",
                value=f"```json\n{feature_nodes}\n```",
                inline=False
            )

            # Sync corporate metadata assets
            if guild.icon:
                info_embed.set_thumbnail(url=guild.icon.url)
                
            info_embed.set_footer(
                text=f"Analyzed via Hybrid Matrix Engine • Powered by RzBot",
                icon_url=self.bot.user.display_avatar.url
            )

            # Send back to the originating execution channel context
            await ctx.send(embed=info_embed)

        except discord.NotFound:
            error_embed = discord.Embed(
                title="⚠️ Diagnostic Link Failure",
                description=f"The specified code `{invite_code}` was not found in the global Discord directory.\nIt may be expired, revoked, or corrupted.",
                color=0xff5555
            )
            error_embed.set_footer(text="Matrix Error Handling Layer • Network Boundary Error")
            await ctx.send(embed=error_embed)

        except Exception as e:
            fail_embed = discord.Embed(
                title="⚠️ Internal Pipeline Interruption",
                description=f"An unhandled execution error disrupted the look-up script.\n\n**Error Telemetry:**\n`{str(e)}`",
                color=0xff5555
            )
            fail_embed.set_footer(text="Matrix Error Handling Layer • Runtime Exception")
            await ctx.send(embed=fail_embed)

# Setup function to seamlessly register this cog class bundle
async def setup(bot):
    await bot.add_cog(InviteUtility(bot))
