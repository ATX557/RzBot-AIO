import discord
from discord import app_commands
from discord.ext import commands
import time
from datetime import datetime, timezone
from typing import Optional

# ==========================================
# 📊 UTILITY: PREMIUM PROGRESS BAR GENERATOR
# ==========================================
def make_premium_bar(percentage: float, length: int = 12) -> str:
    """Generates a high-contrast smooth Unicode progress layout bar."""
    filled_length = int(round(length * percentage / 100))
    bar = "▓" * filled_length + "▒" * (length - filled_length)
    return bar


# ==========================================
# 🎛️ DYNAMIC POLL BUTTON NODES (PURE NUMERIC)
# ==========================================
class PollButton(discord.ui.Button):
    def __init__(self, number: int):
        # 🛠️ ปรับปรุง: แสดงผลเฉพาะตัวเลขเพียวๆ ไม่มีข้อความ และไม่มีอีโมจิห้อยท้าย
        super().__init__(
            style=discord.ButtonStyle.primary,
            label=str(number),
            emoji=None,
            custom_id=f"kitsumi_poll_node_{number}",
            row=0  # จัดวางกลุ่มปุ่มตัวเลขไว้ที่แถวแรกเสมอกัน
        )
        self.number = number

    async def callback(self, interaction: discord.Interaction):
        view: PollVoteView = self.view
        user_id = interaction.user.id

        if user_id in view.user_votes:
            previous_vote = view.user_votes[user_id]
            if previous_vote == self.number:
                # Cancel action registry
                view.votes[self.number] -= 1
                del view.user_votes[user_id]
                msg_status = "↩️ Removed your ballot from this active session."
            else:
                # Migration tracking shift
                view.votes[previous_vote] -= 1
                view.votes[self.number] += 1
                view.user_votes[user_id] = self.number
                msg_status = f"🔄 Swapped ballot selection over to **Option {self.number}**"
        else:
            # New record entry allocation
            view.votes[self.number] += 1
            view.user_votes[user_id] = self.number
            msg_status = f"✅ Registered your vote for **Option {self.number}**"

        updated_embed = view.update_poll_embed()
        await interaction.response.edit_message(embed=updated_embed, view=view)
        await interaction.followup.send(msg_status, ephemeral=True)


# ==========================================
# 🔍 INTERACTIVE ANALYTICS CONTROLLER BUTTON
# ==========================================
class ViewPollAnalyticsButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            style=discord.ButtonStyle.secondary,
            label="View Poll Metrics",
            emoji="🔍",
            custom_id="kitsumi_poll_inspector_node",
            row=1  # แยกปุ่มดูรายละเอียดลงมาที่แถวสอง เพื่อไม่ให้ปนกับปุ่มตัวเลข
        )

    async def callback(self, interaction: discord.Interaction):
        view: PollVoteView = self.view
        guild = interaction.guild
        
        # 🛡️ Dynamic Human-Only Telemetry Calculation
        total_humans = [m for m in guild.members if not m.bot]
        total_human_count = len(total_humans)
        
        voted_users_count = len(view.user_votes)
        unvoted_count = max(0, total_human_count - voted_users_count)

        # Map active voter layouts by their specific configurations
        voter_mapping_lines = []
        for i in range(len(view.options_list)):
            opt_num = i + 1
            voters_for_opt = [f"<@{uid}>" for uid, choice in view.user_votes.items() if choice == opt_num]
            voters_str = ", ".join(voters_for_opt) if voters_for_opt else "None"
            voter_mapping_lines.append(f"**[{opt_num}] {view.options_list[i]}:** {voters_str}")

        voters_registry_data = "\n".join(voter_mapping_lines)
        remaining_time = max(0, view.end_time - int(time.time()))

        metrics_embed = discord.Embed(
            title="🔬 Active Ballots Inspection Board",
            color=0x9B59B6,
            timestamp=datetime.now(timezone.utc)
        )
        metrics_embed.add_field(
            name="📊 Target Voter Allocations", 
            value=voters_registry_data, 
            inline=False
        )
        metrics_embed.add_field(
            name="📉 Sync Metrics Tracking", 
            value=(
                f"• Total Active Ballots Filed: `{voted_users_count}`\n"
                f"• Unvoted Human Members remaining: `{unvoted_count}`\n"
                f"• Total Session Time Limit: `{view.timeout_secs:.0f}s`\n"
                f"• Remaining Life Window: `{remaining_time}s`"
            ), 
            inline=False
        )
        metrics_embed.set_footer(text="Confidential Live Analytics Protocol Framework")

        await interaction.response.send_message(embed=metrics_embed, ephemeral=True)


# ==========================================
# 📊 POLL DASHBOARD VIEW CONTROL
# ==========================================
class PollVoteView(discord.ui.View):
    def __init__(self, author: discord.Member, question: str, options: list, timeout_secs: float):
        super().__init__(timeout=timeout_secs)
        self.author = author
        self.question = question
        self.options_list = options
        self.timeout_secs = timeout_secs
        self.message: Optional[discord.Message] = None
        self.end_time = int(time.time()) + int(timeout_secs)
        
        self.votes = {i+1: 0 for i in range(len(options))}
        self.user_votes = {}

        # 1. Spawn precise incremental numeric button elements matching option length
        for idx in range(len(options)):
            self.add_item(PollButton(number=idx+1))
            
        # 2. Append the analytical inspection registry controller node
        self.add_item(ViewPollAnalyticsButton())

    def update_poll_embed(self, closed: bool = False) -> discord.Embed:
        """Compiles structure records, shifting state color matrices dynamically."""
        total_votes = len(self.user_votes)
        
        embed = discord.Embed(
            title=f"🔒 [CONCLUDED] {self.question}" if closed else f"📊 LIVE POLL: {self.question}",
            color=0x2C3E50 if closed else 0x3498DB,
            timestamp=datetime.now(timezone.utc)
        )
        
        if closed:
            embed.description = (
                f"**Created by Admin:** {self.author.mention}\n"
                f"🛑 *This election cycle is officially finalized. The voting terminal is now locked down.*"
            )
        else:
            embed.description = (
                f"**Created by Admin:** {self.author.mention}\n"
                f"💡 *Press the numerical inputs to vote. Pressing the same option twice cancels your vote.*\n\n"
                f"⏳ **Time Parameters:** Active until <t:{self.end_time}:f> (<t:{self.end_time}:R>)"
            )

        # Render data rows dynamically alongside metrics
        for idx, option in enumerate(self.options_list):
            num = idx + 1
            vote_count = self.votes[num]
            percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
            
            bar_str = make_premium_bar(percentage)
            
            embed.add_field(
                name=f"**[{num}]** {option}",
                value=f"{bar_str} `{vote_count:>2}v` ({round(percentage, 1)}%)",
                inline=False
            )

        embed.set_footer(
            text=f"Secure Voting Protocol Matrix • {total_votes} active responses verified",
            icon_url=self.author.display_avatar.url
        )
        return embed

    async def on_timeout(self):
        """Automated finalization processing sequence triggered upon timeout windows closing."""
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

        if self.message:
            try:
                final_embed = self.update_poll_embed(closed=True)
                await self.message.edit(embed=final_embed, view=self)
            except discord.HTTPException:
                pass


# ==========================================
# 🛠️ MAIN POLL COG MODULE
# ==========================================
class Poll(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        name="poll",
        description="📊 Launch an interactive pipe-delimited live-voting session (Admin Restricted)."
    )
    @app_commands.describe(
        question="The core target topic or inquiry for this session.",
        duration="Matrix lifetime parameters (e.g., 30s, 5m, 1h).",
        options="Delimit choice using structural pipelines | (e.g., Yes | No) • Max 5 items"
    )
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def poll_command(self, ctx: commands.Context, question: str, duration: str, *, options: str):
        """Evaluates structural validation boundaries and instantiates custom voting views."""
        await ctx.defer()

        # Split using structural pipeline design token parsing
        raw_options = [opt.strip() for opt in options.split("|") if opt.strip()]
        
        # Enforce character token array range bounds verification
        if len(raw_options) > 5 or len(raw_options) < 2:
            embed_err = discord.Embed(
                description="❌ **Poll Configuration Blocked:** Please supply between **2 to 5 choice options** separated by `|` strings.",
                color=0xE74C3C
            )
            return await ctx.send(embed=embed_err)

        # Parse countdown duration layouts
        try:
            unit = duration[-1].lower()
            value = int(duration[:-1])
            multipliers = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}

            if unit not in multipliers or value <= 0:
                raise ValueError
                
            timeout_seconds = value * multipliers[unit]
        except (ValueError, IndexError):
            embed_err = discord.Embed(
                description="❌ **Invalid Duration Parameter:** Please format lifecycle strings correctly (e.g., `45s`, `15m`, `3h`).",
                color=0xE74C3C
            )
            return await ctx.send(embed=embed_err)

        # Build runtimes
        view = PollVoteView(ctx.author, question, raw_options, float(timeout_seconds))
        initial_embed = view.update_poll_embed(closed=False)
        
        msg = await ctx.send(embed=initial_embed, view=view)
        view.message = msg

    # ==========================================
    # 🚨 ERROR GATEWAY FOR ADMINS PERMISSION
    # ==========================================
    @poll_command.error
    async def poll_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Captures restriction breaches or configuration errors gracefully."""
        embed = discord.Embed(title="🚨 Poll Deployment Failure", color=0xE74C3C)
        
        if isinstance(error, commands.MissingPermissions):
            embed.description = "❌ **Access Denied:** You lack the `Administrator` clearance permissions to deploy voting mainframe protocols."
        else:
            embed.description = f"An unexpected network error was intercepted:\n`{str(error)}`"
            
        await ctx.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Poll(bot))
