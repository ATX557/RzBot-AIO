import discord
from discord.ext import commands
from discord import app_commands
import random
from discord.utils import utcnow

class ScrambleView(discord.ui.View):
    def __init__(self, ctx: commands.Context, word: str, scrambled: str, difficulty: str):
        super().__init__(timeout=60.0)
        self.ctx = ctx
        self.word = word
        self.scrambled = scrambled
        self.difficulty = difficulty
        self.attempts = 0
        self.max_attempts = 3
    
    @discord.ui.button(label="Submit Answer", style=discord.ButtonStyle.blurple, emoji="✍️")
    async def answer_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("❌ This isn't your game!", ephemeral=True)
            return
        
        modal = AnswerModal(self)
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Get Hint", style=discord.ButtonStyle.green, emoji="💡")
    async def hint_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("❌ This isn't your game!", ephemeral=True)
            return
        
        # Reveal first and last letter
        hint = f"{self.word[0]}{'_' * (len(self.word) - 2)}{self.word[-1]}"
        
        await interaction.response.send_message(
            f"💡 **Hint:** The word pattern is: `{hint}` (Length: {len(self.word)} letters)",
            ephemeral=True
        )
    
    @discord.ui.button(label="Give Up", style=discord.ButtonStyle.red, emoji="🏳️")
    async def giveup_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("❌ This isn't your game!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🏳️ You Gave Up!",
            description=f"The word was: **{self.word.upper()}**",
            color=0x95A5A6,
            timestamp=utcnow()
        )
        embed.add_field(name="📊 Attempts Used", value=f"`{self.attempts}` / {self.max_attempts}", inline=True)
        embed.add_field(name="🎮 Difficulty", value=self.difficulty, inline=True)
        embed.set_footer(text=f"Player: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        
        for item in self.children:
            item.disabled = True
        
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()
    
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        self.stop()


class AnswerModal(discord.ui.Modal):
    def __init__(self, view: ScrambleView):
        super().__init__(title="✍️ Submit Your Answer")
        self.view = view
        
        self.answer_input = discord.ui.TextInput(
            label="Unscramble the word",
            placeholder="Type your answer here...",
            required=True,
            max_length=50
        )
        self.add_item(self.answer_input)
    
    async def on_submit(self, interaction: discord.Interaction):
        answer = self.answer_input.value.strip().lower()
        self.view.attempts += 1
        
        if answer == self.view.word.lower():
            # Correct answer!
            score_map = {"Easy": 100, "Medium": 200, "Hard": 300}
            base_score = score_map[self.view.difficulty]
            bonus = (self.view.max_attempts - self.view.attempts) * 50
            total_score = base_score + bonus
            
            embed = discord.Embed(
                title="🎉 Correct! You Solved It!",
                description=f"The word was: **{self.view.word.upper()}**",
                color=0x57F287,
                timestamp=utcnow()
            )
            
            embed.add_field(name="📊 Attempts", value=f"`{self.view.attempts}` / {self.view.max_attempts}", inline=True)
            embed.add_field(name="🏆 Score", value=f"`{total_score}` points", inline=True)
            embed.add_field(name="🎮 Difficulty", value=self.view.difficulty, inline=True)
            
            # Add stars based on performance
            stars = "⭐" * (self.view.max_attempts - self.view.attempts + 1)
            embed.add_field(name="Rating", value=stars or "Good try!", inline=False)
            
            embed.set_footer(text=f"Player: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
            
            for item in self.view.children:
                item.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self.view)
            self.view.stop()
        
        elif self.view.attempts >= self.view.max_attempts:
            # Out of attempts
            embed = discord.Embed(
                title="❌ Game Over - Out of Attempts",
                description=f"The word was: **{self.view.word.upper()}**\n\nYour answer: **{answer.upper()}**",
                color=0xED4245,
                timestamp=utcnow()
            )
            embed.add_field(name="📊 Attempts Used", value=f"`{self.view.attempts}` / {self.view.max_attempts}", inline=True)
            embed.add_field(name="🎮 Difficulty", value=self.view.difficulty, inline=True)
            embed.set_footer(text=f"Player: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
            
            for item in self.view.children:
                item.disabled = True
            
            await interaction.response.edit_message(embed=embed, view=self.view)
            self.view.stop()
        
        else:
            # Wrong answer, try again
            embed = discord.Embed(
                title=f"❌ Wrong Answer: {answer.upper()}",
                description=f"Try again! The scrambled word is: **{self.view.scrambled}**",
                color=0xED4245,
                timestamp=utcnow()
            )
            
            embed.add_field(
                name="📊 Attempts Left",
                value=f"`{self.view.max_attempts - self.view.attempts}` / {self.view.max_attempts}",
                inline=True
            )
            embed.add_field(name="💡 Tip", value="Use the **Get Hint** button!", inline=True)
            
            embed.set_footer(text=f"Player: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
            
            await interaction.response.edit_message(embed=embed, view=self.view)


class Scramble(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.words = {
            "Easy": [
                "apple", "grape", "melon", "peach", "lemon",
                "bread", "chair", "table", "house", "music",
                "phone", "water", "earth", "plant", "clock"
            ],
            "Medium": [
                "python", "discord", "computer", "keyboard", "internet",
                "elephant", "mountain", "butterfly", "chocolate", "adventure",
                "happiness", "knowledge", "beautiful", "technology", "experience"
            ],
            "Hard": [
                "mysterious", "extraordinary", "sophisticated", "philosophical", "unprecedented",
                "metamorphosis", "chrysanthemum", "onomatopoeia", "entrepreneur", "abbreviation",
                "procrastinate", "serendipity", "kaleidoscope", "hippopotamus", "electromagnetic"
            ]
        }
    
    def scramble_word(self, word: str) -> str:
        """Scramble a word while ensuring it's different from original"""
        if len(word) <= 2:
            return word
        
        scrambled = word
        attempts = 0
        while scrambled == word and attempts < 100:
            word_list = list(word)
            random.shuffle(word_list)
            scrambled = ''.join(word_list)
            attempts += 1
        
        return scrambled
    
    @commands.hybrid_command(name="scramble")
    @commands.guild_only()
    async def scramble(self, ctx: commands.Context, difficulty: str = "Medium"):
        """🔤 Unscramble the word! Test your vocabulary!
        
        Parameters:
        - difficulty: Easy, Medium, or Hard (default: Medium)
        """
        difficulty = difficulty.title()
        
        if difficulty not in self.words:
            return await ctx.send("❌ Invalid difficulty! Choose: **Easy**, **Medium**, or **Hard**")
        
        # Select random word
        word = random.choice(self.words[difficulty])
        scrambled = self.scramble_word(word)
        
        # Create embed
        embed = discord.Embed(
            title="🔤 Word Scramble Challenge",
            description=f"Unscramble this word:\n\n**{scrambled.upper()}**",
            color=0x5865F2,
            timestamp=utcnow()
        )
        
        embed.add_field(name="⏱️ Time Limit", value="60 seconds", inline=True)
        embed.add_field(name="🎮 Difficulty", value=difficulty, inline=True)
        embed.add_field(name="📊 Attempts", value="3 tries", inline=True)
        
        embed.add_field(
            name="💡 Hint Available",
            value="Click the **Get Hint** button to reveal first and last letters!",
            inline=False
        )
        
        embed.set_footer(text=f"Player: {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        
        view = ScrambleView(ctx, word, scrambled, difficulty)
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Scramble(bot))
