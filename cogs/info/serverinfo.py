import discord
from discord import app_commands
from discord.ext import commands

# =======================================================
# 🎛️ SERVER INFO INTERACTIVE UI COMPONENTS
# =======================================================
class ServerInfoSelect(discord.ui.Select):
    """Dropdown select menu for switching between server info telemetry pages."""
    def __init__(self, embeds: list):
        options = [
            discord.SelectOption(
                label="Core & Populations",
                value="0",
                description="Show server ownership, human metrics, and presence uptime.",
                emoji="📡",
                default=True
            ),
            discord.SelectOption(
                label="Channel Infrastructure",
                value="1",
                description="Audit channel layouts, categories, and operational matrices.",
                emoji="🔗"
            ),
            discord.SelectOption(
                label="Boost & Asset Grid",
                value="2",
                description="Review Nitro engine tier data, stickers, and custom branding banners.",
                emoji="⚡"
            ),
            discord.SelectOption(
                label="Security Profile",
                value="3",
                description="Scan system firewalls, verification levels, and filter states.",
                emoji="🔒"
            ),
            discord.SelectOption(
                label="Platform Privileges",
                value="4",
                description="Review Discord allowed features and raw backend flags.",
                emoji="⚙️"
            )
        ]
        super().__init__(placeholder="📡 Choose a telemetry node to explore...", min_values=1, max_values=1, options=options)
        self.embeds = embeds

    async def callback(self, interaction: discord.Interaction):
        page_index = int(self.values[0])
        
        # Sync the default selected options visual state
        for option in self.options:
            option.default = (option.value == self.values[0])
            
        await interaction.response.edit_message(embed=self.embeds[page_index], view=self.view)


class ServerInfoPaginator(discord.ui.View):
    """View container to anchor and manage the dropdown menu session."""
    def __init__(self, ctx: commands.Context, embeds: list):
        super().__init__(timeout=120.0)
        self.ctx = ctx
        self.embeds = embeds
        self.add_item(ServerInfoSelect(self.embeds))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("❌ **Access Denied:** You do not own this interaction sequence.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for child in self.children:
            if isinstance(child, discord.ui.Select):
                child.disabled = True
        try:
            if hasattr(self, 'message') and self.message:
                await self.message.edit(view=self)
        except Exception:
            pass


# =======================================================
# 🌐 MAIN SERVER INFO TELEMETRY COG SYSTEM
# =======================================================
class UtilityServerInfo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="serverinfo",
        aliases=["si", "server-info"],
        description="Fetch comprehensive telemetry grid metrics for this server node."
    )
    @commands.guild_only()
    async def server_info(self, ctx: commands.Context):
        await ctx.defer(ephemeral=False)
        
        guild = ctx.guild
        if not guild:
            await ctx.send("❌ This command must be executed within a valid server node cluster.", ephemeral=True)
            return

        # --- DATA PROCESSING MATRIX ---
        created_at_timestamp = int(guild.created_at.timestamp()) if guild.created_at else None

        # Advanced Population Breakdowns (Humans vs Bots)
        total_members = guild.member_count or len(guild.members)
        bot_count = len([m for m in guild.members if m.bot])
        human_count = total_members - bot_count
        
        human_percent = (human_count / total_members * 100) if total_members > 0 else 0
        bot_percent = (bot_count / total_members * 100) if total_members > 0 else 0

        # Presence / Status Telemetry Breakdown
        online = len([m for m in guild.members if m.status == discord.Status.online])
        idle = len([m for m in guild.members if m.status == discord.Status.idle])
        dnd = len([m for m in guild.members if m.status == discord.Status.dnd])
        offline = total_members - (online + idle + dnd)

        # Deep Channel Auditing
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        stage_channels = len(guild.stage_channels)
        forum_channels = len([c for c in guild.channels if isinstance(c, discord.ForumChannel)])
        category_channels = len(guild.categories)
        total_threads = len(guild.threads)
        total_channels = len(guild.channels)

        # Asset Statistics
        total_emojis = len(guild.emojis)
        static_emojis = len([e for e in guild.emojis if not e.animated])
        animated_emojis = len([e for e in guild.emojis if e.animated])
        total_stickers = len(guild.stickers)
        total_roles = len(guild.roles)

        # System Security Setup
        verification_tier = getattr(guild, 'verification_level', 'UNKNOWN')
        content_filter = getattr(guild, 'explicit_content_filter', 'UNKNOWN')
        mfa_level = "ENABLED (2FA REQUIRED)" if guild.mfa_level == 1 else "DISABLED"
        nsfw_level = str(guild.nsfw_level).upper()
        notification_setting = "ALL MESSAGES" if guild.default_notifications == discord.NotificationLevel.all_messages else "ONLY MENTIONS"

        # Premium / Vanity Telemetry
        vanity_url = f"[{guild.vanity_url_code}](https://discord.gg/{guild.vanity_url_code})" if guild.vanity_url_code else "`NONE`"

        # Map Discord features array with clear status indicators
        feature_checklists = {
            "COMMUNITY": "COMMUNITY_DESIGNATION",
            "VANITY_URL": "VANITY_URL_GATEWAY",
            "INVITE_SPLASH": "CUSTOM_INVITE_SPLASH",
            "BANNER": "GUILD_BANNER_MATRIX",
            "VIP_REGIONS": "VIP_VOICE_REGIONS",
            "VERIFIED": "OFFICIAL_VERIFIED_BADGE",
            "PARTNERED": "DISCORD_PARTNER_STATUS",
            "DISCOVERABLE": "SERVER_DISCOVERY_INDEX",
            "NEWS": "ANNOUNCEMENT_CHANNELS",
            "ROLE_ICONS": "CUSTOM_ROLE_ICONS",
            "ANIMATED_ICON": "ANIMATED_GUILD_ICON",
            "MEMBER_VERIFICATION_GATE_ENABLED": "RULE_SCREENING_GATE",
            "MONETIZATION_ENABLED": "CREATOR_MONETIZATION",
            "TICKETED_EVENTS_ENABLED": "STAGE_TICKETED_EVENTS"
        }

        active_features, inactive_features = [], []
        for key, display_name in feature_checklists.items():
            if key in guild.features:
                active_features.append(f"🟩 `{display_name}`")
            else:
                inactive_features.append(f"🟥 `{display_name}`")

        # ==========================================
        # --- EMBED 1: CORE & ADVANCED POPULATION ---
        # ==========================================
        embed1 = discord.Embed(
            title=f"📡 Server Telemetry Core • {guild.name}",
            description=f"Extracting fundamental identity blocks for Server ID: `{guild.id}`",
            color=0x2B2D31,
            timestamp=discord.utils.utcnow()
        )
        if guild.icon: embed1.set_thumbnail(url=guild.icon.url)

        embed1.add_field(
            name="👑 Administration Core",
            value=(
                f"> **Server Owner:** {guild.owner.mention if guild.owner else '`UNKNOWN`'}\n"
                f"> **Owner ID:** `{guild.owner_id}`\n"
                f"> **Creation Vector:** " + (f"<t:{created_at_timestamp}:F> (<t:{created_at_timestamp}:R>)" if created_at_timestamp else "`N/A`")
            ),
            inline=False
        )

        embed1.add_field(
            name="👥 Population Matrix",
            value=(
                f"> **Total Accounts:** `{total_members:,}`\n"
                f"> **Humans Array:** `{human_count:,}` ({human_percent:.1f}%)\n"
                f"> **Automated Bots:** `{bot_count:,}` ({bot_percent:.1f}%)"
            ),
            inline=True
        )

        embed1.add_field(
            name="🟢 Realtime Presence Relays",
            value=(
                f"> **Online:** `{online:,}` | **Idle:** `{idle:,}`\n"
                f"> **Do Not Disturb:** `{dnd:,}`\n"
                f"> **Offline Node Array:** `{offline:,}`"
            ),
            inline=True
        )
        embed1.set_footer(text=f"Page 1/5 • Powered by RzBot", icon_url=ctx.author.display_avatar.url)

        # ==========================================
        # --- EMBED 2: INFRASTRUCTURE NODES ---
        # ==========================================
        embed2 = discord.Embed(
            title=f"🔗 Channel Infrastructure Node Layout • {guild.name}",
            description="Diagnostic grid auditing of all active channel layout segments.",
            color=0x2B2D31,
            timestamp=discord.utils.utcnow()
        )
        if guild.icon: embed2.set_thumbnail(url=guild.icon.url)

        embed2.add_field(
            name="📂 Channel Grid Ecosystem",
            value=(
                f"> **Total Layout Grid:** `{total_channels} nodes`\n"
                f"> ├ Text Channels: `{text_channels}`\n"
                f"> ├ Voice Rooms: `{voice_channels}`\n"
                f"> ├ Stage Nodes: `{stage_channels}`\n"
                f"> ├ Forums Matrix: `{forum_channels}`\n"
                f"> ├ Active Threads: `{total_threads}`\n"
                f"> └ Parent Categories: `{category_channels}`"
            ),
            inline=False
        )
        embed2.set_footer(text=f"Page 2/5 • Powered by RzBot", icon_url=ctx.author.display_avatar.url)

        # ==========================================
        # --- EMBED 3: NITRO BOOST & ASSET ENGINE ---
        # ==========================================
        embed3 = discord.Embed(
            title=f"⚡ Boost Status & Asset Grid • {guild.name}",
            description="Tracking subscription metrics, customized graphical framing assets, and standard items.",
            color=0x2B2D31,
            timestamp=discord.utils.utcnow()
        )
        if guild.icon: embed3.set_thumbnail(url=guild.icon.url)
        if guild.banner: embed3.set_image(url=guild.banner.url)

        embed3.add_field(
            name="🚀 Nitro Engine Metrics",
            value=(
                f"> **Subscription Tier:** `Level {guild.premium_tier}`\n"
                f"> **Active Power Boosts:** `{guild.premium_subscription_count} Boosts`\n"
                f"> **Custom Roles System:** `{total_roles} Configurations`"
            ),
            inline=True
        )

        embed3.add_field(
            name="🎨 Custom Asset Arrays",
            value=(
                f"> **Emoji Matrix:** `{total_emojis} Variations`\n"
                f"> ├ Static Assets: `{static_emojis}`\n"
                f"> └ Animated Assets: `{animated_emojis}`\n"
                f"> **Sticker Artifacts:** `{total_stickers} Active`"
            ),
            inline=True
        )

        banner_url = f"[Download Banner Vector]({guild.banner.url})" if guild.banner else "`NOT_CONFIGURED`"
        splash_url = f"[Download Splash Vector]({guild.splash.url})" if guild.splash else "`NOT_CONFIGURED`"
        
        embed3.add_field(
            name="🖼️ Display Graphic Matrix Vectors",
            value=f"> **Guild Banner Frame:** {banner_url}\n> **Invite Splash Frame:** {splash_url}",
            inline=False
        )
        embed3.set_footer(text=f"Page 3/5 • Powered by RzBot", icon_url=ctx.author.display_avatar.url)

        # ==========================================
        # --- EMBED 4: SECURITY FIREWALLS ---
        # ==========================================
        embed4 = discord.Embed(
            title=f"🔒 Security Matrix & Firewalls • {guild.name}",
            description="Deep scan diagnostics of automated system protection shields and gateway settings.",
            color=0x2B2D31,
            timestamp=discord.utils.utcnow()
        )
        if guild.icon: embed4.set_thumbnail(url=guild.icon.url)

        embed4.add_field(
            name="🛡️ System Protection Configuration",
            value=(
                f"> **Verification Firewall:** `{str(verification_tier).upper()}`\n"
                f"> **Explicit Content Filter:** `{str(content_filter).upper()}`\n"
                f"> **Elevated Admin MFA State:** `{mfa_level}`"
            ),
            inline=False
        )

        embed4.add_field(
            name="⚙️ Gateway Routing Settings",
            value=(
                f"> **NSFW Gate Rating:** `{nsfw_level}`\n"
                f"> **Default Notification:** `{notification_setting}`\n"
                f"> **Vanity URL Gateway:** {vanity_url}"
            ),
            inline=False
        )
        embed4.set_footer(text=f"Page 4/5 • Powered by RzBot", icon_url=ctx.author.display_avatar.url)

        # ==========================================
        # --- EMBED 5: PLATFORM PRIVILEGES ---
        # ==========================================
        embed5 = discord.Embed(
            title=f"⚙️ Discord Platform Privileges • {guild.name}",
            description="Audit configuration of features and privileges allowed by Discord deployment grid.",
            color=0x2B2D31,
            timestamp=discord.utils.utcnow()
        )
        if guild.icon: embed5.set_thumbnail(url=guild.icon.url)

        active_str = "\n".join(active_features[:7]) if active_features else "• `NO_SPECIAL_PRIVILEGES`"
        inactive_str = "\n".join(inactive_features[:7]) if inactive_features else "• `FULL_SYSTEM_UNLOCKED`"

        if len(active_features) > 7: active_str += f"\n> *And {len(active_features) - 7} more...*"
        if len(inactive_features) > 7: inactive_str += f"\n> *And {len(inactive_features) - 7} more...*"

        embed5.add_field(name="🟩 Unlocked Engine Features", value=active_str, inline=True)
        embed5.add_field(name="🟥 Locked Matrix Nodes", value=inactive_str, inline=True)

        all_raw_features = ", ".join([f"`{f}`" for f in guild.features]) if guild.features else "`STANDARD_GRID`"
        
        # จัดพารามิเตอร์ข้อความ Raw Flag ไม่ให้แถวยาวทะลุกล่อง
        if len(all_raw_features) > 900:
            all_raw_features = all_raw_features[:897] + "..."
            
        embed5.add_field(
            name="📦 Raw Platform Flag Array",
            value=all_raw_features,
            inline=False
        )
        embed5.set_footer(text=f"Page 5/5 • Powered by RzBot", icon_url=ctx.author.display_avatar.url)

        # --- RENDERING EXPEDITION ---
        embeds = [embed1, embed2, embed3, embed4, embed5]
        view = ServerInfoPaginator(ctx, embeds)
        view.message = await ctx.send(embed=embeds[0], view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(UtilityServerInfo(bot))