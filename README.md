# 🛰️ RzBot-AIO (All-In-One Discord Framework)

---

Welcome to **RzBot-AIO**! This is a free, open-source, advanced Discord Bot framework written in Python using `discord.py`. The project is currently in **Beta**, meaning you have full authorization and freedom to customize, adapt, modify, and optimize the source architecture to fit your specific deployment matrix.

---

## 🛠️ Infrastructure Core Configurations

To successfully deploy and synchronize this system node, you need to configure the core environments below.

### 📄 1. The Environment Matrix (`.env`)
Create a file named `.env` in the root directory of your project and configure the system variables as follows:

```env
# 🔑 SECURITY CREDENTIALS
DISCORD_TOKEN=your_discord_bot_token_here
MONGO_URI=your_mongodb_atlas_connection_string_here

# ⚙️ GLOBAL PRESETS
BOT_PREFIX=!
# Status Modes -> 0: Online, 1: Idle, 2: DND, 3: Invisible, 4: Offline
BOT_STATUS=0

# 📊 DYNAMIC PRESENCE STREAM (Supports: {prefix}, {guilds}, {users}, {ram}, {ping})
STATUS_TEXT_1=Core System | {prefix}help
STATUS_TEXT_2=Monitoring {guilds} Servers & {users} Users
STATUS_TEXT_3=Latency: {ping} | RAM: {ram}
```
