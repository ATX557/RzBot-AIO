import discord
from discord.ext import commands
import aiohttp
import os
import traceback

class CommandTelemetryLogger(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def dispatch_webhook(self, webhook_env_name: str, embed: discord.Embed):
        """Dispatches telemetry logs to the designated Discord Webhook URL mapped in .env."""
        webhook_url = os.getenv(webhook_env_name)
        if not webhook_url:
            print(f"⚠️ [Telemetry Error] Missing variable `{webhook_env_name}` in your .env configuration.")
            return

        async with aiohttp.ClientSession() as session:
            try:
                webhook = discord.Webhook.from_url(webhook_url, session=session)
                await webhook.send(
                    embed=embed,
                    username=f"{self.bot.user.name} Analytics Node",
                    avatar_url=self.bot.user.display_avatar.url
                )
            except Exception as e:
                print(f"❌ [Webhook Dispatch Failed] Unable to forward command log transmission: {str(e)}")

    # =======================================================
    # 📡 EVENT: DETECT & LOG EXECUTION SUCCESS
    # =======================================================
    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        """Intercepts and records telemetry when a traditional prefix-based text command completes successfully."""
        # Determine location vector metrics (Guild or DM Channel)
        if ctx.guild:
            location_vector = f"📡 **Server:** `{ctx.guild.name}`\n> 🔗 **Channel:** {ctx.channel.mention} (`#{ctx.channel.name}`)"
            server_id = f"`{ctx.guild.id}`"
        else:
            location_vector = "🔒 **Direct Message (DM Channel)**"
            server_id = "`N/A (PRIVATE_NODE)`"

        # Capture raw payload string invoked by the operator
        invoked_message = ctx.message.content if ctx.message else f"{ctx.prefix}{ctx.command.qualified_name}"

        log_embed = discord.Embed(
            title="⚡ Text Command Executed",
            description=f"Detected active infrastructure interaction via text-based command interface.",
            color=0x3498DB, 
            timestamp=discord.utils.utcnow()
        )
        log_embed.set_thumbnail(url=ctx.author.display_avatar.url)

        log_embed.add_field(
            name="👤 OPERATOR PROFILE",
            value=(
                f"• **User Tag:** {ctx.author.mention}\n"
                f"• **Username:** `{ctx.author.name}`\n"
                f"• **Global ID:** `{ctx.author.id}`"
            ),
            inline=False
        )

        log_embed.add_field(
            name="📥 COMMAND MATRIX",
            value=(
                f"• **Invoked Node:** `{ctx.command.qualified_name}`\n"
                f"• **Raw Payload:** `{invoked_message}`"
            ),
            inline=False
        )

        log_embed.add_field(
            name="📍 LOCATION TARGET",
            value=f"• {location_vector}\n• **Target Guild ID:** {server_id}",
            inline=False
        )
        log_embed.set_footer(text="Execution Success Node • Logged via Analytics Matrix")

        await self.dispatch_webhook("WEBHOOK_COMMAND_LOG", log_embed)


    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction: discord.Interaction, command: discord.app_commands.Command or discord.app_commands.ContextMenu):
        """Intercepts and records telemetry when an Application Slash Command completes successfully."""
        if interaction.guild:
            location_vector = f"📡 **Server:** `{interaction.guild.name}`\n> 🔗 **Channel:** {interaction.channel.mention if interaction.channel else '`UNKNOWN`'}"
            server_id = f"`{interaction.guild.id}`"
        else:
            location_vector = "🔒 **Direct Message (DM Channel)**"
            server_id = "`N/A (PRIVATE_NODE)`"

        # Parse slash options/arguments layout array safely
        options = interaction.data.get("options", []) if interaction.data else []
        parsed_payload = f"/{command.name} " + " ".join([f"{opt.get('name')}:{opt.get('value')}" for opt in options])

        log_embed = discord.Embed(
            title="⚡ Slash Command Executed",
            description=f"Detected active infrastructure interaction via Application Command framework (Slash).",
            color=0x9B59B6, 
            timestamp=discord.utils.utcnow()
        )
        log_embed.set_thumbnail(url=interaction.user.display_avatar.url)

        log_embed.add_field(
            name="👤 OPERATOR PROFILE",
            value=(
                f"• **User Tag:** {interaction.user.mention}\n"
                f"• **Username:** `{interaction.user.name}`\n"
                f"• **Global ID:** `{interaction.user.id}`"
            ),
            inline=False
        )

        log_embed.add_field(
            name="📥 APPLICATION COMMAND MATRIX",
            value=(
                f"• **Invoked Node:** `/{command.name}`\n"
                f"• **Vector Payload:** `{parsed_payload.strip()}`"
            ),
            inline=False
        )

        log_embed.add_field(
            name="📍 LOCATION TARGET",
            value=f"• {location_vector}\n• **Target Guild ID:** {server_id}",
            inline=False
        )
        log_embed.set_footer(text="Slash Execution Success Node • Logged via Analytics Matrix")

        await self.dispatch_webhook("WEBHOOK_COMMAND_LOG", log_embed)


    # =======================================================
    # ⚠️ EVENT: ERROR TRACKING & FAULT DIAGNOSTICS
    # =======================================================
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Intercepts system operational critical failures during prefix text command processes."""
        # Bypass custom handled feedback components to avoid payload spam
        if isinstance(error, commands.CommandOnCooldown) or isinstance(error, commands.CheckFailure):
            return

        if ctx.guild:
            location_vector = f"📡 **Server:** `{ctx.guild.name}`\n> 🔗 **Channel:** {ctx.channel.mention}"
        else:
            location_vector = "🔒 **Direct Message (DM Channel)**"

        # Build clean string mapping formatting from the traceback structure stack
        error_traceback = "".join(traceback.format_exception(type(error), error, error.__traceback__))
        if len(error_traceback) > 950:
            error_traceback = error_traceback[:940] + "\n... [Traceback output exceeds block limit configuration]"

        error_embed = discord.Embed(
            title="<:No:1517480787744784475> System Internal Crash / Failure",
            description="Diagnostic analysis intercepted a technical exception within the core text execution module.",
            color=0xE74C3C, 
            timestamp=discord.utils.utcnow()
        )
        error_embed.set_thumbnail(url=ctx.author.display_avatar.url)

        error_embed.add_field(
            name="👤 TRIGGER OPERATOR",
            value=f"• User: {ctx.author.mention} | ID: `{ctx.author.id}`",
            inline=True
        )
        error_embed.add_field(
            name="📍 ERROR SECTOR",
            value=location_vector,
            inline=True
        )
        error_embed.add_field(
            name="📥 FAULTY COMMAND INPUT",
            value=f"• Action Name: `{ctx.command.qualified_name if ctx.command else 'Unknown'}`\n• Input: `{ctx.message.content if ctx.message else 'N/A'}`",
            inline=False
        )
        error_embed.add_field(
            name="📦 EXCEPTION TRACEBACK REPORT",
            value=f"```py\n{error_traceback}\n```",
            inline=False
        )
        error_embed.set_footer(text="Critical System Exception Intercepted")

        await self.dispatch_webhook("WEBHOOK_COMMAND_ERROR", error_embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(CommandTelemetryLogger(bot))
