import discord
from discord.ext import commands
from discord import app_commands
import json
from typing import Optional

# =======================================================
# 📝 MODALS: FORMS TO CAPTURE USER TEXT INPUTS
# =======================================================

class QuickEmbedModal(discord.ui.Modal, title="1/2: Core Embed Structure"):
    """Core structure builder for standard setup."""
    embed_title = discord.ui.TextInput(label="Embed Title", placeholder="Enter main heading text...", required=False)
    embed_desc = discord.ui.TextInput(label="Main Description (Markdown Support)", style=discord.TextStyle.paragraph, placeholder="Enter main content narrative...", required=True)
    embed_color = discord.ui.TextInput(label="Hex Color Code", placeholder="e.g., #7A62FF", required=False, default="#2B2D31")

    async def on_submit(self, interaction: discord.Interaction):
        color_val = self.embed_color.value.strip()
        if color_val.startswith("#"):
            try: color = int(color_val.lstrip("#"), 16)
            except ValueError: color = 0x2B2D31
        else:
            try: color = int(color_val)
            except ValueError: color = 0x2B2D31

        embed = discord.Embed(
            title=self.embed_title.value if self.embed_title.value else None,
            description=self.embed_desc.value,
            color=color
        )
        
        view = EmbedDesignFlowView(embed)
        await interaction.response.send_message(
            "🔮 **Core Frame Captured!** Choose to dispatch the embed immediately or add advanced visual elements (Images, Footers):", 
            embed=embed, 
            view=view, 
            ephemeral=True
        )


class AdvancedVisualsModal(discord.ui.Modal, title="2/2: Advanced Layout Customizer"):
    """Secondary form to attach advanced visuals without exploding the 5-field limit."""
    thumbnail_url = discord.ui.TextInput(label="Thumbnail URL (Small Top-Right Image)", placeholder="https://domain.com/image.png", required=False)
    image_url = discord.ui.TextInput(label="Large Image URL (Bottom Banner)", placeholder="https://domain.com/banner.png", required=False)
    footer_text = discord.ui.TextInput(label="Footer Content Text", placeholder="System operational footprint notes...", required=False)

    def __init__(self, base_embed: discord.Embed):
        super().__init__()
        self.base_embed = base_embed

    async def on_submit(self, interaction: discord.Interaction):
        if self.thumbnail_url.value:
            self.base_embed.set_thumbnail(url=self.thumbnail_url.value.strip())
        if self.image_url.value:
            self.base_embed.set_image(url=self.image_url.value.strip())
        if self.footer_text.value:
            self.base_embed.set_footer(text=self.footer_text.value)

        view = EmbedSendActionView(self.base_embed)
        await interaction.response.send_message(
            "✨ **Premium Profile Compiled!** Review the finished matrix below before sending:",
            embed=self.base_embed,
            view=view,
            ephemeral=True
        )


class EditMessageModal(discord.ui.Modal, title="Modify Existing Target Segment"):
    """Modal to edit any existing bot message using its Message ID."""
    msg_id = discord.ui.TextInput(label="Target Message ID", placeholder="Paste the message ID here...", required=True)
    new_content = discord.ui.TextInput(label="Updated Raw Content / Raw JSON", style=discord.TextStyle.paragraph, placeholder="Enter normal text OR copy-paste your complete JSON template layout here...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            target_id = int(self.msg_id.value.strip())
            message = await interaction.channel.fetch_message(target_id)
        except (ValueError, discord.NotFound, discord.Forbidden):
            await interaction.followup.send("<:No:1517480787744784475> Error: Message target not found. Make sure the ID is correct and in this channel.", ephemeral=True)
            return

        raw_text = self.new_content.value.strip()

        if raw_text.startswith("{") and raw_text.endswith("}"):
            try:
                data = json.loads(raw_text)
                await interaction.client.http.edit_message(
                    channel_id=interaction.channel_id,
                    message_id=target_id,
                    content=data.get("content", None),
                    components=data.get("components", []),
                    flags=data.get("flags", 0)
                )
                await interaction.followup.send("⚡ Target message successfully overwritten via Core Layout JSON Structure.", ephemeral=True)
                return
            except Exception as e:
                await interaction.followup.send(f"<:No:1517480787744784475> JSON structural compilation failed: `{str(e)}`", ephemeral=True)
                return
        
        await message.edit(content=raw_text, embed=None, components=[])
        await interaction.followup.send("<:Yes:1517480634908541099> Target message successfully updated.", ephemeral=True)


class JsonPayloadModal(discord.ui.Modal, title="Deploy Custom JSON Configuration"):
    """Modal to paste completely pre-formed JSON payloads supporting Premium Component Layouts."""
    json_payload = discord.ui.TextInput(label="Raw JSON Blueprint", style=discord.TextStyle.paragraph, placeholder="Paste your structural JSON containing flags, components, etc...", required=True)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        try:
            raw_json = self.json_payload.value.strip()
            data = json.loads(raw_json)
            
            # FIXED: ใช้ Route ส่งแบบดิบเพื่อรองรับส่วนประกอบพิเศษและแก้ไขข้อผิดพลาด
            route = discord.http.Route("POST", "/channels/{channel_id}/messages", channel_id=interaction.channel_id)
            payload = {
                "content": data.get("content", None),
                "components": data.get("components", []),
                "flags": data.get("flags", 0)
            }
            
            await interaction.client.http.request(route, json=payload)
            await interaction.followup.send(" Layout payload broadcasted successfully.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"<:No:1517480787744784475> Execution terminated due to layout exception: `{str(e)}`", ephemeral=True)


# =======================================================
# 🔘 UI COMPONENTS: SUB-FLOW & WORKFLOW INTERFACES
# =======================================================

class EmbedDesignFlowView(discord.ui.View):
    def __init__(self, current_embed: discord.Embed):
        super().__init__(timeout=300)
        self.current_embed = current_embed

    @discord.ui.button(label="Add Premium Visuals (Images/Footer)", style=discord.ButtonStyle.blurple, emoji="🎨")
    async def go_advanced(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AdvancedVisualsModal(self.current_embed))

    @discord.ui.button(label="Send As-Is Now", style=discord.ButtonStyle.green, emoji="<:Yes:1517480634908541099>")
    async def send_now(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.send(embed=self.current_embed)
        await interaction.response.edit_message(content="<:Yes:1517480634908541099> Broadcast deployed successfully.", embed=None, view=None)


class EmbedSendActionView(discord.ui.View):
    def __init__(self, final_embed: discord.Embed):
        super().__init__(timeout=300)
        self.final_embed = final_embed

    @discord.ui.button(label="Confirm & Dispatch Broadcast", style=discord.ButtonStyle.green, emoji="📡")
    async def send_final(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.send(embed=self.final_embed)
        await interaction.response.edit_message(content="<:Yes:1517480634908541099> Premium matrix deployed.", embed=None, view=None)


# =======================================================
# 🗂️ SELECT MENUS: PRESET SELECTION SYSTEMS
# =======================================================

class PresetRulesSelect(discord.ui.Select):
    """Select menu configured with predefined official legal templates."""
    def __init__(self):
        options = [
            discord.SelectOption(label="Community Rules", description="Deploy standard community behaviors template.", value="rule_community", emoji="📜"),
            discord.SelectOption(label="Development Rules", description="Deploy technical codes and production guidelines.", value="rule_dev", emoji="💻"),
            discord.SelectOption(label="Other Rules", description="Deploy secondary sector conditions rules.", value="rule_other", emoji="🛡️")
        ]
        super().__init__(placeholder="📋 Choose a Preset Template to Send...", min_values=1, max_values=1, options=options, custom_id="cp:preset_select")

    async def callback(self, interaction: discord.Interaction):
        templates = {
            "rule_community": {
                "title": "⚖️ Community Codes of Conduct",
                "desc": "1. **Respect Members:** Maintain civil dialogue across all sectors.\n2. **No Spam:** Flooding visual structures with excessive payloads is prohibited.\n3. **Safety First:** Adhere strictly to Discord TOS guidelines."
            },
            "rule_dev": {
                "title": "💻 Infrastructure Development Protocol",
                "desc": "1. **Code Reviews:** All source vectors require secondary validation.\n2. **Testing Node:** Never execute operational updates directly on terminal cores.\n3. **Uptime Safety:** Maintain proper structural parameters for bot host files."
            },
            "rule_other": {
                "title": "🛡️ Auxiliary Operational Mandates",
                "desc": "1. **Ticket Protocols:** Direct all commercial queries to formal ticket units.\n2. **Channel Matrix:** Keep contents contextualized to their exact deployment feeds."
            }
        }
        
        selected_data = templates.get(self.values[0])
        embed = discord.Embed(
            title=selected_data["title"],
            description=selected_data["desc"],
            color=0x7A62FF
        )
        embed.set_footer(text=f"Official Protocol Broadcast • Managed by {interaction.user.name}")
        
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message(f"<:Yes:1517480634908541099> Successfully dispatched preset: **{self.values[0]}**", ephemeral=True)


# =======================================================
# 🔘 UI COMPONENTS: MAIN SYSTEM CONTROL PANEL
# =======================================================

class ControlPanelHubView(discord.ui.View):
    """Control interface acting as the terminal manager dashboard."""
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(PresetRulesSelect())

    @discord.ui.button(label="Design Best Embed", style=discord.ButtonStyle.blurple, custom_id="cp:create_embed", emoji="✨", row=1)
    async def create_embed_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(QuickEmbedModal())

    @discord.ui.button(label="Edit Message via ID", style=discord.ButtonStyle.green, custom_id="cp:edit_msg", emoji="🆔", row=1)
    async def edit_message_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EditMessageModal())

    # 📥 ADDED: ปุ่มที่ 3 สำหรับเปิดกล่องใส่ข้อมูลหรือไฟล์ JSON พิเศษโดยตรงจากหน้าหลัก
    @discord.ui.button(label="Deploy Special JSON Layout", style=discord.ButtonStyle.gray, custom_id="cp:deploy_json", emoji="🎛️", row=1)
    async def deploy_json_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(JsonPayloadModal())


# =======================================================
# 🛰️ CORE COG: COMMAND MANAGEMENT CENTRAL (HYBRID)
# =======================================================

class EmbedManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.add_view(ControlPanelHubView())

    @commands.hybrid_command(name="embed", aliases=["cp"], description="Spawns the operational configuration terminal dashboard.")
    @app_commands.describe(
        json_file="Optional: Attach a JSON file layout to deploy directly.",
        channel="Optional: Target channel destination for the attached JSON file."
    )
    @commands.has_permissions(administrator=True)
    @app_commands.default_permissions(administrator=True)
    async def spawn_control_panel(self, ctx: commands.Context, json_file: Optional[discord.Attachment] = None, channel: Optional[discord.TextChannel] = None):
        """Spawns the operational configuration terminal dashboard or handles JSON file attachments."""
        
        target_channel = channel or ctx.channel

        # กรณีผู้ใช้อัปโหลดไฟล์ JSON เข้ามาใน Argument
        if json_file:
            if not json_file.filename.endswith('.json'):
                await ctx.send("<:No:1517480787744784475> Failure: Attached document format must be strictly an official `.json` layout.", ephemeral=True)
                return

            try:
                file_bytes = await json_file.read()
                data = json.loads(file_bytes.decode('utf-8'))
                
                # FIXED: ย้ายมาใช้ระบบส่งตรงผ่าน Route เพื่อความเข้ากันได้ 100%
                route = discord.http.Route("POST", "/channels/{channel_id}/messages", channel_id=target_channel.id)
                payload = {
                    "content": data.get("content", None),
                    "components": data.get("components", []),
                    "flags": data.get("flags", 0)
                }

                await self.bot.http.request(route, json=payload)
                await ctx.send(f"🚀 Successfully processed layout payload file into channel {target_channel.mention}!", ephemeral=True)
                return

            except Exception as e:
                await ctx.send(f"<:No:1517480787744784475> Failed to parse payload from the uploaded JSON file: `{str(e)}`", ephemeral=True)
                return

        # หน้าต่างหลักของ Control Panel
        embed = discord.Embed(
            title="🛰️ Display Matrix Configuration Terminal",
            description=(
                "Interact with the processing protocols below to build or change broadcasts.\n\n"
                "• **Dropdown Menu:** Select and deploy official predefined rule parameters.\n"
                "• **Button 1 (Design Best Embed):** Generates premium multi-tiered custom embed screens.\n"
                "• **Button 2 (Edit Message via ID):** Edits any message already posted by this bot instance.\n"
                "• **Button 3 (Deploy Special JSON Layout):** Directly renders elite premium templates (Containers `Type 17`/`10`).\n\n"
                "💡 *Tip: You can now pass a `.json` file attachment as a command option to route dynamic objects anywhere!*"
            ),
            color=0x7A62FF
        )
        embed.set_footer(text="System Framework Module • Admin Access Verified")
        await ctx.send(embed=embed, view=ControlPanelHubView())


async def setup(bot: commands.Bot):
    await bot.add_cog(EmbedManager(bot))
