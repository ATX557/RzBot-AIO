# 🛰️ RzBot-AIO (All-In-One Discord Framework)

---

Welcome to **RzBot-AIO**! This is a free, open-source, advanced Discord Bot framework written in Python using `discord.py`. The project is currently in **Beta**, meaning you have full authorization and freedom to customize, adapt, modify, and optimize the source architecture to fit your specific deployment matrix.

---

## 🛠️ Infrastructure Core Configurations

To successfully deploy and synchronize this system node, you need to configure the core environments below.

### 📄 1. The Environment Matrix (`.env`)
> Create a file named `.env` in the root directory of your project and configure the system variables as follows:

```env
# ⚙️ DISCORD CORE CONFIG
DISCORD_TOKEN=your_bot_token_here
BOT_PREFIX=$
OWNERS_IDS=your_user_id

# 📡 DATABASE CONFIG
MONGO_URI=

# 🤖 AI API CONFIG (Gemini / ChatGPT / Group) [Not mandatory]
GEMINI_API=your_gemini_api_key
GPT_API=your_openai_api_key
GROUP_API=your_group_api_key

# 🎭 BOT APPEARANCE STATUS
# Bot Presence Status (Enter a number from 0-4):
# 0 = Online, 1 = Idle, 2 = DND, 3 = Invisible, 4 = Offline
BOT_STATUS=2

# 💬 DYNAMIC STATUS TEXTS (Up to 3 messages / Optional slots)
# New Available Placeholders: {prefix}, {guilds}, {users}, {size.commands}, {ping}, {cogs}, {shards}
STATUS_TEXT_1=⚡ Mainframe: {ping} | {guilds} Guilds Sectors
STATUS_TEXT_2=RzBot™ • {prefix}help | {size.commands} Protocols Loaded
STATUS_TEXT_3=🛰️ Matrix Active • Monitoring {users} Inhabitants via Shard #{shards}

# 🔔 SYSTEM LOGGING WEBHOOKS
WEBHOOK_GUILD_JOIN=
WEBHOOK_GUILD_LEAVE=
WEBHOOK_COMMAND_LOG=
WEBHOOK_COMMAND_ERROR=
```

### 📄 2. The Environment Matrix (`app.py`)
> And for part 2, you need to edit the file in the app.py, on line 145, to modify the variable `{size.commands}`
