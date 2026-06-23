import discord
from discord.ext import commands
from discord import app_commands
import random
from discord.utils import utcnow

class GuessView(discord.ui.View):
    def __init__(self, ctx: commands.Context, target: int, max_num: int):
        super().__init__(timeout=120.0)
        self.ctx = ctx
        self.target = target
        self.max_num = max_num
        self.attempts = 0
        self.max_attempts = 10
    
    @discord.ui.button(label="Make a Guess", style=discord.ButtonStyle.blurple, emoji="🎯")
    async def guess_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("❌ This isn't your game!", ephemeral=True)
            return
        
        # Create modal for input
        modal = GuessModal(self)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Give Up", style=discord.ButtonStyle.red, emoji="🏳️")
    async def giveup_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("❌ This isn't your game!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🏳️ Game Over - You Gave Up",
            description=f"The number was **{self.target}**\n\nYou made **{self.attempts}** attempts.",
            color=0x95A5A6,
            timestamp=utcnow()
        )
        embed.set_footer(text=f"Player: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        self.stop()


class GuessModal(discord.ui.Modal):
    def __init__(self, view: GuessView):
        super().__init__(title="🎯 Make Your Guess")
        self.view = view
        
        self.guess_input = discord.ui.TextInput(
            label=f"Enter a number (1-{view.max_num})",
            placeholder="Type your guess here...",
            required=True,
            max_length=len(str(view.max_num))
        )
        self.add_item(self.guess_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            guess = int(self.guess_input.value)
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number!", ephemeral=True)
            return
        
        if guess < 1 or guess > self.view.max_num:
            await interaction.response.send_message(
                f"❌ Number must be between 1 and {self.view.max_num}!",
                ephemeral=True
            )
            return
        
        self.view.attempts += 1
        
        # Check if correct
        if guess == self.view.target:
            embed = discord.Embed(
                title="🎉 Correct! You Win!",
                description=(
                    f"**The number was {self.view.target}!**\n\n"
                    f"🎯 You guessed it in **{self.view.attempts}** attempts!\n"
                    f"{'⭐' * min(5, 11 - self.view.attempts)} Perfect!"
                ),
                color=0x57F287,
                timestamp=utcnow()
            )
            
            # Calculate score
            score = max(0, 1000 - (self.view.attempts * 100))
            embed.add_field(name="🏆 Score", value=f"`{score}` points", inline=True)
            embed.add_field(name="📊 Attempts", value=f"`{self.view.attempts}`", inline=True)
            
            embed.set_footer(
                text=f"Player: {interaction.user.name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            for item in self.view.children:
                item.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self.view)
            self.view.stop()
        
        elif self.view.attempts >= self.view.max_attempts:
            embed = discord.Embed(
                title="💥 Game Over - Out of Attempts",
                description=f"The number was **{self.view.target}**\n\nYou used all **{self.view.max_attempts}** attempts!",
                color=0xED4245,
                timestamp=utcnow()
            )
            embed.set_footer(
                text=f"Player: {interaction.user.name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            for item in self.view.children:
                item.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self.view)
            self.view.stop()
        
        else:
            # Give hints
            diff = abs(guess - self.view.target)
            
            if diff <= 5:
                hint = "🔥 **Very Hot!** You're super close!"
                color = 0xED4245
            elif diff <= 10:
                hint = "♨️ **Hot!** You're getting close!"
                color = 0xF26522
            elif diff <= 20:
                hint = "🌡️ **Warm!** You're on the right track!"
                color = 0xFEE75C
            elif diff <= 30:
                hint = "❄️ **Cold!** Not quite there yet!"
                color = 0x5865F2
            else:
                hint = "🧊 **Freezing!** Way off!"
                color = 0x95A5A6
            
            direction = "📈 Too low!" if guess < self.view.target else "📉 Too high!"
            
            embed = discord.Embed(
                title=f"❌ Wrong Guess: {guess}",
                description=f"{direction}\n{hint}",
                color=color,
                timestamp=utcnow()
            )
            
            embed.add_field(
                name="📊 Attempts Left",
                value=f"`{self.view.max_attempts - self.view.attempts}` / {self.view.max_attempts}",
                inline=True
            )
            embed.add_field(
                name="🎯 Range",
                value=f"1 - {self.view.max_num}",
                inline=True
            )
            
            embed.set_footer(
                text=f"Player: {interaction.user.name}",
                icon_url=interaction.user.display_avatar.url
            )
            
            await interaction.response.edit_message(embed=embed, view=self.view)


class Guess(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name="guess")
    @commands.guild_only()
    async def guess(self, ctx: commands.Context, max_number: int = 100):
        """🎯 Guess the number! Can you find it?
        
        Parameters:
        - max_number: Maximum number to guess (default: 100)
        """
        if max_number < 10:
            return await ctx.send("❌ Maximum number must be at least 10!")
        
        if max_number > 10000:
            return await ctx.send("❌ Maximum number can't exceed 10,000!")
        
        target = random.randint(1, max_number)
        
        embed = discord.Embed(
            title="🎯 Guess the Number!",
            description=(
                f"I'm thinking of a number between **1** and **{max_number}**.\n"
                f"You have **10 attempts** to guess it!\n\n"
                "Click the button below to make your guess."
            ),
            color=0x5865F2,
            timestamp=utcnow()
        )
        
        embed.add_field(name="🎮 How to Play", value="• Click **Make a Guess** button\n• Enter your number\n• Follow the hints!", inline=False)
        embed.add_field(name="🔥 Hints", value="You'll get temperature hints:\n🔥 Very Hot | ♨️ Hot | 🌡️ Warm | ❄️ Cold | 🧊 Freezing", inline=False)
        
        embed.set_footer(text=f"Player: {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        
        view = GuessView(ctx, target, max_number)
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Guess(bot))
