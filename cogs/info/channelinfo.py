import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timezone
import asyncio
from typing import List, Dict, Any, Optional

# ==========================================
# 📊 UTILITY: CHANNEL TYPE TRANSLATOR
# ==========================================
def get_channel_type_string(channel: discord.abc.GuildChannel) -> str:
    """Translates discord channel types into readable formatted tags."""
    if isinstance(channel, discord.TextChannel):
        return "📝 Text Channel"
    elif isinstance(channel, discord.VoiceChannel):
        return "🔊 Voice Channel"
    elif isinstance(channel, discord.StageChannel):
        return "🎭 Stage Channel"
    elif isinstance(channel, discord.ForumChannel):
        return "🗂️ Forum Channel"
    elif isinstance(channel, discord.CategoryChannel):
        return "📁 Category Room"
    elif isinstance(channel, discord.Thread):
        return "🧵 Thread Line"
    else:
        return "⚙️ System Generic"


# ==========================================
# 🎛️ CHANNEL INFO DISCORD COMPONENTS
# ==========================================
class ChannelInfoDropdown(discord.ui.Select):
    def __init__(self, author: discord.Member, target_channel: discord.abc.GuildChannel):
        options = [
            discord.SelectOption(
                label="Core Metadata", 
                value="page_1", 
                description="Identity keys, types, structure positions, and timelines.", 
                emoji="📊",
                default=True
            ),
            discord.SelectOption(
                label="Permission Matrices", 
                value="page_2", 
                description="Deep permission overwrites, lock stats, and ACL security.", 
                emoji="🔐"
            ),
            discord.SelectOption(
                label="Live Inhabitant Inventory",
                value="page_3",
                description="Active member allocations or room read-access statistics.",
                emoji="👥"
            ),
            discord.SelectOption(
                label="Forum & Thread Layout",
                value="page_4",
                description="Audit forum tags, guidelines, post restrictions and sub-threads.",
                emoji="🍿"
            ),
            discord.SelectOption(
                label="Webhooks & Gateways",
                value="page_5",
                description="Backend active webhooks tracking and external data feeds.",
                emoji="🔌"
            )
        ]
        super().__init__(
            placeholder="Select a channel metrics category to view...", 
            min_values=1, 
            max_values=1, 
            options=options,
            row=0
        )
        self.author = author
        self.target_channel = target_channel

    async def callback(self, interaction: discord.Interaction):
        page_value = self.values[0]
        
        # Sync selected status display
        for option in self.options:
            option.default = (option.value == page_value)

        if page_value == "page_1":
            embed = self.view.build_page_1()
        elif page_value == "page_2":
            embed = self.view.build_page_2()
        elif page_value == "page_3":
            embed = await self.view.build_page_3()
        elif page_value == "page_4":
            embed = self.view.build_page_4()
        elif page_value == "page_5":
            embed = await self.view.build_page_5()
            
        await interaction.response.edit_message(embed=embed, view=self.view)


class ChannelInfoDashboardView(discord.ui.View):
    def __init__(self, bot: commands.Bot, author: discord.Member, target_channel: discord.abc.GuildChannel):
        super().__init__(timeout=300)
        self.bot = bot
        self.author = author
        self.target_channel = target_channel
        self.message = None
        self.embed_color = 0x2B2D31
        self.remaining_time = int(self.timeout)
        
        self.add_item(ChannelInfoDropdown(author, target_channel))
        
        self.delete_btn = discord.ui.Button(
            label=f"Delete Dashboard ({self.remaining_time}s)",
            style=discord.ButtonStyle.danger,
            emoji="🗑️",
            row=1
        )
        self.delete_btn.callback = self.delete_callback
        self.add_item(self.delete_btn)

        self.countdown_task = asyncio.create_task(self.start_countdown())

    async def start_countdown(self):
        try:
            update_interval = 5 
            while self.remaining_time > 0:
                await asyncio.sleep(update_interval)
                self.remaining_time -= update_interval
                
                if self.remaining_time <= 0:
                    break
                    
                self.delete_btn.label = f"Delete Dashboard ({self.remaining_time}s)"
                
                if self.message:
                    try:
                        await self.message.edit(view=self)
                    except (discord.NotFound, discord.HTTPException):
                        break
        except asyncio.CancelledError:
            pass

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("❌ This control panel is locked to the command initiator.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        if hasattr(self, 'countdown_task') and not self.countdown_task.done():
            self.countdown_task.cancel()

        for item in self.children:
            item.disabled = True
            if isinstance(item, discord.ui.Button):
                item.label = "Dashboard Expired (Timed Out)"
                item.style = discord.ButtonStyle.secondary

        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    async def delete_callback(self, interaction: discord.Interaction):
        if interaction.user.guild_permissions.manage_messages or interaction.user.id == self.author.id:
            if hasattr(self, 'countdown_task') and not self.countdown_task.done():
                self.countdown_task.cancel()
            try:
                await interaction.message.delete()
            except discord.HTTPException:
                pass
        else:
            await interaction.response.send_message(
                "❌ **Access Denied:** You lack authorization matrix to purge this information board.", 
                ephemeral=True
            )

    # ---------------------------------------------------
    # 📊 PAGE 1: CORE METADATA
    # ---------------------------------------------------
    def build_page_1(self) -> discord.Embed:
        created_at_ts = int(self.target_channel.created_at.replace(tzinfo=timezone.utc).timestamp())
        creation_str = f"<t:{created_at_ts}:F> (<t:{created_at_ts}:R>)"
        channel_type = get_channel_type_string(self.target_channel)
        category_name = self.target_channel.category.name if hasattr(self.target_channel, 'category') and self.target_channel.category else "None"

        embed = discord.Embed(
            title=f"📊 Analytics: #{self.target_channel.name}",
            color=self.embed_color,
            timestamp=datetime.now(timezone.utc)
        )
        embed.description = f"**Core Infrastructure Configuration Data**"
        
        embed.add_field(name="🆔 Identity Key (ID)", value=f"`{self.target_channel.id}`", inline=False)
        embed.add_field(name="🎚️ Structure Type", value=channel_type, inline=True)
        embed.add_field(name="📁 Parent Category", value=f"📁 {category_name}", inline=True)
        embed.add_field(name="📶 Position Index", value=f"`#{self.target_channel.position + 1}` on list", inline=True)
        embed.add_field(name="📅 Creation Timeline", value=creation_str, inline=False)

        if isinstance(self.target_channel, discord.TextChannel):
            nsfw_status = "🔞 Restricted (NSFW)" if self.target_channel.is_nsfw() else "🟢 Safe Content"
            embed.add_field(name="🔞 Age Guard Status", value=nsfw_status, inline=True)
            embed.add_field(name="🧵 Active Threads", value=f"`{len(self.target_channel.threads)}` active", inline=True)
            topic_summary = self.target_channel.topic if self.target_channel.topic else "*No description topic set for this room.*"
            embed.add_field(name="📋 Channel Topic Description", value=f"> {topic_summary}", inline=False)

        elif isinstance(self.target_channel, (discord.VoiceChannel, discord.StageChannel)):
            bitrate_kbps = int(self.target_channel.bitrate / 1000)
            embed.add_field(name="🔊 Audio Bitrate Pool", value=f"`{bitrate_kbps} Kbps`", inline=True)
            limit_str = f"`{self.target_channel.user_limit}` slots" if self.target_channel.user_limit > 0 else "♾️ No Limit"
            embed.add_field(name="👥 Capacity Cap", value=limit_str, inline=True)

        embed.set_footer(text=f"RzBot Telecom Matrix • Page 1/5", icon_url=self.author.display_avatar.url)
        return embed

    # ---------------------------------------------------
    # 🔐 PAGE 2: DEEP PERMISSION OVERRIDES
    # ---------------------------------------------------
    def build_page_2(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"🔐 Overwrites Matrix: #{self.target_channel.name}",
            color=self.embed_color,
            timestamp=datetime.now(timezone.utc)
        )
        embed.description = (
            "**Detailed Permission Lock State Analytics**\n"
            "This section audits the specific permissions configured for roles overriding this channel.\n"
            "🔒 = **Locked** (Denied) | 🔓 = **Unlocked** (Allowed)"
        )

        overwrites = self.target_channel.overwrites
        if not overwrites:
            embed.add_field(
                name="🛡️ Role Configurations", 
                value="*No specialized permission overrides configured. Inheriting server defaults.*", 
                inline=False
            )
        else:
            role_count = 0
            for target, overwrite in overwrites.items():
                if isinstance(target, discord.Role):
                    role_count += 1
                    if role_count > 4:
                        embed.add_field(
                            name="⚠️ Truncation Notice", 
                            value="*Display system payload optimized. Additional roles are truncated to maintain formatting layout.*", 
                            inline=False
                        )
                        break

                    allowed_perms = []
                    denied_perms = []

                    for perm, value in overwrite:
                        if value is True:
                            allowed_perms.append(perm)
                        elif value is False:
                            denied_perms.append(perm)

                    allowed_str = ", ".join(allowed_perms) if allowed_perms else "None"
                    denied_str = ", ".join(denied_perms) if denied_perms else "None"

                    value_payload = (
                        f"📊 **Summary Structure:** `🔓 Unlocked: {len(allowed_perms)}` | `🔒 Locked: {len(denied_perms)}` \n"
                        f"```diff\n"
                        f"+ Unlocked Permissions:\n  {allowed_str}\n\n"
                        f"- Locked Permissions:\n  {denied_str}\n"
                        f"```"
                    )
                    
                    embed.add_field(
                        name=f"🎭 Overwrite Node: @{target.name}", 
                        value=value_payload, 
                        inline=False
                    )

        embed.set_footer(text=f"RzBot Telecom Matrix • Page 2/5", icon_url=self.author.display_avatar.url)
        return embed

    # ---------------------------------------------------
    # 👥 PAGE 3: LIVE INHABITANT INVENTORY
    # ---------------------------------------------------
    async def build_page_3(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"👥 Live Inhabitant Inventory: #{self.target_channel.name}",
            color=self.embed_color,
            timestamp=datetime.now(timezone.utc)
        )

        if isinstance(self.target_channel, (discord.VoiceChannel, discord.StageChannel)):
            current_users = self.target_channel.members
            total_connected = len(current_users)
            embed.description = f"**Active Voice Socket Diagnostics**\nCurrently connected users inside this telecom pipeline: `{total_connected}` active."
            
            if total_connected > 0:
                sampling = current_users[:20]
                users_payload = ", ".join(m.mention for m in sampling)
                if total_connected > 20:
                    users_payload += f" ... *and `{total_connected - 20}` more in stream.*"
            else:
                users_payload = "*Room pipeline empty. No users streaming voice arrays.*"
                
            embed.add_field(name="🎙️ Connected Sound Feeds", value=users_payload, inline=False)
        else:
            guild_members = self.target_channel.guild.members
            accessible_count = 0
            for m in guild_members:
                if self.target_channel.permissions_for(m).read_messages:
                    accessible_count += 1
                    
            embed.description = (
                f"**Static Room Read-Access Survey**\n"
                f"» Enrolled Server Population: `{len(guild_members):,}` accounts\n"
                f"» Verified Clearance Vector: `{accessible_count:,}` users can see this channel."
            )

        embed.set_footer(text=f"RzBot Telecom Matrix • Page 3/5", icon_url=self.author.display_avatar.url)
        return embed

    # ---------------------------------------------------
    # 🎭 PAGE 4: FORUM & THREAD STREAM LAYOUT
    # ---------------------------------------------------
    def build_page_4(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"🍿 Forum & Thread Layout: #{self.target_channel.name}",
            color=self.embed_color,
            timestamp=datetime.now(timezone.utc)
        )
        embed.description = "**Analyzing structured forum architectures and internal timeline threads.**"

        if isinstance(self.target_channel, discord.ForumChannel):
            tags = [f"`{tag.name}`" for tag in self.target_channel.available_tags]
            tags_display = ", ".join(tags) if tags else "`NO_TAGS_CONFIGURED`"
            guidelines = self.target_channel.topic if self.target_channel.topic else "*No layout guidelines set.*"
            
            embed.add_field(name="📋 Forum Guidelines", value=f"> {guidelines}", inline=False)
            embed.add_field(name="🏷️ Available System Tags", value=tags_display, inline=False)
            embed.add_field(name="⏳ Post Interface Slowmode", value=f"`{self.target_channel.slowmode_delay}s` interval", inline=True)
            embed.add_field(name="🗂️ Default Sort Order", value=f"`{str(self.target_channel.default_sort_order).upper()}`", inline=True)
            
        elif isinstance(self.target_channel, discord.Thread):
            embed.add_field(name="🪡 Archival Lock State", value=f"`Locked: {self.target_channel.locked}`", inline=True)
            embed.add_field(name="⏱️ Auto-Archive Duration", value=f"`{self.target_channel.auto_archive_duration} minutes`", inline=True)
            embed.add_field(name="👑 Thread Founder/Creator", value=f"<@{self.target_channel.owner_id}>", inline=False)
        else:
            slowmode = getattr(self.target_channel, 'slowmode_delay', 0)
            slowmode_str = f"`{slowmode}s` interval" if slowmode > 0 else "🔴 Disabled"
            embed.add_field(name="⏳ Message Interface Slowmode", value=slowmode_str, inline=True)
            embed.add_field(name="⚙️ Architecture Status", value="*This entity type is not a complex Forum node or a sub-thread stream.*", inline=False)

        embed.set_footer(text=f"RzBot Telecom Matrix • Page 4/5", icon_url=self.author.display_avatar.url)
        return embed

    # ---------------------------------------------------
    # 🔌 PAGE 5: ADVANCED WEBHOOKS & INTEGRATION
    # ---------------------------------------------------
    async def build_page_5(self) -> discord.Embed:
        embed = discord.Embed(
            title=f"🔌 Live Gateway Integrations: #{self.target_channel.name}",
            color=self.embed_color,
            timestamp=datetime.now(timezone.utc)
        )
        embed.description = "**Scoping automated HTTP API pipeline nodes attached to this workspace.**"

        if isinstance(self.target_channel, (discord.TextChannel, discord.VoiceChannel, discord.ForumChannel, discord.StageChannel)):
            try:
                webhooks = await self.target_channel.webhooks()
                webhook_count = len(webhooks)
                embed.add_field(name="📡 Total Active Webhook Nodes", value=f"`{webhook_count}` pipelines configured", inline=False)
                
                if webhook_count > 0:
                    lines = []
                    for idx, wh in enumerate(webhooks[:5]):
                        creator = wh.user.mention if wh.user else "`System Core`"
                        wh_type = "Application Bot Hook" if wh.type == discord.WebhookType.application else "Incoming Payload Hook"
                        
                        if wh.user and wh.user.id == self.bot.user.id:
                            url_display = f"\n> 🔗 **Webhook URL:** ||{wh.url}||"
                        else:
                            url_display = "\n> 🔗 **Webhook URL:** *[Hidden - Unauthorized to view non-owned webhooks]*"

                        lines.append(
                            f"**{idx+1}. {wh.name}**\n"
                            f"> 🧩 Core Node ID: `{wh.id}`\n"
                            f"> 🛠️ Bound Type: `{wh_type}` | Spawned by: {creator}"
                            f"{url_display}"
                        )
                        
                    if webhook_count > 5:
                        lines.append(f"\n*... and `{webhook_count - 5}` more hidden background pipelines.*")
                    embed.add_field(name="🛡️ Audited Integration Feeds", value="\n".join(lines), inline=False)
                else:
                    embed.add_field(name="🛡️ Audited Integration Feeds", value="*No incoming Webhook infrastructure bound to this room.*", inline=False)
            except discord.Forbidden:
                embed.add_field(name="❌ Security Error", value="*RzBot lack `Manage Webhooks` permissions grid to read this infrastructure map.*", inline=False)
        else:
            embed.add_field(name="🎚️ Architecture Block", value="*This specific directory entity type does not support direct HTTP Webhook bindings.*", inline=False)

        embed.set_footer(text=f"RzBot Telecom Matrix • Page 5/5", icon_url=self.author.display_avatar.url)
        return embed


# ==========================================
# 🛠️ MAIN CHANNEL INFO COG & ERROR HANDLER
# ==========================================
class ChannelInfo(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="channelinfo",
        aliases=["cinfo", "ci"],
        description="Fetch comprehensive multi-page operational metadata for a specific channel! 📊"
    )
    @app_commands.describe(
        channel="The target channel to inspect. Leave empty to audit the current active channel room."
    )
    @commands.guild_only()
    async def channelinfo(self, ctx: commands.Context, channel: Optional[discord.abc.GuildChannel] = None):
        """Deep channel analysis gateway - Fallback routing assigns current active context if parameters are vacant."""
        
        # 💡 ปรับปรุง: หากไม่มีการเลือกช่อง (None) ระบบจะดึงห้องปัจจุบันมาใช้อัตโนมัติ
        target_channel = channel or ctx.channel
        
        # Pre-check: Verify if the bot has view permission for the target channel
        bot_permissions = target_channel.permissions_for(ctx.guild.me)
        if not bot_permissions.view_channel:
            embed = discord.Embed(
                title="❌ Matrix Access Blocked",
                description=f"**Error:** The bot does not have sufficient permission matrix to view or access {target_channel.mention}.\nPlease grant `View Channel` authorization to the bot profile.",
                color=discord.Color.red()
            )
            return await ctx.send(embed=embed, ephemeral=True)

        await ctx.defer()

        # Instantiate dashboard view with verified target channel parameters
        view = ChannelInfoDashboardView(self.bot, ctx.author, target_channel)
        initial_embed = view.build_page_1()
        
        msg = await ctx.send(embed=initial_embed, view=view)
        view.message = msg

    @channelinfo.error
    async def channelinfo_error(self, ctx: commands.Context, error: commands.CommandError):
        """Universal gateway exception event handling structure."""
        embed = discord.Embed(title="🚨 Execution System Failure", color=discord.Color.red())
        
        if isinstance(error, commands.ChannelNotFound):
            embed.description = "**Error:** The specified channel container or channel ID could not be located inside this guild cluster."
        elif isinstance(error, commands.NoPrivateMessage):
            embed.description = "**Error:** This analytical control unit is strictly restricted to guild network sectors."
        else:
            embed.description = f"**Error:** An unexpected gateway system anomaly has occurred:\n`{str(error)}`"
            
        if ctx.interaction:
            if ctx.interaction.response.is_done():
                await ctx.followup.send(embed=embed, ephemeral=True)
            else:
                await ctx.interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(ChannelInfo(bot))