import discord
from discord.ext import commands
import aiohttp
import os
import asyncio
from datetime import datetime

class GuildWebhookLogger(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def send_webhook_log(self, webhook_env_name: str, embed: discord.Embed):
        """Manages and dispatches telemetry data via Discord Webhook URLs from .env configuration."""
        webhook_url = os.getenv(webhook_env_name)
        if not webhook_url:
            print(f"⚠️ [Webhook Error] Missing configuration parameter `{webhook_env_name}` in your .env file.")
            return

        # Attempt to reuse the bot's global aiohttp session to save network resources
        session = getattr(self.bot, "session", None) or getattr(self.bot.http, "_HTTPClient__session", None)
        
        if session and not session.closed:
            try:
                webhook = discord.Webhook.from_url(webhook_url, session=session)
                await webhook.send(
                    embed=embed,
                    username=f"{self.bot.user.name if self.bot.user else 'System'} Network Log",
                    avatar_url=self.bot.user.display_avatar.url if self.bot.user else None
                )
            except Exception as e:
                print(f"❌ [Webhook Dispatch Failed] Failed via shared session cluster: {str(e)}")
        else:
            # Fallback to isolated context session if global session container is unavailable
            async with aiohttp.ClientSession() as backup_session:
                try:
                    webhook = discord.Webhook.from_url(webhook_url, session=backup_session)
                    await webhook.send(
                        embed=embed,
                        username=f"{self.bot.user.name if self.bot.user else 'System'} Network Log",
                        avatar_url=self.bot.user.display_avatar.url if self.bot.user else None
                    )
                except Exception as e:
                    print(f"❌ [Webhook Dispatch Failed] Failed via isolated fallback tunnel: {str(e)}")

    # =======================================================
    # 🟩 EVENT: BOT JOINED A SERVER
    # =======================================================
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        # Calculate current global bot network footprints
        total_servers = len(self.bot.guilds)
        total_members = sum(g.member_count for g in self.bot.guilds if g.member_count)

        # Scan or generate instant invite link dynamically (Audit network permissions)
        invite_url = "❌ NO_INVITE_PRIVILEGES"
        bot_member = guild.me or guild.get_member(self.bot.user.id) if self.bot.user else None

        if bot_member and bot_member.guild_permissions.create_instant_invite:
            try:
                target_channel = next((c for c in guild.text_channels if c.permissions_for(bot_member).create_instant_invite), None)
                if target_channel:
                    invite = await target_channel.create_invite(max_age=0, max_uses=0, reason="RzBot Network Indexing")
                    invite_url = f"[Click to Access Cluster]({invite.url})"
            except Exception:
                invite_url = "⚠️ GATEWAY_LINK_GENERATION_FAILED"

        created_timestamp = int(guild.created_at.timestamp()) if guild.created_at else 0

        # Build Core Node registration summary embed
        join_embed = discord.Embed(
            title="🛰️ New Server Cluster Indexed",
            description="The bot has successfully connected and integrated into a new guild sector coordinate.",
            color=0x2ECC71, 
            timestamp=discord.utils.utcnow()
        )
        if guild.icon:
            join_embed.set_thumbnail(url=guild.icon.url)

        owner_mention = guild.owner.mention if guild.owner else "`UNKNOWN`"
        join_embed.add_field(
            name="🌐 SERVER IDENTIFICATION",
            value=(
                f"• **Server Name:** `{guild.name}`\n"
                f"• **Network ID:** `{guild.id}`\n"
                f"• **Owner Node:** {owner_mention} (ID: `{guild.owner_id}`)\n"
                f"• **Sector Created:** <t:{created_timestamp}:R>"
            ),
            inline=False
        )

        join_embed.add_field(
            name="📊 CAPACITOR POPULATION",
            value=(
                f"• **Current Members:** `{guild.member_count or 0:,} accounts`\n"
                f"• **Verification Firewall:** `{str(guild.verification_level).upper()}`"
            ),
            inline=True
        )

        join_embed.add_field(
            name="🔗 NETWORK ENTRY LINK",
            value=f"• Gateway: {invite_url}",
            inline=True
        )

        join_embed.add_field(
            name="📈 GLOBAL FOOTPRINT METRICS (TOTAL)",
            value=(
                f"```ini\n"
                f"[Global Servers] = {total_servers:,} Nodes\n"
                f"[Global Users]   = {total_members:,} Accounts\n"
                f"```"
            ),
            inline=False
        )
        join_embed.set_footer(text="Network Growth Alert • Processed via Webhook Gateway")

        await self.send_webhook_log("WEBHOOK_GUILD_JOIN", join_embed)

    # =======================================================
    # 🟥 EVENT: BOT LEFT / KICKED / BANNED FROM SERVER
    # =======================================================
    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        # Recalculate remaining network footprints after connection cutoff
        total_servers = len(self.bot.guilds)
        total_members = sum(g.member_count for g in self.bot.guilds if g.member_count)

        exit_method = "UNKNOWN_DISCONNECT (Self-leave or manual server extraction)"
        responsible_moderator = "SYSTEM / USER_SELF"
        reason_log = "No specific reason provided in transmission."

        # Fetch audit log entries with a robust conditional timeout strategy
        bot_user_id = self.bot.user.id if self.bot.user else None
        
        # Check permissions safely using fallback context logic
        has_audit_perm = False
        if guild.me:
            has_audit_perm = guild.me.guild_permissions.view_audit_log
        
        if has_audit_perm and bot_user_id:
            try:
                # Limit the search duration to avoid thread stalling
                async for entry in guild.audit_logs(limit=10, oldest_first=False):
                    if entry.target and entry.target.id == bot_user_id:
                        if entry.action == discord.AuditLogAction.kick:
                            exit_method = "❌ KICKED (Removed by server administration)"
                            responsible_moderator = f"{entry.user.mention if entry.user else 'Operator'} (`{entry.user.id if entry.user else '0'}`)"
                            reason_log = entry.reason or "No specific reason specified."
                            break
                        elif entry.action == discord.AuditLogAction.ban:
                            exit_method = "🚫 BANNED (Permanently restricted from server)"
                            responsible_moderator = f"{entry.user.mention if entry.user else 'Operator'} (`{entry.user.id if entry.user else '0'}`)"
                            reason_log = entry.reason or "No specific reason specified."
                            break
            except Exception as e:
                exit_method = f"⚠️ AUDIT_LOG_FETCH_ERROR (`{type(e).__name__}`)"
        elif not has_audit_perm:
            exit_method = "⚠️ UNVERIFIED_DISCONNECT (Missing View Audit Log permission to verify source)"

        # Build server cluster loss diagnostic embed
        leave_embed = discord.Embed(
            title="⚠️ Server Cluster Severed / Lost",
            description="The bot connection has been severed or deleted from the target guild sector.",
            color=0xFF5555, 
            timestamp=discord.utils.utcnow()
        )
        if guild.icon:
            leave_embed.set_thumbnail(url=guild.icon.url)

        owner_mention = guild.owner.mention if guild.owner else "`UNKNOWN`"
        leave_embed.add_field(
            name="🌐 SEVERED SECTOR PROFILE",
            value=(
                f"• **Server Name:** `{guild.name}`\n"
                f"• **Network ID:** `{guild.id}`\n"
                f"• **Server Owner:** {owner_mention} (ID: `{guild.owner_id}`)\n"
                f"• **Lost Capacity:** `{guild.member_count or 0:,} users`"
            ),
            inline=False
        )

        leave_embed.add_field(
            name="🛡️ DISCONNECT DIAGNOSTICS",
            value=(
                f"• **Execution Method:** `{exit_method}`\n"
                f"• **Operator:** {responsible_moderator}\n"
                f"• **Reason Protocol:** `{reason_log}`"
            ),
            inline=False
        )

        leave_embed.add_field(
            name="📉 DEGRADED FOOTPRINT METRICS (REMAINING)",
            value=(
                f"```ini\n"
                f"[Remaining Servers] = {total_servers:,} Nodes\n"
                f"[Remaining Users]   = {total_members:,} Accounts\n"
                f"```"
            ),
            inline=False
        )
        leave_embed.set_footer(text="Network Shrinkage Detected • Processed via Webhook Gateway")

        await self.send_webhook_log("WEBHOOK_GUILD_LEAVE", leave_embed)

# Initialize and load the cog module into the main bot core
async def setup(bot: commands.Bot):
    await bot.add_cog(GuildWebhookLogger(bot))
