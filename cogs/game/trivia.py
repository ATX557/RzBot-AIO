import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
from typing import Dict, List
from discord.utils import utcnow

class TriviaView(discord.ui.View):
    def __init__(self, ctx: commands.Context, question_data: Dict, category: str):
        super().__init__(timeout=30.0)
        self.ctx = ctx
        self.question_data = question_data
        self.category = category
        self.answered = False
        self.correct_answer = question_data["correct"]
        
        # Shuffle answers
        answers = question_data["options"].copy()
        random.shuffle(answers)
        
        # Create buttons for each answer
        for idx, answer in enumerate(answers):
            button = discord.ui.Button(
                label=answer,
                style=discord.ButtonStyle.blurple,
                custom_id=f"answer_{idx}"
            )
            button.callback = self.create_answer_callback(answer)
            self.add_item(button)
    
    def create_answer_callback(self, selected_answer: str):
        async def answer_callback(interaction: discord.Interaction):
            if interaction.user != self.ctx.author:
                await interaction.response.send_message("❌ This isn't your trivia game!", ephemeral=True)
                return
            
            if self.answered:
                await interaction.response.send_message("⏱️ You already answered!", ephemeral=True)
                return
            
            self.answered = True
            
            # Check if correct
            is_correct = (selected_answer == self.correct_answer)
            
            # Update all buttons
            for item in self.children:
                if isinstance(item, discord.ui.Button):
                    item.disabled = True
                    if item.label == self.correct_answer:
                        item.style = discord.ButtonStyle.green
                        item.emoji = "✅"
                    elif item.label == selected_answer and not is_correct:
                        item.style = discord.ButtonStyle.red
                        item.emoji = "❌"
            
            # Create result embed
            if is_correct:
                embed = discord.Embed(
                    title="🎉 Correct Answer!",
                    description=f"**{selected_answer}** is correct!\n\n💡 **Explanation:**\n{self.question_data.get('explanation', 'Well done!')}",
                    color=0x57F287,
                    timestamp=utcnow()
                )
            else:
                embed = discord.Embed(
                    title="❌ Wrong Answer",
                    description=f"**{selected_answer}** is incorrect.\n\nThe correct answer was: **{self.correct_answer}**\n\n💡 **Explanation:**\n{self.question_data.get('explanation', 'Better luck next time!')}",
                    color=0xED4245,
                    timestamp=utcnow()
                )
            
            embed.add_field(name="Category", value=f"📚 {self.category}", inline=True)
            embed.add_field(name="Difficulty", value=f"⭐ {self.question_data['difficulty']}", inline=True)
            embed.set_footer(text=f"Player: {self.ctx.author.name}", icon_url=self.ctx.author.display_avatar.url)
            
            await interaction.response.edit_message(embed=embed, view=self)
            self.stop()
        
        return answer_callback
    
    async def on_timeout(self):
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
                if item.label == self.correct_answer:
                    item.style = discord.ButtonStyle.green
        self.stop()


class Trivia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.questions = {
            "General": [
                {
                    "question": "What is the capital of France?",
                    "options": ["London", "Berlin", "Paris", "Madrid"],
                    "correct": "Paris",
                    "difficulty": "Easy",
                    "explanation": "Paris has been the capital of France since 987 AD."
                },
                {
                    "question": "How many continents are there on Earth?",
                    "options": ["5", "6", "7", "8"],
                    "correct": "7",
                    "difficulty": "Easy",
                    "explanation": "The 7 continents are: Africa, Antarctica, Asia, Europe, North America, Oceania, and South America."
                },
                {
                    "question": "Who painted the Mona Lisa?",
                    "options": ["Vincent van Gogh", "Leonardo da Vinci", "Pablo Picasso", "Michelangelo"],
                    "correct": "Leonardo da Vinci",
                    "difficulty": "Medium",
                    "explanation": "Leonardo da Vinci painted the Mona Lisa between 1503-1519."
                },
            ],
            "Science": [
                {
                    "question": "What is the chemical symbol for gold?",
                    "options": ["Go", "Gd", "Au", "Ag"],
                    "correct": "Au",
                    "difficulty": "Medium",
                    "explanation": "Gold's symbol 'Au' comes from the Latin word 'aurum' meaning 'shining dawn'."
                },
                {
                    "question": "What is the speed of light in vacuum?",
                    "options": ["299,792 km/s", "150,000 km/s", "500,000 km/s", "1,000,000 km/s"],
                    "correct": "299,792 km/s",
                    "difficulty": "Hard",
                    "explanation": "Light travels at approximately 299,792 kilometers per second in a vacuum."
                },
                {
                    "question": "How many bones are in the adult human body?",
                    "options": ["186", "206", "226", "246"],
                    "correct": "206",
                    "difficulty": "Medium",
                    "explanation": "An adult human has 206 bones, while babies are born with about 270 that later fuse."
                },
            ],
            "Gaming": [
                {
                    "question": "What year was Minecraft officially released?",
                    "options": ["2009", "2010", "2011", "2012"],
                    "correct": "2011",
                    "difficulty": "Medium",
                    "explanation": "Minecraft was officially released on November 18, 2011, after years in development."
                },
                {
                    "question": "Which company developed Discord?",
                    "options": ["Microsoft", "Discord Inc.", "Facebook", "Google"],
                    "correct": "Discord Inc.",
                    "difficulty": "Easy",
                    "explanation": "Discord was developed by Discord Inc. (formerly Hammer & Chisel) in 2015."
                },
                {
                    "question": "What is the maximum level in Pokémon games?",
                    "options": ["99", "100", "120", "255"],
                    "correct": "100",
                    "difficulty": "Easy",
                    "explanation": "In most Pokémon games, the maximum level a Pokémon can reach is 100."
                },
            ],
            "History": [
                {
                    "question": "In which year did World War II end?",
                    "options": ["1943", "1944", "1945", "1946"],
                    "correct": "1945",
                    "difficulty": "Medium",
                    "explanation": "World War II ended in 1945 with Germany's surrender in May and Japan's in September."
                },
                {
                    "question": "Who was the first president of the United States?",
                    "options": ["Thomas Jefferson", "George Washington", "Abraham Lincoln", "John Adams"],
                    "correct": "George Washington",
                    "difficulty": "Easy",
                    "explanation": "George Washington served as the first U.S. president from 1789 to 1797."
                },
            ],
        }
    
    @commands.hybrid_command(name="trivia")
    @commands.guild_only()
    async def trivia(self, ctx: commands.Context, category: str = None):
        """🧠 Test your knowledge with interactive trivia questions!
        
        Categories: General, Science, Gaming, History
        """
        await ctx.defer()
        
        # Select category
        if category:
            category = category.title()
            if category not in self.questions:
                available = ", ".join(self.questions.keys())
                return await ctx.send(f"❌ Invalid category! Available: **{available}**")
        else:
            category = random.choice(list(self.questions.keys()))
        
        # Select random question from category
        question_data = random.choice(self.questions[category])
        
        # Create embed
        embed = discord.Embed(
            title=f"🧠 Trivia Challenge: {category}",
            description=f"**Question:**\n{question_data['question']}",
            color=0x5865F2,
            timestamp=utcnow()
        )
        embed.add_field(name="⏱️ Time Limit", value="30 seconds", inline=True)
        embed.add_field(name="📊 Difficulty", value=question_data['difficulty'], inline=True)
        embed.set_footer(text=f"Player: {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        
        view = TriviaView(ctx, question_data, category)
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Trivia(bot))
