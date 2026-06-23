import discord
from discord import app_commands
from discord.ext import commands
import math
import re
import time

# ==========================================
# 📊 UTILITY: SPECIAL CHARACTER TRANSLATOR
# ==========================================
def normalize_special_characters(expression: str) -> str:
    """Translates superscripts, fractions, and strips global currency nodes."""
    expr = expression
    
    # 1. Superscript Translations
    superscripts = {'⁰': '^0', '¹': '^1', '²': '^2', '³': '^3', '⁴': '^4', 
                    '⁵': '^5', '⁶': '^6', '⁷': '^7', '⁸': '^8', '⁹': '^9', 'ⁿ': '**n'}
    for super_char, normal_char in superscripts.items():
        expr = expr.replace(super_char, normal_char)
        
    # 2. Fraction Translations
    fractions = {'½': '(1/2)', '⅓': '(1/3)', '¼': '(1/4)', '⅕': '(1/5)', '⅙': '(1/6)', 
                 '⅐': '(1/7)', '⅛': '(1/8)', '⑨': '(1/9)', '⅒': '(1/10)'}
    for frac_char, normal_char in fractions.items():
        expr = expr.replace(frac_char, normal_char)

    # 3. Currency Symbols Auto-Strip (Ignore purely for evaluations)
    currencies = ['฿', '$', '¢', '€', '£', '₱', '¥', '₹']
    for currency in currencies:
        expr = expr.replace(currency, '')
        
    # 4. Math Set & Special Constants Nullification
    expr = expr.replace('∅', '0')
    
    return expr


# ==========================================
# 🗔 UI DIALOG ENGINE: MODAL INTERFACES
# ==========================================
class CalculatorModal(discord.ui.Modal):
    def __init__(self, mode: str):
        super().__init__(title=f"📐 Core Analytical Engine - {mode}")
        self.mode = mode
        
        self.expression_input = discord.ui.TextInput(
            label="Enter Mathematical Expression",
            placeholder="e.g., (5km / 2h) * 10² or sin(π/4) * sqrt(16)",
            style=discord.TextStyle.short,
            required=True,
            max_length=200
        )
        self.add_item(self.expression_input)

    def analyze_complexity(self, expression: str) -> tuple[int, int, str]:
        """Performs lexical and structural analysis of the mathematical string."""
        current_depth = max_depth = 0
        for char in expression:
            if char == '(':
                current_depth += 1
                if current_depth > max_depth:
                    max_depth = current_depth
            elif char == ')':
                current_depth = max(0, current_depth - 1)

        operators = re.findall(r'[+\-*/%^√]|sqrt|sin|cos|tan|log|ln|pow|factorial', expression)
        operator_count = len(operators)

        if any(x in expression for x in ["sin", "cos", "tan"]):
            domain = "Trigonometry Field"
        elif any(x in expression for x in ["log", "log10", "ln"]):
            domain = "Logarithmic System"
        elif any(x in expression for x in ["c", "g_earth"]):
            domain = "Physics Constants Matrix"
        elif "n" in expression or "pow" in expression or "^" in expression:
            domain = "Algebra / Polynomial"
        else:
            domain = "Foundational Arithmetic"

        return max_depth, operator_count, domain

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        raw_input = self.expression_input.value
        start_time = time.perf_counter()

        # Translate special mathematical characters and remove whitespace
        translated_expr = normalize_special_characters(raw_input)
        clean_expr = translated_expr.replace(" ", "").lower()

        bracket_depth, op_count, math_domain = self.analyze_complexity(clean_expr)

        # Unit Matrix metrics conversions using comprehensive safe patterns
        clean_expr = re.sub(r'(\d+(\.\d+)?)(cm)\b', r'(\1*0.01)', clean_expr)
        clean_expr = re.sub(r'(\d+(\.\d+)?)(km)\b', r'(\1*1000)', clean_expr)
        clean_expr = re.sub(r'(\d+(\.\d+)?)(g)\b', r'(\1*0.001)', clean_expr)
        clean_expr = clean_expr.replace("÷", "/").replace("×", "*").replace("℅", "*0.01")
        
        # Standardize square root structures
        clean_expr = re.sub(r'√\(([^)]+)\)', r'sqrt(\1)', clean_expr)
        clean_expr = re.sub(r'√(\d+(\.\d+)?)', r'sqrt(\1)', clean_expr)

        # Mathematical Sandbox evaluation rules configuration
        safe_dict = {
            "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "log": math.log, "log10": math.log10, "ln": math.log, "abs": abs,
            "round": round, "pow": pow, "factorial": math.factorial,
            "pi": math.pi, "π": math.pi, "e": math.e,
            "inf": float('inf'), "∞": float('inf'), "n": 5,
            "c": 299792458, "g_earth": 9.80665
        }

        processed_expr = clean_expr.replace("^", "**")

        # Core operational security firewall filter layout validation
        allowed_words = list(safe_dict.keys())
        whitelist_pattern = re.compile(r'^([0-9.+\-*/()%\s]|' + '|'.join(allowed_words) + r')+$')

        if not whitelist_pattern.match(processed_expr):
            embed_warn = discord.Embed(
                title="🛡️ Security Firewall Triggered",
                description=f"❌ **Execution Blocked:** Unauthorized logic parameters or symbols detected inside calculation request.\n`Your Input: {raw_input}`",
                color=0xED4245
            )
            return await interaction.followup.send(embed=embed_warn, ephemeral=True)

        try:
            # Execution processing via standard python logic mapping sandbox
            result = eval(processed_expr, {"__builtins__": {}}, safe_dict)
            
            if isinstance(result, float):
                if result.is_integer(): result = int(result)
                elif math.isinf(result): result = "∞ (Infinity)"
                elif math.isnan(result): result = "NaN (Undefined)"
                else: result = round(result, 8)

            result_display = f"{result:,}" if isinstance(result, int) and result < 1e15 else str(result)
            calculation_time = round((time.perf_counter() - start_time) * 1000, 4)

            # Build Advanced Matrix Analytical Telemetry Table
            metrics_table = (
                f"```\n"
                f"┌──────────────────────┬──────────────────────────────────┐\n"
                f"│ METRIC ENGINE KEY    │ DATA MATRIX VALUE                │\n"
                f"├──────────────────────┼──────────────────────────────────┤\n"
                f"│ Raw Input Token      │ {raw_input[:30]:<32} │\n"
                f"│ Computed Output      │ {result_display[:30]:<32} │\n"
                f"│ Processing Latency   │ {f'{calculation_time} ms':<32} │\n"
                f"│ Core Operational Mode│ {self.mode:<32} │\n"
                f"└──────────────────────┴──────────────────────────────────┘\n"
                f"```"
            )

            analytical_breakdown = []
            if self.mode == "DEEP_ANALYTICS":
                analytical_breakdown.append(f"📡 **Mathematical Domain Classification:** `{math_domain}`")
                analytical_breakdown.append(f"🧮 **Token Operator Concentration:** Loaded `{op_count}` operational components.")
                analytical_breakdown.append(f"⛓️ **Maximum Structural Nesting Depth:** `{bracket_depth}` layered parentheses levels deep.")
            else:
                analytical_breakdown.append("📊 **Standard Analysis Engine:** Comprehensive telemetry matrices are loaded above.")

            execution_order = []
            if "(" in raw_input:
                execution_order.append("• **Parentheses Priority:** Resolved isolated calculations embedded inside brackets `()` first.")
            if any(x in clean_expr for x in ["sqrt", "**", "pow"]):
                execution_order.append("• **Radical / Power Matrix:** Evaluated algorithmic exponents, roots (`√`), or exponential elements.")
            if any(x in clean_expr for x in ["*", "/"]):
                execution_order.append("• **Products & Quotients:** Computed structural multiplication and division pipelines from left-to-right.")
            if any(x in clean_expr for x in ["+", "-"]):
                execution_order.append("• **Summation Chains:** Unified standard linear values using standard addition and subtraction operations.")
                
            if not execution_order:
                execution_order.append("• **Direct Arithmetic Reduction:** Resolved flat linear components instantly via foundational logic processing.")

            analysis_output = "\n".join(analytical_breakdown)
            roadmap_output = "\n".join(execution_order)

            embed = discord.Embed(
                title=f"🧮 Advanced Mathematical Processing Unit [{self.mode}]",
                color=0x5865F2 if self.mode == "STANDARD_COMPUTE" else 0x9B59B6,
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(name="📋 Accurate System Metric Parameters", value=metrics_table, inline=False)
            embed.add_field(name="🔬 Numerical Lexical Analysis Registry", value=analysis_output, inline=False)
            embed.add_field(name="🛠️ Algorithmic Procedural Roadmap", value=roadmap_output, inline=False)
            embed.set_footer(text="RzBot Compute Core Engine Framework")

            await interaction.followup.send(embed=embed)

        except ZeroDivisionError:
            await interaction.followup.send("❌ **Calculation Error:** Division by zero is undefined mathematical nonsense.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ **System Processing Fault:** `{str(e)}`", ephemeral=True)


# ==========================================
# 🔘 UI BUTTON MATRIX SYSTEM
# ==========================================
class CalculatorModeSelectionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="Standard Compute", style=discord.ButtonStyle.secondary, emoji="🧠")
    async def standard_compute_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CalculatorModal(mode="STANDARD_COMPUTE"))

    @discord.ui.button(label="Deep Analytical Matrix", style=discord.ButtonStyle.primary, emoji="🔬")
    async def deep_analytical_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CalculatorModal(mode="DEEP_ANALYTICS"))

    @discord.ui.button(label="Guide & Documentation", style=discord.ButtonStyle.success, emoji="📖")
    async def guide_documentation_click(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Displays localized engine rules and acceptable mathematical values."""
        embed = discord.Embed(
            title="📖 Kitsumi Core Engine: Guide Matrix",
            description="Official comprehensive reference guide outlining parameters, constants, and character indexes supported by the system.",
            color=0x2ECC71
        )
        
        embed.add_field(
            name="📊 1. Supported Mathematical Functions",
            value="• `sqrt(x)` or `√x` : Resolves square root operations.\n"
                  "• `pow(x, y)` or `x^y` : Computes dynamic exponential power matrices.\n"
                  "• `sin(x)`, `cos(x)`, `tan(x)` : Core standard trigonometry configurations.\n"
                  "• `log(x)`, `log10(x)`, `ln(x)` : Advanced logarithmic processing protocols.\n"
                  "• `factorial(x)` : Calculates full factorial integers.",
            inline=False
        )
        
        embed.add_field(
            name="🛰️ 2. Constants & Scientific Parameters",
            value="• `pi` or `π` : Ratio of a circle's circumference ($\approx 3.14159$)\n"
                  "• `e` : Euler's natural logarithm constant ($\approx 2.71828$)\n"
                  "• `c` : Constant speed of light in a vacuum ($299,792,458\\text{ m/s}$)\n"
                  "• `g_earth` : Earth's gravitational coefficient acceleration standard ($9.80665\\text{ m/s}^2$)\n"
                  "• `n` : Generic variable constant index (Default value initialized to `5`).",
            inline=False
        )

        embed.add_field(
            name="🕰️ 3. Character Indices & Metric Scale Translations",
            value="The parsing workflow intercepts syntax layouts and auto-scales metrics based on standard systems:\n"
                  "• **Automatic Metric Converters:** Numeric values trailing unit tokens convert into direct base definitions:\n"
                  "  - `km` (Kilometers conversion factor) $\\rightarrow$ evaluated as ($*1000$).\n"
                  "  - `cm` (Centimeters conversion factor) $\\rightarrow$ evaluated as ($*0.01$).\n"
                  "  - `g` (Grams conversion weight factor) $\\rightarrow$ evaluated as ($*0.001$).\n"
                  "• **Superscripts & Nested Fraction Filters:** Compact superscripts like `⁵` translate to `^5`, and compact layout symbols like `½` translate into balanced equations `(1/2)` prior to engine deployment.",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


# ==========================================
# 🤖 DISCORD COG MODULE ENGINE
# ==========================================
class Calculator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="calc",
        description="🧮 Process high-resolution mathematics via Standard or Deep Analytical systems."
    )
    async def calculator_hub(self, ctx: commands.Context):
        """Initial core gateway rendering interactive options for localized execution layers."""
        embed = discord.Embed(
            title="🧮 Kitsumi Mathematical Control Core",
            description=(
                "Select your desired execution and calculation node mapping below:\n\n"
                "🧠 **Standard Compute:** Regular calculations delivering processing speeds, error checking, and layout tracking.\n"
                "🔬 **Deep Analytical Matrix:** Runs complex algorithmic token telemetry, categorizes math domains, and calculates execution density grids.\n"
                "📖 **Guide & Documentation:** View comprehensive functional protocols and token registry definitions."
            ),
            color=0x2F3136
        )
        view = CalculatorModeSelectionView()
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Calculator(bot))
