import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import re
from typing import Optional

# =======================================================
# 🎨 COLOR SPECTRUM BLEND & MODIFIER PARSER ENGINE
# =======================================================
class ColorSpectrumEngine:
    """Foundational Color Space Registry and Blending Matrix."""
    
    # Base color spaces defined as RGB vectors
    BASE_COLORS = {
        'white': (255, 255, 255),
        'black': (0, 0, 0),
        'red': (255, 0, 0),
        'green': (0, 255, 0),
        'blue': (0, 0, 255),
        'yellow': (255, 255, 0),
        'purple': (128, 0, 128),
        'orange': (255, 165, 0),
        'pink': (255, 192, 203),
        'cyan': (0, 255, 255),
        'grey': (128, 128, 128),
        'gray': (128, 128, 128),
        'blurple': (88, 101, 242)
    }

    # Weight modifiers for shading and tonal adjustments
    MODIFIERS = {
        'light': {'target': 'white', 'weight': 0.35},
        'pale': {'target': 'white', 'weight': 0.45},
        'dark': {'target': 'black', 'weight': 0.35},
        'deep': {'target': 'black', 'weight': 0.45},
        'bright': {'target': None, 'weight': 1.2}  # Boosts saturation vectors
    }

    @classmethod
    def blend_colors(cls, rgb1: tuple, rgb2: tuple, weight: float) -> tuple:
        """Applies linear interpolation vectors to blend two color nodes together."""
        r = int(rgb1[0] * (1 - weight) + rgb2[0] * weight)
        g = int(rgb1[1] * (1 - weight) + rgb2[1] * weight)
        b = int(rgb1[2] * (1 - weight) + rgb2[2] * weight)
        return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

    @classmethod
    def interpret_natural_color(cls, raw_input: str) -> Optional[str]:
        """Tokenizes descriptive text strings and handles complex blending arrays."""
        tokens = raw_input.strip().lower().replace('-', ' ').split()
        if not tokens:
            return None

        active_rgb = None
        active_modifiers = []

        # Step 1: Extract structure and distinguish primary bases from blended modifiers
        for token in tokens:
            # Check for blended compound colors (e.g., 'blackish', 'pinkish')
            clean_token = re.sub(r'(ish|y)$', '', token)
            
            if token in cls.MODIFIERS:
                active_modifiers.append(cls.MODIFIERS[token])
            elif token in cls.BASE_COLORS:
                active_rgb = cls.BASE_COLORS[token]
            elif clean_token in cls.BASE_COLORS:
                # Compound modifier blend target discovered (e.g. "blackish" means 40% black tint)
                blend_target = cls.BASE_COLORS[clean_token]
                if active_rgb is None:
                    # Fallback default value initialization
                    active_rgb = cls.BASE_COLORS['white']
                active_rgb = cls.blend_colors(active_rgb, blend_target, 0.40)

        # Fail out early if no foundational color anchor is recognized
        if not active_rgb:
            return None

        # Step 2: Calculate adjustments for tint/shade modifiers (e.g., 'light', 'dark')
        for mod in active_modifiers:
            if mod['target'] == 'white':
                active_rgb = cls.blend_colors(active_rgb, (255, 255, 255), mod['weight'])
            elif mod['target'] == 'black':
                active_rgb = cls.blend_colors(active_rgb, (0, 0, 0), mod['weight'])
            elif mod['target'] is None:  # Brightness amplification boost
                active_rgb = tuple(max(0, min(255, int(channel * mod['weight']))) for channel in active_rgb)

        # Convert the processed vector directly to a standard Hex string
        return f"{active_rgb[0]:02X}{active_rgb[1]:02X}{active_rgb[2]:02X}"


# =======================================================
# 🤖 DISCORD COG MODULE ENGINE
# =======================================================
class Color(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._session: Optional[aiohttp.ClientSession] = getattr(bot, "session", None)

    async def _get_session(self) -> aiohttp.ClientSession:
        """Retrieves or provisions a structured ClientSession Singleton framework."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    def expand_short_hex(self, hex_code: str) -> str:
        """Expands short 3-digit hex structures to full 6-digit layouts."""
        if len(hex_code) == 3:
            return "".join(c * 2 for c in hex_code)
        return hex_code

    @commands.hybrid_command(
        name="color", 
        aliases=["colour", "hexinfo", "rgb"],
        description="🎨 Fetch comprehensive color space telemetry and interpret custom descriptive blends."
    )
    @app_commands.describe(color="Provide Hex (#FF5733), Integer IDs, or descriptive text (e.g., 'light pink', 'blackish white').")
    async def color_command(self, ctx: commands.Context, *, color: str):
        """🎨 Displays multi-space visual telemetry data for any specified color."""
        await ctx.defer()

        cleaned_input = color.strip().lstrip('#')
        
        # 1. Route descriptive text queries through the Spectrum Interpretation Engine
        interpreted_hex = ColorSpectrumEngine.interpret_natural_color(cleaned_input)
        
        if interpreted_hex:
            cleaned_color = interpreted_hex
        else:
            # Fallback to structural evaluations if raw input represents numeric parameters
            if cleaned_input.isdigit() and len(cleaned_input) > 5:
                try:
                    cleaned_input = hex(int(cleaned_input))[2:].zfill(6)
                except ValueError:
                    pass

            cleaned_color = self.expand_short_hex(cleaned_input)

        # Validate structured hex syntax formatting via Regex boundaries
        if not re.match(r"^[0-9a-fA-F]{6}$", cleaned_color):
            return await ctx.send(
                "<:No:1517480787744784475> **Parsing Error:** Invalid color input format specified. "
                "Use Hex (`#FF5733`), Short Hex (`#F57`), or descriptions like `light pink` or `blackish white`."
            )

        cleaned_color = cleaned_color.upper()

        # 2. Async HTTP Request Payload Retrieval
        api_url = f"https://www.thecolorapi.com/id?hex={cleaned_color}"
        try:
            session = await self._get_session()
            async with session.get(api_url, timeout=10) as response:
                if response.status != 200:
                    return await ctx.send("<:No:1517480787744784475> **API Connection Failed:** External color repository returned a bad response.")
                data = await response.json()
        except Exception as e:
            return await ctx.send(f"<:No:1517480787744784475> **Telemetry Error:** Failed to establish handshake with global repository matrix. (`{type(e).__name__}`)")

        # 3. Telemetry Extraction & Data Normalization
        color_name = data.get("name", {}).get("value", "Unknown Designation")
        is_exact = "Exact Match" if data.get("name", {}).get("exact_match_with_hex", False) else "Closest Approximation"
        
        clean_val = lambda space: data.get(space, {}).get("value", "N/A").replace(f"{space}(", "").replace(")", "")
        
        rgb_str = clean_val("rgb")
        hsv_str = clean_val("hsv")
        hsl_str = clean_val("hsl")
        cmyk_str = clean_val("cmyk")
        
        try:
            int_value = int(cleaned_color, 16)
        except ValueError:
            int_value = 0

        contrast_hex = data.get("contrast", {}).get("value", "#FFFFFF").lstrip('#').upper()

        # 4. Constructing Advanced Matrix Embed Presentation
        embed = discord.Embed(
            title=f"🎨 Color Profile Matrix • {color_name}",
            description=f"Analytical framework detailing properties of interpreted Hex: `#{cleaned_color}`\n*Parsed from input:* `{color}`",
            color=int_value if int_value <= 0xFFFFFF else 0x000000,
            timestamp=discord.utils.utcnow()
        )
        
        swatch_url = f"https://singlecolorimage.com/get/{cleaned_color}/200x200"
        embed.set_thumbnail(url=swatch_url)

        embed.add_field(
            name="🆔 Core Taxonomy",
            value=(
                f"> **Designation:** `{color_name}`\n"
                f"> **Classification:** `{is_exact}`\n"
                f"> **Integer Registry:** `{int_value:,}`"
            ),
            inline=False
        )

        embed.add_field(
            name="📊 Screen & Digital Spaces",
            value=(
                f"> **HEX Code:** `#{cleaned_color}`\n"
                f"> **RGB Array:** `rgb({rgb_str})`\n"
                f"> **HSV Relay:** `hsv({hsv_str})`\n"
                f"> **HSL Vector:** `hsl({hsl_str})`"
            ),
            inline=True
        )

        embed.add_field(
            name="🖨️ Print & Design Systems",
            value=(
                f"> **CMYK Node:** `cmyk({cmyk_str})`\n"
                f"> **Contrast Hex:** `#{contrast_hex}`\n"
                f"> **Contrast Node:** [Visual Link](https://singlecolorimage.com/get/{contrast_hex}/100x100)"
            ),
            inline=True
        )

        embed.add_field(
            name="🔮 Creative Utility Insight",
            value=f"To optimize structural readability or interface contrast alongside `#{cleaned_color}`, integrate its designated opposite contrast element: **`#{contrast_hex}`**.",
            inline=False
        )

        embed.set_footer(
            text=f"Color Engine Node • Requested by {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Color(bot))
