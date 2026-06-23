import discord
from discord import app_commands
from discord.ext import commands

# =======================================================
# 🎛️ DYNAMIC INTERACTIVE AVATAR & BANNER VIEW
# =======================================================
class AvatarDownloaderView(discord.ui.View):
    def __init__(self, bot: commands.Bot, ctx: commands.Context, target_user: discord.Member):
        super().__init__(timeout=180)  # Expires in 3 minutes to free up RAM overhead
        self.bot = bot
        self.ctx = ctx
        self.target_user = target_user
        self.message = None
        self.current_mode = "avatar"  # Tracks whether avatar or banner asset is displayed

        # Initialize the default asset configuration buttons
        self.refresh_format_buttons()

    def refresh_format_buttons(self):
        """Rebuilds the asset-specific link buttons based on the active mode selection."""
        # Clean out any pre-existing buttons to prevent duplicate stacks
        self.clear_items()

        # 1. Target URL Mapping System
        if self.current_mode == "avatar":
            base_asset = self.target_user.avatar if self.target_user.avatar else self.target_user.display_avatar
        else:
            base_asset = self.target_user.banner

        # 2. Dynamic Asset URL Link Generation Block
        if base_asset:
            # Generate static requirements: PNG and JPEG
            png_url = base_asset.with_format("png").with_size(1024).url
            jpg_url = base_asset.with_format("jpg").with_size(1024).url
            
            self.add_item(discord.ui.Button(label="Download .PNG", style=discord.ButtonStyle.link, url=png_url, row=0))
            self.add_item(discord.ui.Button(label="Download .JPG", style=discord.ButtonStyle.link, url=jpg_url, row=0))

            # Conditional format requirement: GIF (Active only if the source profile asset is animated)
            if base_asset.is_animated():
                gif_url = base_asset.with_format("gif").with_size(1024).url
                self.add_item(discord.ui.Button(label="Download .GIF", style=discord.ButtonStyle.link, url=gif_url, row=0))

        # 3. Append Action/State Interactivity Switch Controllers
        self.add_item(self.avatar_toggle_button)
        self.add_item(self.banner_toggle_button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Enforces restriction matrix: only the command initiator can execute adjustments."""
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("<:No:1517480787744784475> You cannot modify this asset configuration matrix.", ephemeral=True)
            return False
        return True

    # =======================================================
    # 🎭 INTERACTIVE CONTROL SWITCH ACTIONS
    # =======================================================
    @discord.ui.button(label="View Avatar", style=discord.ButtonStyle.primary, emoji="👤", row=1)
    async def avatar_toggle_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Switches the context matrix viewport back to the user's avatar asset array."""
        self.current_mode = "avatar"
        self.refresh_format_buttons()

        embed = interaction.message.embeds[0]
        embed.title = f"🖼️ Avatar Asset Matrix • {self.target_user.name}"
        embed.set_image(url=self.target_user.display_avatar.with_size(1024).url)

        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="View Banner", style=discord.ButtonStyle.primary, emoji="🎏", row=1)
    async def banner_toggle_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Switches the context matrix viewport to the user's banner profile asset array."""
        # 🛡️ Fetch full profile telemetry via API payload to securely detect banner structures
        user_profile = await self.bot.fetch_user(self.target_user.id)
        
        if not user_profile.banner:
            # Emergency fail-safe fallback: block action and disable button mapping to prevent crashes
            button.disabled = True
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("<:No:1517480787744784475> This user does not have an active profile banner configured.", ephemeral=True)
            return

        self.current_mode = "banner"
        self.refresh_format_buttons()

        embed = interaction.message.embeds[0]
        embed.title = f"🖼️ Banner Asset Matrix • {self.target_user.name}"
        embed.set_image(url=user_profile.banner.with_size(1024).url)

        await interaction.response.edit_message(embed=embed, view=self)


# =======================================================
# 😴 MAIN UTILITY COG CORE ENGINE
# =======================================================
class UtilityAvatar(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="avatar",
        aliases=["av", "pfp", "banner"],
        description="Extract and download high-resolution profile assets (Avatar & Banners).",
        help="Extract and download the high-resolution profile asset arrays of a specified target."
    )
    @app_commands.describe(user="The target member whose profile assets you want to compile.")
    @commands.guild_only()
    async def avatar(self, ctx: commands.Context, user: discord.Member = None):
        """Processes hybrid command allocation layers for cross-context safety."""
        target_user = user or ctx.author
        
        # Pull extended API profile metrics to check for banner asset data instantly
        user_profile = await self.bot.fetch_user(target_user.id)

        embed = discord.Embed(
            title=f"🖼️ Avatar Asset Matrix • {target_user.name}",
            description=f"Successfully extracted structural resolution arrays for {target_user.mention}.",
            color=0x2B2D31,
            timestamp=discord.utils.utcnow()
        )
        embed.set_image(url=target_user.display_avatar.with_size(1024).url)
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        
        view = AvatarDownloaderView(self.bot, ctx, target_user)

        # 🦾 Enforce Disabled mode condition directly on initialization if no banner payload exists
        if not user_profile.banner:
            view.banner_toggle_button.disabled = True

        view.message = await ctx.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(UtilityAvatar(bot))
