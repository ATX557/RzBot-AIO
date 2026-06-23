import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
from discord.utils import utcnow
import time
from typing import Optional

# UI Metadata directory featuring strict allowed translation targets
LANG_METADATA = {
    'th': {'name': 'Thai', 'flag': '🇹🇭'},
    'en': {'name': 'English', 'flag': '🇬🇧'},
    'ja': {'name': 'Japanese', 'flag': '🇯🇵'},
    'ko': {'name': 'Korean', 'flag': '🇰🇷'},
    'zh-cn': {'name': 'Chinese', 'flag': '🇨🇳'},
    'fr': {'name': 'French', 'flag': '🇫🇷'},
    'de': {'name': 'German', 'flag': '🇩🇪'},
    'es': {'name': 'Spanish', 'flag': '🇪🇸'}
}

def get_lang_label(lang_code: str) -> str:
    """Helper to construct readable names with emojis for UI elements."""
    code = lang_code.lower()
    if code in LANG_METADATA:
        return f"{LANG_METADATA[code]['name']} {LANG_METADATA[code]['flag']}"
    return f"{lang_code.upper()} 🌐"


# ==========================================
# 🔘 UI INTERACTION: TRANSLATION INVERTER VIEW
# ==========================================
class TranslateInvertView(discord.ui.View):
    def __init__(self, cog, source_lang: str, target_lang: str, current_text: str, user_id: int, is_ephemeral: bool = False):
        super().__init__(timeout=180.0)
        self.cog = cog
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.current_text = current_text
        self.user_id = user_id
        self.is_ephemeral = is_ephemeral
        self.message: Optional[discord.Message] = None

        self.invert_button.label = f"Swap to {get_lang_label(source_lang)}"

    @discord.ui.button(style=discord.ButtonStyle.secondary, emoji="🔄")
    async def invert_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Allows users to instantly swap destination and source targets via UI interaction."""
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ **Access Denied:** You cannot trigger this matrix.", ephemeral=True)
        
        # --- COOLDOWN GATEKEEPER CHECK ---
        is_restricted, retry_ts = self.cog.check_cooldown(interaction.user.id)
        if is_restricted:
            limit_embed = discord.Embed(
                title="🛡️ Rate Limit Boundary Triggered",
                description=(
                    f"❌ **Action Blocked:** You have consumed your allowed quota of **7 translations per 2 hours**.\n"
                    f"⌛ **Cooling Window Reset:** Your access matrix will restore <t:{retry_ts}:R> (<t:{retry_ts}:t>)."
                ),
                color=0xED4245
            )
            return await interaction.response.send_message(embed=limit_embed, ephemeral=True)

        await interaction.response.defer()
        
        new_source = self.target_lang
        new_target = "th" if self.source_lang.lower() == "auto" or self.source_lang == self.target_lang else self.source_lang

        # Enforce validation checks against inversion targets
        resolved_target = self.cog.resolve_lang_code(new_target)
        if resolved_target not in LANG_METADATA:
            return await interaction.followup.send("❌ **Inversion Failure:** Swept target falls outside of allowed language boundaries.", ephemeral=True)

        try:
            # 💡 แก้ไข: การสลับภาษาจากข้อความเดิม จะไม่นับเป็นการเพิ่ม Quota การใช้งานใหม่
            embed, view = await self.cog.execute_translation(
                target_lang=resolved_target,
                source_lang=new_source,
                text=self.current_text,
                user=interaction.user,
                is_ephemeral=self.is_ephemeral
            )
            
            # 🛠️ ปรับปรุงระบบ Smart Routing ให้แก้ไขข้อความได้ถูกต้องทั้งแบบธรรมดาและ Ephemeral
            if self.is_ephemeral or interaction.message.flags.ephemeral:
                await interaction.edit_original_response(embed=embed, view=view)
            else:
                await interaction.message.edit(embed=embed, view=view)
                
            view.message = self.message or interaction.message
        except Exception as e:
            await interaction.followup.send(f"❌ **Inversion Failure:** `{str(e)}`", ephemeral=True)

    @discord.ui.button(label="Get Raw Text", style=discord.ButtonStyle.success, emoji="📋")
    async def copy_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Sends the pure translated text inside an ephemeral code block for clean copying."""
        embed = interaction.message.embeds[0]
        # ดึงเอาเครื่องหมายจัดรูปแบบตัวหนาของข้อความแปลออกเพื่อให้ก๊อปปี้ง่ายขึ้น
        translated_raw = embed.fields[1].value.replace("**", "").strip()
        
        # 🛠️ แก้ไข Syntax Error จากจุดเดิมเรียบร้อยแล้ว
        await interaction.response.send_message(
            f"📋 **Copy-Paste Optimized Node:**\n```text\n{translated_raw}\n```", 
            ephemeral=True
        )

    async def on_timeout(self):
        """Safely clean up interactive node elements after deployment lifecycle expires."""
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        if self.message:
            try:
                # ตรวจสอบประเภท Message เพื่อป้องกันการ Edit หลุดพ้นขอบเขต
                if not self.message.flags.ephemeral:
                    await self.message.edit(view=self)
            except discord.HTTPException:
                pass


# ==========================================
# 🌐 CORE TRANSLATION COG COMPONENT
# ==========================================
class UtilityTranslate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Sliding history queue tracker tracking individual translation user requests
        self._cooldown_matrix = {}

        self.ctx_menu = app_commands.ContextMenu(
            name="Translate to English",
            callback=self.context_translate_to_english
        )
        self.bot.tree.add_command(self.ctx_menu)

    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def cog_unload(self):
        self.bot.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)
        if self._session and not self._session.closed:
            self.bot.loop.create_task(self._session.close())

    def resolve_lang_code(self, lang: str) -> str:
        """Normalizes explicit string variations down to system-recognized keys."""
        lang_map = {
            'thai': 'th', 'th': 'th',
            'english': 'en', 'en': 'en', 'eng': 'en',
            'japan': 'ja', 'japanese': 'ja', 'ja': 'ja',
            'korea': 'ko', 'korean': 'ko', 'ko': 'ko',
            'china': 'zh-cn', 'chinese': 'zh-cn', 'zh': 'zh-cn', 'cn': 'zh-cn', 'zh-cn': 'zh-cn',
            'france': 'fr', 'french': 'fr', 'fr': 'fr',
            'german': 'de', 'germany': 'de', 'de': 'de',
            'spanish': 'es', 'spain': 'es', 'es': 'es'
        }
        return lang_map.get(lang.lower(), lang.lower())

    def check_cooldown(self, user_id: int) -> tuple[bool, int]:
        """Cleans stale timestamps and evaluates if user profile hits the 7 uses / 2-hour window limit."""
        now = int(time.time())
        two_hours_ago = now - 7200

        if user_id not in self._cooldown_matrix:
            return False, 0

        # Discard records that are older than the 2-hour sliding window
        self._cooldown_matrix[user_id] = [ts for ts in self._cooldown_matrix[user_id] if ts > two_hours_ago]

        if len(self._cooldown_matrix[user_id]) >= 7:
            # Predict execution reset timestamp based on the oldest expiration node
            oldest_execution = self._cooldown_matrix[user_id][0]
            restoration_epoch = oldest_execution + 7200
            return True, restoration_epoch

        return False, 0

    def log_usage(self, user_id: int):
        """Appends a new epoch checkpoint into the active tracking window arrays."""
        now = int(time.time())
        if user_id not in self._cooldown_matrix:
            self._cooldown_matrix[user_id] = []
        self._cooldown_matrix[user_id].append(now)

    async def execute_translation(self, target_lang: str, source_lang: str, text: str, user, is_ephemeral: bool = False) -> tuple[discord.Embed, discord.ui.View]:
        """Core translation backend parser."""
        actual_target = self.resolve_lang_code(target_lang)
        actual_source = self.resolve_lang_code(source_lang)
        
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            'client': 'gtx',
            'sl': actual_source,
            'tl': actual_target,
            'dt': 't',
            'q': text
        }
        
        session = await self.get_session()
        async with session.get(url, params=params, timeout=10) as response:
            if response.status != 200:
                raise Exception("Unable to reach Google Translation service pipelines.")
            
            data = await response.json()
            translated_text = ""
            detected_source = data[2] if len(data) > 2 else actual_source
            
            for sentence in data[0]:
                if sentence[0]:
                    translated_text += sentence[0]
            
            if not translated_text.strip():
                raise Exception("Could not extract meaningful structural translated outputs.")
            
            src_text = text if len(text) <= 1000 else text[:997] + "..."
            dst_text = translated_text if len(translated_text) <= 1000 else translated_text[:997] + "..."
            
            src_label = get_lang_label(detected_source)
            dst_label = get_lang_label(actual_target)

            embed = discord.Embed(color=0x3498DB, timestamp=utcnow())
            embed.set_author(name="Google Translate Engine", icon_url="https://upload.wikimedia.org/wikipedia/commons/d/d7/Google_Translate_logo.svg")
            
            embed.add_field(name=f"📝 Original Content ({src_label})", value=f"```text\n{src_text}\n```", inline=False)
            embed.add_field(name=f"✨ Translated Output ({dst_label})", value=f"**{dst_text}**", inline=False)
            embed.set_footer(text=f"Requested by {user.display_name}", icon_url=user.display_avatar.url)
            
            view = TranslateInvertView(
                self, 
                source_lang=detected_source, 
                target_lang=actual_target, 
                current_text=text, 
                user_id=user.id,
                is_ephemeral=is_ephemeral
            )
            return embed, view

    # 🌐 METHOD A: SLASH/HYBRID SYSTEM EXECUTION NODE
    @commands.hybrid_command(
        name="translate",
        aliases=["tr", "trans"],
        description="🌐 Translate phrases smoothly into restricted target language scopes."
    )
    @app_commands.describe(
        target_lang="Destination language code ( th, en, ja, ko, fr, de, es, zh-cn )",
        text="The text payload to translate"
    )
    @commands.guild_only()
    async def translate_command(self, ctx: commands.Context, target_lang: str, *, text: str):
        """Intercepts translation inputs, checks limits, and handles core execution routing maps."""
        resolved_target = self.resolve_lang_code(target_lang)

        # Enforce strict system-wide whitelisted language validation checks
        if resolved_target not in LANG_METADATA:
            allowed_list = ", ".join([f"`{k}` ({v['name']})" for k, v in LANG_METADATA.items()])
            err_embed = discord.Embed(
                title="❌ Target Specification Rejected",
                description=f"Target language code selection falls outside bounds.\n**Supported Options:** {allowed_list}",
                color=0xE74C3C
            )
            return await ctx.send(embed=err_embed, ephemeral=True)

        # --- RATELIMIT FILTER CHECK ---
        is_restricted, retry_ts = self.check_cooldown(ctx.author.id)
        if is_restricted:
            limit_embed = discord.Embed(
                title="🛡️ Rate Limit Boundary Triggered",
                description=(
                    f"❌ **Action Blocked:** You have consumed your allowed quota of **7 translations per 2 hours**.\n"
                    f"⌛ **Cooling Window Reset:** Your access matrix will restore <t:{retry_ts}:R> (<t:{retry_ts}:t>)."
                ),
                color=0xED4245
            )
            return await ctx.send(embed=limit_embed, ephemeral=True)

        await ctx.defer()
        try:
            # Register quota consumption metric entry
            self.log_usage(ctx.author.id)

            embed, view = await self.execute_translation(resolved_target, "auto", text, ctx.author, is_ephemeral=False)
            msg = await ctx.send(embed=embed, view=view)
            view.message = msg
        except Exception as e:
            err_embed = discord.Embed(description=f"❌ **Translation Error:** `{str(e)}`", color=0xE74C3C)
            await ctx.send(embed=err_embed)

    # 🖱️ METHOD B: RIGHT-CLICK CONTEXT MENU APP EXECUTION NODE
    async def context_translate_to_english(self, interaction: discord.Interaction, message: discord.Message):
        """Shortcut action routing system enabling quick message translation to English via right-click."""
        if not message.content or not message.content.strip():
            return await interaction.response.send_message("❌ **Context Error:** Selected target element contains no raw text properties.", ephemeral=True)

        # --- RATELIMIT FILTER CHECK ---
        is_restricted, retry_ts = self.check_cooldown(interaction.user.id)
        if is_restricted:
            limit_embed = discord.Embed(
                title="🛡️ Rate Limit Boundary Triggered",
                description=(
                    f"❌ **Action Blocked:** You have consumed your allowed quota of **7 translations per 2 hours**.\n"
                    f"⌛ **Cooling Window Reset:** Your access matrix will restore <t:{retry_ts}:R> (<t:{retry_ts}:t>)."
                ),
                color=0xED4245
            )
            return await interaction.response.send_message(embed=limit_embed, ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        try:
            self.log_usage(interaction.user.id)

            embed, view = await self.execute_translation("en", "auto", message.content, interaction.user, is_ephemeral=True)
            msg = await interaction.followup.send(embed=embed, view=view, ephemeral=True)
            view.message = msg
        except Exception as e:
            err_embed = discord.Embed(description=f"❌ **Context Translation Failure:** `{str(e)}`", color=0xE74C3C)
            await interaction.followup.send(embed=err_embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(UtilityTranslate(bot))
