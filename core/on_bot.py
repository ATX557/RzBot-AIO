import discord
from discord.ext import commands
from discord.utils import utcnow
from typing import Optional

# =======================================================
# 🔘 UI COMPONENTS: INTERFACE ACTION BUTTONS
# =======================================================
class IntroActionView(discord.ui.View):
    """Interactive navigation hub deployed alongside system introduction metrics."""
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None) # Persistent view, won't expire
        
        # Safe check: If bot is not logged in yet, default to an empty or placeholder ID
        bot_id = bot.user.id if bot.user else 0
        
        # Formulate secure application invite link dynamically
        invite_url = discord.utils.oauth_url(
            bot_id,
            permissions=discord.Permissions(8584986789675007), # Requests Administrator authority by default
            scopes=("bot", "applications.commands")
        )
        
        # Add dynamic link buttons to the view grid
        if bot_id != 0:
            self.add_item(discord.ui.Button(label="Deploy to Another Sector", url=invite_url, emoji="🚀"))


# =======================================================
# 🛰️ CORE COG: SYSTEM INTRODUCTION INTEL
# =======================================================
class BotIntroduction(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _get_unique_commands_count(self) -> int:
        """Helper to safely filter unique command structures across hybrid registries."""
        prefix_cmds = set(c.name for c in self.bot.commands)
        slash_cmds = set(c.name for c in self.bot.tree.get_commands())
        return len(prefix_cmds.union(slash_cmds))  # 🛠️ FIXED: Added the dot for .union()

    # =======================================================
    # 🟩 EVENT: BOT GUILD INITIALIZATION (JOIN SERVER)
    # =======================================================
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """Dispatches an initialization introduction matrix when joining a new server sector."""
        total_commands = self._get_unique_commands_count()
        command_prefix = "$"  # Match this with your bot's system prefix

        embed = discord.Embed(
            title="🛰️ System Integration Successful",
            description=f"Hello! I am **{self.bot.user.name if self.bot.user else 'The Bot'}**, an advanced operational utility core designed to manage and optimize this guild sector.",
            color=0x2B2D31,
            timestamp=utcnow()
        )
        
        if self.bot.user and self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        # Enhanced operational telemetry statistics
        embed.add_field(
            name="🎮 SYSTEM CORE TELEMETRY",
            value=(
                f"• **Command Prefix:** `{command_prefix}`\n"
                f"• **Available Protocols:** `{total_commands}` unique commands loaded\n"
                f"• **Global Infrastructure:** `{len(self.bot.guilds):,}` clusters indexed"
            ),
            inline=False
        )
        
        # New Feature: Targeted Guild Analysis Data Field
        embed.add_field(
            name="📊 TARGET SECTOR PROFILE",
            value=(
                f"• **Sector Identity:** `{guild.name}`\n"
                f"• **Population Matrix:** `{guild.member_count:,}` users detected\n"
                f"• **Sector Authority:** {guild.owner.mention if guild.owner else '`Unknown Signature`'}" # 🛠️ FIXED: Removed stray character
            ),
            inline=False
        )
        
        bot_name = self.bot.user.name.lower() if self.bot.user else "bot"
        embed.add_field(
            name="🛠️ INITIALIZATION INSTRUCTION",
            value=f"To view the complete diagnostics matrix and list of commands, please execute `/{bot_name} help` or use the prefix command `{command_prefix}help`.",
            inline=False
        )
        
        if self.bot.user:
            embed.set_footer(text=f"{self.bot.user.name} Operational Protocol • Online")

        # Instantiate interactive button controls
        view = IntroActionView(self.bot)

        # Find the first available text channel where the bot has send permissions
        for channel in guild.text_channels:
            permissions = channel.permissions_for(guild.me)
            if permissions.send_messages and permissions.embed_links:
                try:
                    await channel.send(embed=embed, view=view)
                    break
                except discord.HTTPException:
                    continue

    # =======================================================
    # 📡 EVENT: INTERCEPT PURE MENTION / IGNORE CONTENT TAGS
    # =======================================================
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Intercepts messages to detect absolute pure mentions, ignoring multi-string content tags."""
        # Ignore automated bot transmissions to prevent endless feedback loops
        if message.author.bot or not self.bot.user:
            return

        # Check if the message structure mentions this bot instance
        if self.bot.user.mentioned_in(message):
            content = message.content.strip()
            
            # Corrected string interpolation for strict mention checks
            strict_mention_1 = f"<@{self.bot.user.id}>"
            strict_mention_2 = f"<@!{self.bot.user.id}>"

            # Condition: Trigger ONLY if the message content is exclusively the bot's mention tag
            if content == strict_mention_1 or content == strict_mention_2:
                command_prefix = "$"  # Match this with your bot's system prefix
                
                embed = discord.Embed(
                    title=f"📡 Core System Node Active: {self.bot.user.name}",
                    description=(
                        f"Operational mainframe is online and monitoring network signals.\n\n"
                        f"• **Current Prefix Vector:** `{command_prefix}`\n"
                        f"• **Application Interface:** Try typing `/` to view slash commands.\n"
                        f"• **Support Protocol:** Use `{command_prefix}help` for terminal details.\n"
                        f"• [Website official](https://rzbot.wasmer.app/)"
                    ),
                    color=0x2B2D31,
                    timestamp=utcnow()
                )
                embed.set_footer(text="Telecom Matrix Response Grid", icon_url=message.author.display_avatar.url)
                
                # Attach the UI buttons to the ping mention response as well
                view = IntroActionView(self.bot)
                
                try:
                    await message.channel.send(embed=embed, view=view)
                except discord.Forbidden:
                    pass  # Safeguard against missing permission parameters in target channel
            else:
                return


# Module setup registration matrix
async def setup(bot: commands.Bot):
    await bot.add_cog(BotIntroduction(bot))
      
