import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

# =======================================================
# 🎛️ USER INFO INTERACTIVE UI COMPONENTS
# =======================================================
class UserInfoSelect(discord.ui.Select):
    """Dropdown select menu for switching between user telemetry pages."""
    def __init__(self, embeds: list):
        options = [
            discord.SelectOption(
                label="Identity Core",
                value="0",
                description="Show basic user identity, account age, and server join vector.",
                emoji="👤",
                default=True
            ),
            discord.SelectOption(
                label="Roles & Permissions",
                value="1",
                description="Audit custom server roles and administrative key privileges.",
                emoji="🎭"
            ),
            discord.SelectOption(
                label="Display Graphic Matrix",
                value="2",
                description="Extract profile vector assets, global avatars, and server banners.",
                emoji="🖼️"
            ),
            discord.SelectOption(
                label="Status & Client Relays",
                value="3",
                description="Check realtime presence status, active client devices, and activities.",
                emoji="🟢"
            ),
            discord.SelectOption(
                label="Security & Profiling",
                value="4",
                description="Review account security signals and server premium boosting state.",
                emoji="🛡️"
            )
        ]
        super().__init__(placeholder="👤 Choose a telemetry node to explore...", min_values=1, max_values=1, options=options)
        self.embeds = embeds

    async def callback(self, interaction: discord.Interaction):
        page_index = int(self.values[0])
        
        # Sync the default selected options visual state
        for option in self.options:
            option.default = (option.value == self.values[0])
            
        await interaction.response.edit_message(embed=self.embeds[page_index], view=self.view)


class UserInfoPaginator(discord.ui.View):
    """View container to anchor and manage the dropdown menu session."""
    def __init__(self, ctx: commands.Context, embeds: list):
        super().__init__(timeout=120.0)
        self.ctx = ctx
        self.embeds = embeds
        self.add_item(UserInfoSelect(self.embeds))

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
# 🌐 MAIN USER INFO TELEMETRY COG SYSTEM
# =======================================================
class UtilityUserInfo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="userinfo",
        aliases=["ui", "user-info"],
        description="Fetch comprehensive telemetry grid metrics for a user account profile."
    )
    @commands.guild_only()
    @app_commands.describe(member="The target server member to extract telemetry data from.")
    async def user_info(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        await ctx.defer(ephemeral=False)
        
        # หากไม่ได้ระบุเป้าหมาย ระบบจะเลือกผู้ใช้งานคำสั่งโดยอัตโนมัติ (Dynamic Fallback)
        member = member or ctx.author

        # --- DATA PROCESSING MATRIX ---
        created_timestamp = int(member.created_at.timestamp()) if member.created_at else None
        joined_timestamp = int(member.joined_at.timestamp()) if member.joined_at else None

        # Roles Matrix Auditing
        roles = [role.mention for role in member.roles if role != ctx.guild.default_role]
        roles_count = len(roles)
        roles_display = ", ".join(roles) if roles else "`NO_CUSTOM_ROLES`"
        if len(roles_display) > 800:
            roles_display = ", ".join(roles[:15]) + f" ... *and {roles_count - 15} more roles*"

        # Key Administrative Permissions Filter
        key_permissions = []
        perms = member.guild_permissions
        if perms.administrator: key_permissions.append("`ADMINISTRATOR`")
        if perms.manage_guild: key_permissions.append("`MANAGE_SERVER`")
        if perms.manage_roles: key_permissions.append("`MANAGE_ROLES`")
        if perms.manage_channels: key_permissions.append("`MANAGE_CHANNELS`")
        if perms.kick_members: key_permissions.append("`KICK_MEMBERS`")
        if perms.ban_members: key_permissions.append("`BAN_MEMBERS`")
        if perms.manage_messages: key_permissions.append("`MANAGE_MESSAGES`")
        if perms.mention_everyone: key_permissions.append("`MENTION_EVERYONE`")
        
        perms_display = ", ".join(key_permissions) if key_permissions else "`STANDARD_USER_PRIVILEGES`"

        # Client / Device Telemetry (Requires Presence Intent Enabled)
        active_devices = []
        if member.desktop_status != discord.Status.offline: active_devices.append("💻 Desktop")
        if member.mobile_status != discord.Status.offline: active_devices.append("📱 Mobile")
        if member.web_status != discord.Status.offline: active_devices.append("🌐 Web Browser")
        devices_display = ", ".join(active_devices) if active_devices else "`OFFLINE_DISCONNECTED`"

        # Active Activities/Statuses Matrix
        activity_display = "`NONE`"
        if member.activities:
            act_list = []
            for act in member.activities:
                if act.type == discord.ActivityType.custom:
                    act_list.append(f"💬 Status: *\"{act.name}\"*")
                else:
                    act_list.append(f"🎮 {act.type.name.title()}: **{act.name}**")
            activity_display = "\n> ".join(act_list)

        # Boosting Status Telemetry
        is_booster = "🟩 ACTIVE PREMIUM BOOSTER" if member.premium_since else "🟥 NOT BOOSTING"
        boost_time = f"<t:{int(member.premium_since.timestamp())}:F>" if member.premium_since else "`N/A`"

        # Embed Baseline Dynamic Color Mapping
        embed_color = member.color if member.color.value != 0 else 0x2B2D31

        # ==========================================
        # --- EMBED 1: IDENTITY CORE ---
        # ==========================================
        embed1 = discord.Embed(
            title=f"👤 User Telemetry Matrix • {member.name}",
            description=f"Extracting fundamental user profile matrix for Global ID: `{member.id}`",
            color=embed_color,
            timestamp=discord.utils.utcnow()
        )
        embed1.set_thumbnail(url=member.display_avatar.url)

        embed1.add_field(
            name="🆔 Account Metadata",
            value=(
                f"> **User Tag:** {member.mention}\n"
                f"> **Global Username:** `{member.name}`\n"
                f"> **Account Classification:** `{f'🤖 AUTOMATED_BOT' if member.bot else '👤 HUMAN_CLIENT'}`"
            ),
            inline=False
        )

        embed1.add_field(
            name="📅 Deployment Timestamps",
            value=(
                f"> **Account Created:** <t:{created_timestamp}:F> (<t:{created_timestamp}:R>)\n"
                f"> **Server Joined Vector:** <t:{joined_timestamp}:F> (<t:{joined_timestamp}:R>)"
            ),
            inline=False
        )
        embed1.set_footer(text=f"Page 1/5 • Powered by RzBot", icon_url=ctx.author.display_avatar.url)

        # ==========================================
        # --- EMBED 2: ROLES & PERMISSIONS ---
        # ==========================================
        embed2 = discord.Embed(
            title=f"🎭 Roles & System Permissions • {member.name}",
            description="Diagnostic review of assigned roles matrix and administrative power nodes.",
            color=embed_color,
            timestamp=discord.utils.utcnow()
        )
        embed2.set_thumbnail(url=member.display_avatar.url)

        embed2.add_field(
            name=f"🎖️ Assigned Server Roles [{roles_count}]",
            value=f"> {roles_display}",
            inline=False
        )

        embed2.add_field(
            name="🛡️ Administrative Key Permissions",
            value=f"> {perms_display}",
            inline=False
        )
        
        embed2.add_field(
            name="🎨 Profile Matrix Color",
            value=f"> Hex Code: `{str(member.color).upper()}`",
            inline=False
        )
        embed2.set_footer(text=f"Page 2/5 • Powered by RzBot", icon_url=ctx.author.display_avatar.url)

        # ==========================================
        # --- EMBED 3: DISPLAY GRAPHIC MATRIX ---
        # ==========================================
        embed3 = discord.Embed(
            title=f"🖼️ Profile Graphic Matrix • {member.name}",
            description="Isolating graphical interface vectors and custom server layouts.",
            color=embed_color,
            timestamp=discord.utils.utcnow()
        )
        embed3.set_thumbnail(url=member.display_avatar.url)
        
        global_avatar = f"[Download Link]({member.avatar.url})" if member.avatar else "`STANDARD_DEFAULT`"
        guild_avatar = f"[Download Link]({member.guild_avatar.url})" if member.guild_avatar else "`NO_LOCAL_OVERRIDE`"
        
        embed3.add_field(
            name="🎭 Graphical Avatar Assets",
            value=f"> **Global User Avatar:** {global_avatar}\n> **Server Local Avatar:** {guild_avatar}",
            inline=False
        )
        
        # ตรวจสอบสิทธิ์ของแบนเนอร์ประจำเซิร์ฟเวอร์
        if hasattr(member, 'guild_banner') and member.guild_banner:
            embed3.set_image(url=member.guild_banner.url)
            embed3.add_field(name="🖼️ Server Banner Variant", value=f"> [Download Banner Link]({member.guild_banner.url})", inline=False)
        else:
            embed3.add_field(name="🖼️ Server Banner Variant", value="> `NO_LOCAL_BANNER_CONFIGURED`", inline=False)
            
        embed3.set_footer(text=f"Page 3/5 • Powered by RzBot", icon_url=ctx.author.display_avatar.url)

        # ==========================================
        # --- EMBED 4: REALTIME PRESENCE & CLIENTS ---
        # ==========================================
        embed4 = discord.Embed(
            title=f"🟢 Status & Client Relays • {member.name}",
            description="Deep diagnostics of realtime presence telemetry and network client nodes.",
            color=embed_color,
            timestamp=discord.utils.utcnow()
        )
        embed4.set_thumbnail(url=member.display_avatar.url)

        embed4.add_field(
            name="⚡ Presence Relay State",
            value=f"> Status: `{str(member.status).upper()}`",
            inline=True
        )

        embed4.add_field(
            name="📱 Active Client Hardware",
            value=f"> Devices: `{devices_display}`",
            inline=True
        )

        embed4.add_field(
            name="🕹️ Current Core Activities",
            value=f"> {activity_display}",
            inline=False
        )
        embed4.set_footer(text=f"Page 4/5 • Powered by RzBot", icon_url=ctx.author.display_avatar.url)

        # ==========================================
        # --- EMBED 5: SECURITY & PROFILING ---
        # ==========================================
        embed5 = discord.Embed(
            title=f"🛡️ Security Profile & Matrix • {member.name}",
            description="Review server specific premium boosting metrics and security vectors.",
            color=embed_color,
            timestamp=discord.utils.utcnow()
        )
        embed5.set_thumbnail(url=member.display_avatar.url)

        embed5.add_field(
            name="💎 Premium Server Booster Status",
            value=(
                f"> **Boosting Engine:** {is_booster}\n"
                f"> **Booster Since:** {boost_time}"
            ),
            inline=False
        )

        is_guild_owner = "🟩 TRUE (SERVER FOUNDER)" if ctx.guild.owner_id == member.id else "🟥 FALSE"
        embed5.add_field(
            name="👑 Guild Crown Vector",
            value=f"> **Guild Owner State:** {is_guild_owner}",
            inline=False
        )
        embed5.set_footer(text=f"Page 5/5 • Powered by RzBot", icon_url=ctx.author.display_avatar.url)

        # --- RENDERING SESSION WITH DROPDOWN VIEW ---
        embeds = [embed1, embed2, embed3, embed4, embed5]
        view = UserInfoPaginator(ctx, embeds)
        view.message = await ctx.send(embed=embeds[0], view=view)

async def setup(bot: commands.Bot):
    await bot.add_cog(UtilityUserInfo(bot))
              
