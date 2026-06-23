import discord
from discord.ext import commands
from discord import app_commands
import random
import re
from typing import Optional
from discord.utils import utcnow

class DiceRoller(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # คอมไพล์ Regex Pattern รองรับรูปแบบ XdY หรือ XdY+Z และ XdY-Z
        self.dice_pattern = re.compile(r'^(\d+)d(\d+)(?:([+-])(\d+))?$', re.IGNORECASE)

    @commands.hybrid_command(name="roll", aliases=["dice", "r"])
    @app_commands.describe(formula="The dice formula to roll (e.g., 1d6, 2d20+5). Leave blank for 1d20.")
    @commands.guild_only()
    async def roll(self, ctx: commands.Context, formula: Optional[str] = "1d20"):
        """🎲 Roll dice using standard notation (e.g., 1d20, 2d6+3). Defaults to 1d20."""
        await ctx.defer()
        
        # ปรับค่าให้อยู่ในรูปแบบพิมพ์เล็กและตัดเว้นวรรคออกทั้งหมด
        formula = formula.replace(" ", "").lower()
        match = self.dice_pattern.match(formula)
        
        if not match:
            embed_err = discord.Embed(
                description="<:No:1517480787744784475> **Syntax Error:** Invalid notation. Please use `XdY` (e.g., `1d20`, `2d10+5`).",
                color=0xE74C3C
            )
            return await ctx.interaction.followup.send(embed=embed_err, ephemeral=True)
            
        dice_count = int(match.group(1))
        dice_sides = int(match.group(2))
        modifier_sign = match.group(3)
        modifier_value = int(match.group(4)) if match.group(4) else 0
        
        # Security Constraints: ป้องกันไม่ให้แอดมินหรือผู้ใช้สั่งทอยเยอะเกินไปจนบอทแลค
        if not (1 <= dice_count <= 100) or not (2 <= dice_sides <= 1000):
            embed_err = discord.Embed(
                description="<:No:1517480787744784475> **Range Error:** You can only roll 1-100 dice with 2-1000 sides each.",
                color=0xE74C3C
            )
            return await ctx.interaction.followup.send(embed=embed_err, ephemeral=True)
            
        # เริ่มกระบวนการสุ่มตัวเลขเต๋า
        rolls = [random.randint(1, dice_sides) for _ in range(dice_count)]
        base_sum = sum(rolls)
        
        # ประมวลผลคณิตศาสตร์ร่วมกับ Modifier
        if modifier_sign == '+':
            total_sum = base_sum + modifier_value
            mod_display = f" + {modifier_value}"
        elif modifier_sign == '-':
            total_sum = base_sum - modifier_value
            mod_display = f" - {modifier_value}"
        else:
            total_sum = base_sum
            mod_display = ""

        # Embed Visualization
        embed = discord.Embed(
            title="🎲 Dice Roll Results",
            color=0x9B59B6,
            timestamp=utcnow()
        )
        
        # ตัดลิสต์ประวัติเต๋าเพื่อความสะอาดของ UI ไม่ให้ Embed บวมเกินไป
        rolls_str = ", ".join(map(str, rolls))
        display_rolls = rolls_str if len(rolls_str) < 500 else f"{rolls_str[:497]}..."

        # สร้างข้อความ Breakdown แตกโครงสร้างสูตร
        sampled_rolls = " + ".join(map(str, rolls[:10]))
        ellipsis_str = " + ..." if dice_count > 10 else ""
        breakdown_value = f"`({sampled_rolls}{ellipsis_str}){mod_display}`"

        embed.add_field(name="Formula", value=f"`{formula}`", inline=True)
        embed.add_field(name="Result", value=f"**` {total_sum:,} `**", inline=True)
        embed.add_field(name="Breakdown", value=breakdown_value, inline=False)
        embed.add_field(name="Individual Rolls", value=f"```json\n[{display_rolls}]\n```", inline=False) # แก้ไข Syntax เรียบร
        
        embed.set_footer(
            text=f"Initiated by {ctx.author.name}",
            icon_url=ctx.author.display_avatar.url
        )
        
        # หลังจากสั่ง defer() ต้องตอบกลับด้วย followup.send เสมอ
        await ctx.interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(DiceRoller(bot))
