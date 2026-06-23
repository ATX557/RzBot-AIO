import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

# -----------------------
# LOAD ENVIRONMENT CONFIG
# -----------------------
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("BOT_PREFIX", "!")
MONGO_URI = os.getenv("MONGO_URI")

# 🔄 ฟังก์ชันสำหรับย่อตัวเลขให้อยู่ในรูปแบบ K, M+ เพื่อประหยัดพื้นที่บน Status
def format_compact_number(num: int) -> str:
    if num >= 1_000_000:
        return f"{num / 1_000_000:.0f}M+"  
    elif num >= 1_000:
        val = num / 1_000
        return f"{val:.0f}K" if val.is_integer() else f"{val:.1f}K"
    return str(num)  

# 📡 DYNAMIC PREFIX PROCESSOR FOR MONGODB
async def determine_prefix(bot: commands.Bot, message: discord.Message):
    """Dynamic prefix loader for text commands routing through MongoDB."""
    if not message.guild:
        return PREFIX
        
    try:
        data = await bot.db["guild_prefixes"].find_one({"guild_id": str(message.guild.id)})
        if data and "prefix" in data:
            return data["prefix"]
    except Exception as e:
        print(f"[DB PREFIX ERROR] Failed to fetch prefix: {e}")
        
    return PREFIX 

# -----------------------
# BOT CORE ENGINE CLASS
# -----------------------
class CoreBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        
        status_input = os.getenv("BOT_STATUS", "0")
        status_mapping = {
            "0": discord.Status.online,
            "1": discord.Status.idle,
            "2": discord.Status.dnd,
            "3": discord.Status.invisible,
            "4": discord.Status.offline
        }
        self.status_enum = status_mapping.get(status_input, discord.Status.online)

        super().__init__(
            command_prefix=determine_prefix,
            intents=intents,
            status=self.status_enum,
            activity=None  
        )

    async def setup_hook(self):
        self.start_time = datetime.now(timezone.utc)
        
        # 💾 INITIALIZE MONGO CLIENT MATRIX
        if MONGO_URI:
            try:
                self.db_client = AsyncIOMotorClient(MONGO_URI)
                self.db = self.db_client["RzBotDatabase"] 
                print("[DATABASE] Successfully established MongoDB Atlas connection grid.")
            except Exception as e:
                print(f"[DATABASE CRITICAL ERROR] Connection failed: {e}")
        else:
            print("[DATABASE WARNING] 'MONGO_URI' not detected in environment variables!")

        # 🚀 1. AUTOMATICALLY LOAD BOTH 'COGS' AND 'CORE' DIRECTORIES
        # ระบบจะทำการค้นหาและโหลดไฟล์อัตโนมัติจากทั้ง 2 โฟลเดอร์ที่กำหนดไว้
        target_directories = ["./cogs", "./core"]
        
        for directory in target_directories:
            if not os.path.exists(directory):
                print(f"[WARNING] Directory '{directory}' not found, skipping...")
                continue
                
            print(f"--- Loading Infrastructure from {directory} ---")
            for root, _, files in os.walk(directory):
                for file in files:
                    if file.endswith(".py") and not file.startswith("_"):
                        relative_path = os.path.relpath(os.path.join(root, file), start=".")
                        path = relative_path.replace("\\", ".").replace("/", ".")[:-3]
                        try:
                            await self.load_extension(path)
                            print(f"[LOADED] {path}")
                        except Exception as e:
                            print(f"[ERROR] Fail to load {path}: {e}")

        try:
            await self.tree.sync()
            print("[SYNC] Slash commands synchronized globally.")
        except Exception as e:
            print(f"[ERROR] Slash sync failed: {e}")
        print("―" * 30)

        if not self.update_presence_loop.is_running():
            self.update_presence_loop.start()

    # ==========================================
    # 🔄 DYNAMIC CUSTOM PRESENCE STATUS LOOP
    # ==========================================
    @tasks.loop(minutes=2)  
    async def update_presence_loop(self):
        if not self.is_ready():
            return

        prefix_cmds = set(c.name for c in self.commands)
        slash_cmds = set(c.name for c in self.tree.get_commands())
        total_commands = len(prefix_cmds.union(slash_cmds))
        
        total_guilds = len(self.guilds)
        total_users = sum(guild.member_count for guild in self.guilds if guild.member_count)
        
        raw_templates = [
            os.getenv("STATUS_TEXT_1"),
            os.getenv("STATUS_TEXT_2"),
            os.getenv("STATUS_TEXT_3")
        ]
        active_templates = [t for t in raw_templates if t and t.strip()]

        if not active_templates:
            active_templates = ["Core System | {prefix}help"]

        current_loop_count = self.update_presence_loop.current_loop
        chosen_template = active_templates[current_loop_count % len(active_templates)]

        bot_ping = round(self.latency * 1000)
        shard_count = self.shard_count if self.shard_count else 1

        format_data = {
            "prefix": PREFIX, 
            "guilds": format_compact_number(total_guilds),
            "users": format_compact_number(total_users),
            "size.commands": format_compact_number(total_commands),
            "ping": f"{bot_ping}ms",
            "shards": str(shard_count),
            "cogs": str(len(self.cogs))
        }

        try:
            status_text = chosen_template.format(**format_data)
        except Exception as e:
            status_text = "Core Engine: Template Error"
            print(f"[STATUS ERROR] Formatting exception details: {e}")

        await self.change_presence(
            status=self.status_enum,
            activity=discord.CustomActivity(name=status_text)
        )

    # -----------------------
    # SYSTEM ENGINE EVENTS
    # -----------------------
    async def on_ready(self):
        prefix_cmds = set(c.name for c in self.commands)
        slash_cmds = set(c.name for c in self.tree.get_commands())
        total_commands = len(prefix_cmds.union(slash_cmds))
        total_users = sum(guild.member_count for guild in self.guilds if guild.member_count)

        print("=" * 30)
        print(f"[Application Name]: {self.user.name}")
        print(f"[ID]: {self.user.id}")
        print(f"[Guilds]: {len(self.guilds)}")
        print(f"[Total Users]: {total_users}")
        print("=" * 30)
        print("[SERVER]: Core Engine Online & Ready!")
        print("=" * 30)
        print(f"[GLOBAL PREFIX]: {PREFIX}")
        print(f"[Total Extensions Loaded]: {len(self.cogs)}")
        print(f"[Total Commands]: {total_commands}")
        print("=" * 30)

# -----------------------
# CORE INITIALIZATION
# -----------------------
core = CoreBot()

# -----------------------
# PROGRAM EXECUTION
# -----------------------
if __name__ == "__main__":
    if not TOKEN:
        print("[CRITICAL ERROR] 'DISCORD_TOKEN' missing in .env configuration!")
    else:
        core.run(TOKEN)
