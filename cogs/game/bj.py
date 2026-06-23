import discord
from discord.ext import commands
from discord import app_commands
import random
from typing import List, Tuple
from discord.utils import utcnow

class BlackjackView(discord.ui.View):
    def __init__(self, ctx: commands.Context, player_hand: List[str], dealer_hand: List[str], deck: List[str]):
        super().__init__(timeout=60.0) # หมดเวลาปุ่มภายใน 60 วินาที
        self.ctx = ctx
        self.player_hand = player_hand
        self.dealer_hand = dealer_hand
        self.deck = deck

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # ป้องกันไม่ให้คนอื่นมากดปุ่มเล่นแทนผู้ใช้ที่เรียกคำสั่ง
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("<:No:1517480787744784475> **Security Alert:** This gaming terminal is locked to the original user.", ephemeral=True)
            return False
        return True

    def calculate_score(self, hand: List[str]) -> int:
        """คำนวณแต้มจากไพ่ในมือ (Smart Ace System)"""
        score = 0
        aces = 0
        for card in hand:
            value = card[:-1] # แยกดอกไพ่ออก เอาเฉพาะค่า เช่น '10♦' -> '10'
            if value in ['J', 'Q', 'K']:
                score += 10
            elif value == 'A':
                aces += 1
                score += 11
            else:
                score += int(value)
        
        # ปรับค่า Ace จาก 11 แต้มเป็น 1 แต้ม ถ้าแต้มรวมเกิน 21
        while score > 21 and aces:
            score -= 10
            aces -= 1
        return score

    def get_hand_string(self, hand: List[str]) -> str:
        return " ".join(f"`{card}`" for card in hand)

    def create_bj_embed(self, title: str, description: str, show_dealer_hidden: bool = True) -> discord.Embed:
        player_score = self.calculate_score(self.player_hand)
        
        embed = discord.Embed(
            title=f"🃏 Blackjack Core • {title}",
            description=description,
            color=0x2B2D31,
            timestamp=utcnow()
        )
        
        # คุมการแสดงผลไพ่ของเจ้ามือ (Dealer)
        if show_dealer_hidden:
            dealer_display = f"`{self.dealer_hand[0]}` `🃏`"
            dealer_score_str = "?"
        else:
            dealer_display = self.get_hand_string(self.dealer_hand)
            dealer_score_str = str(self.calculate_score(self.dealer_hand))

        embed.add_field(
            name=f"🤖 Dealer Hand [{dealer_score_str}]",
            value=f"> {dealer_display}",
            inline=False
        )
        
        embed.add_field(
            name=f"👤 {self.ctx.author.display_name}'s Hand [{player_score}]",
            value=f"> {self.get_hand_string(self.player_hand)}",
            inline=False
        )
        
        embed.set_footer(
            text=f"Game Instance • {self.ctx.author.name}",
            icon_url=self.ctx.author.display_avatar.url
        )
        return embed

    async def end_game(self, interaction: discord.Interaction, title: str, description: str, color: int):
        # จบเกม ลบปุ่มทั้งหมดออกเพื่อเคลียร์ UI
        self.clear_items()
        embed = self.create_bj_embed(title, description, show_dealer_hidden=False)
        embed.color = color
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    @discord.ui.button(label="Hit (Draw)", style=discord.ButtonStyle.blurple, emoji="➕")
    async def hit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # ผู้ใช้เลือกจั่วไพ่เพิ่ม 1 ใบ
        self.player_hand.append(self.deck.pop())
        player_score = self.calculate_score(self.player_hand)

        if player_score > 21:
            # แต้มเกิน (Bust) แพ้ทันที
            await self.end_game(interaction, "Bust!", "❌ You went over 21. **Dealer Wins!**", 0xED4245)
        elif player_score == 21:
            # ได้ 21 แต้มพอดี บังคับ Stand เพื่อความปลอดภัย
            await self.execute_stand(interaction)
        else:
            # อัปเดตการแสดงผลหน้าจอเกม
            embed = self.create_bj_embed("Your Turn", "Select your next tactical move.")
            await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Stand (Stay)", style=discord.ButtonStyle.green, emoji="🛑")
    async def stand_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.execute_stand(interaction)

    async def execute_stand(self, interaction: discord.Interaction):
        # ฝั่งเจ้ามือ (Dealer) จั่วไพ่ตามกฎสากล (ต้องจั่วจนกว่าแต้มจะมากกว่าหรือเท่ากับ 17)
        player_score = self.calculate_score(self.player_hand)
        dealer_score = self.calculate_score(self.dealer_hand)

        while dealer_score < 17:
            self.dealer_hand.append(self.deck.pop())
            dealer_score = self.calculate_score(self.dealer_hand)

        # ตัดสินผลแพ้ชนะ
        if dealer_score > 21:
            await self.end_game(interaction, "Dealer Bust!", "🎉 **Dealer went over 21! You win!**", 0x57F287)
        elif player_score > dealer_score:
            await self.end_game(interaction, "Victory!", f"🎉 You outscored the dealer! `{player_score}` vs `{dealer_score}`", 0x57F287)
        elif player_score < dealer_score:
            await self.end_game(interaction, "Defeat", f"❌ Dealer outscored you. `{dealer_score}` vs `{player_score}`", 0xED4245)
        else:
            await self.end_game(interaction, "Push (Tie)", f"🤝 Standard standoff. It's a draw at `{player_score}`.", 0x95A5A6)

    async def on_timeout(self):
        # จัดการกรณีผู้ใช้ปล่อยจอยทิ้งไว้เฉยๆ ไม่กดอะไร
        self.clear_items()
        self.stop()


class Blackjack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def generate_deck(self) -> List[str]:
        suits = ['♠', '♥', '♦', '♣']
        values = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        deck = [f"{v}{s}" for v in values for s in suits]
        random.shuffle(deck)
        return deck

    @commands.hybrid_command(name="blackjack", aliases=["bj"])
    async def blackjack(self, ctx: commands.Context):
        """🃏 Start a fast-paced interactive tactical Blackjack game matrix."""
        await ctx.defer()

        deck = self.generate_deck()
        
        # แจกไพ่เริ่มต้นคนละ 2 ใบ
        player_hand = [deck.pop(), deck.pop()]
        dealer_hand = [deck.pop(), deck.pop()]

        view = BlackjackView(ctx, player_hand, dealer_hand, deck)
        
        player_score = view.calculate_score(player_hand)
        
        # เช็กกรณีได้ไพ่คู่เทพ Natural Blackjack (21 แต้มตั้งแต่แจกหนแรก)
        if player_score == 21:
            view.clear_items() # ลบปุ่ม
            embed = view.create_bj_embed("Natural Blackjack!", "✨ **Incredible! You hit a Natural Blackjack! Victory achieved.**", show_dealer_hidden=False)
            embed.color = 0xFEE75C # สีทองเฉลิมฉลอง
            return await ctx.send(embed=embed)

        embed = view.create_bj_embed("Game Initialized", "Choose whether to **Hit** for another card or **Stand** to lock your score.")
        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Blackjack(bot))
  
