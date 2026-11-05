import os
import time
import datetime
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

load_dotenv()
TOKEN = os.getenv("TOKEN")

# Render Port Binding Keep-Alive HTTP Server
app = Flask('')

@app.route('/')
def home():
    return "Spike.lol Bot is Live and Running 24/7!"

def run_web():
    port = int(os.getenv("PORT", 3000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

keep_alive()

# Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.dm_messages = True
intents.voice_states = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# Snipe and Cooldown storage
snipe_storage = {}
help_cooldowns = {}

@bot.event
async def on_ready():
    print(f"[BOT] Logged in as {bot.user.tag} successfully!")
    await bot.change_presence(
        status=discord.Status.dnd,
        activity=discord.Activity(type=discord.ActivityType.watching, name=".gg/Spike.lol | .helps")
    )

# Snipe tracker (Store deleted messages for 24 hours)
@bot.event
async def on_message_delete(message):
    if message.author.bot or not message.guild:
        return
    guild_id = message.guild.id
    if guild_id not in snipe_storage:
        snipe_storage[guild_id] = []
    
    snipe_storage[guild_id].insert(0, {
        "content": message.content or "[Embed or Attachment]",
        "author": str(message.author),
        "channel": message.channel.name,
        "time": time.time()
    })
    current_time = time.time()
    snipe_storage[guild_id] = [m for m in snipe_storage[guild_id] if current_time - m["time"] < 86400][:20]

# Message Listener (Ticket help trigger with 10m cooldown)
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content_lower = message.content.lower()
    if content_lower == "help" or ("help" in content_lower and not message.content.startswith('.')):
        guild_id = message.guild.id if message.guild else "dm"
        user_id = message.author.id
        cooldown_key = f"{guild_id}-{user_id}"
        current_time = time.time()

        if cooldown_key not in help_cooldowns or current_time - help_cooldowns[cooldown_key] >= 600:
            help_cooldowns[cooldown_key] = current_time
            embed = discord.Embed(
                title="✨ **SPIKE.LOL SUPPORT TICKET DESK** ✨",
                description="> **Need assistance?** Use `.ticketsetup` to open a ticket via panel or contact staff!\n\n📌 **Status:** Ticket System Active\n🔒 **Security:** Fully Encrypted & Secure",
                color=0x2b2d31
            )
            embed.set_footer(text="⚡ Powered by Spike.lol | Cooldown: 10m")
            try:
                await message.reply(embed=embed)
            except Exception:
                pass

    await bot.process_commands(message)

# --- ADVANCED TICKET SYSTEM (SELECT MENU + BUTTONS) ---

class TicketControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket_btn", emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⚠️ Ticket is closing in 5 seconds...", ephemeral=False)
        import asyncio
        await asyncio.sleep(5)
        try:
            await interaction.channel.delete()
        except Exception:
            pass

class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="General Support", description="Get help regarding general server questions", emoji="💬", value="general"),
            discord.SelectOption(label="Staff Report", description="Report a staff member or user", emoji="🛡️", value="report"),
            discord.SelectOption(label="Partnership / Promo", description="Inquire about partnerships and promotions", emoji="🤝", value="partnership"),
        ]
        super().__init__(placeholder="📂 Choose ticket category...", min_values=1, max_values=1, options=options, custom_id="ticket_dropdown")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        category_type = self.values[0]

        existing_channel = discord.utils.get(guild.text_channels, name=f"ticket-{member.name.lower()}")
        if existing_channel:
            return await interaction.response.send_message(f"❌ Aapka pehle se ek ticket khula hua hai: {existing_channel.mention}", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }

        try:
            ticket_channel = await guild.create_text_channel(
                name=f"ticket-{member.name}",
                overwrites=overwrites,
                topic=f"Category: {category_type.upper()} | User: {member.tag}"
            )

            embed = discord.Embed(
                title=f"✨ **SPIKE.LOL TICKET [{category_type.upper()}]** ✨",
                description=f"> Hello {member.mention},\n> Apni problem yahan detail me batao. Staff jald hi reply karega.\n\n🔒 **Neeche diye gaye button se ticket close kar sakte ho.**",
                color=0x2b2d31
            )
            embed.set_footer(text="⚡ Spike.lol Security & Support")

            await ticket_channel.send(content=f"{member.mention}", embed=embed, view=TicketControlView())
            await interaction.response.send_message(f"✅ Aapka ticket successfully ban gaya hai: {ticket_channel.mention}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Ticket banane me error aayi: {e}", ephemeral=True)

class TicketSetupDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())

    @discord.ui.button(label="Create Direct Ticket", style=discord.ButtonStyle.primary, custom_id="create_direct_ticket_btn", emoji="🎫", row=1)
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = interaction.user

        existing_channel = discord.utils.get(guild.text_channels, name=f"ticket-{member.name.lower()}")
        if existing_channel:
            return await interaction.response.send_message(f"❌ Aapka pehle se ek ticket khula hua hai: {existing_channel.mention}", ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
        }

        try:
            ticket_channel = await guild.create_text_channel(
                name=f"ticket-{member.name}",
                overwrites=overwrites,
                topic=f"Support ticket for {member.tag}. Created via Spike.lol Ticket System."
            )

            embed = discord.Embed(
                title="✨ **SPIKE.LOL SUPPORT TICKET** ✨",
                description=f"> Hello {member.mention},\n> Staff team ko yahan apni problem batao. Wo jald hi reply karenge.\n\n🔒 **Neeche diye gaye button se ticket close kar sakte ho.**",
                color=0x2b2d31
            )
            embed.set_footer(text="⚡ Spike.lol Security & Support")

            await ticket_channel.send(content=f"{member.mention}", embed=embed, view=TicketControlView())
            await interaction.response.send_message(f"✅ Aapka ticket successfully ban gaya hai: {ticket_channel.mention}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Ticket banane me error aayi: {e}", ephemeral=True)


# --- COMMANDS ---

# 1. .ticketsetup Command (Sends Dropdown & Button Panel)
@bot.command(name="ticketsetup")
@commands.has_permissions(administrator=True)
async def ticket_setup(ctx):
    embed = discord.Embed(
        title="✨ **SPIKE.LOL OFFICIAL TICKET DESK** ✨",
        description="> **Need help or want to talk to staff?**\n> Neeche diye gaye **Select Menu** se category choose karo ya **Button** dabao taaki private ticket instant create ho jaye!\n\n📌 **Rules:** Do not spam tickets unnecessarily.",
        color=0x2b2d31
    )
    embed.set_footer(text="⚡ Powered by Spike.lol Ticket System")
    
    try:
        await ctx.message.delete()
    except Exception:
        pass

    await ctx.send(embed=embed, view=TicketSetupDropdownView())

# 2. .helps Command
@bot.command(name="helps")
async def helps_cmd(ctx):
    embed = discord.Embed(
        title="🔥 **✨ SPIKE.LOL MODERATION & UTILITY HELP ✨** 🔥",
        description="> *Experience elite performance with premium styling & instant action logs.*\n",
        color=0x2b2d31
    )
    embed.add_field(
        name="🛡️ **Moderation & Actions**", 
        value="`•` `.ban @user [reason]` - Ban user & send DM alert\n`•` `.to @user [reason]` - Timeout user for 30m & send DM notice\n`•` `.w @user [reason]` - Issue formal warning & DM notice\n`•` `.dm @user Title | Message` - Send custom premium embed DM", 
        inline=False
    )
    embed.add_field(
        name="🎫 **Ticket & Utilities**", 
        value="`•` `.ticketsetup` - Send interactive ticket panel (Menu + Button)\n`•` `.join` / `.leave` - Voice channel 24/7 utilities\n`•` `.snipe` - View deleted messages from last 24h", 
        inline=False
    )
    embed.set_footer(text="Spike.lol Security | Type .helps for menu")
    await ctx.reply(embed=embed)

# 3. .dm @user Title | Message
@bot.command(name="dm")
@commands.has_permissions(manage_messages=True)
async def prefix_dm(ctx, member: discord.Member = None, *, content: str = None):
    if not member or not content or "|" not in content:
        return await ctx.reply("❌ **Usage:** `.dm @user Title | Your Message Here`")
    
    parts = content.split("|", 1)
    title = parts[0].strip()
    msg = parts[1].strip()

    embed = discord.Embed(
        title=f"📩 {title}",
        description=msg,
        color=0x2b2d31
    )
    embed.add_field(name="👤 Sender", value=str(ctx.author), inline=True)
    embed.add_field(name="🏠 Server", value=ctx.guild.name, inline=True)
    embed.set_footer(text="⚡ Spike.lol Secure Dispatcher")

    try:
        await member.send(embed=embed)
        await ctx.reply(f"✅ Successfully dispatched DM embed to **{member.tag}**!")
    except Exception:
        await ctx.reply(f"⚠️ Could not send DM to **{member.tag}** (User DMs are closed, but action is logged).")

# 4. .to @user [reason] (Timeout System - 30 mins)
@bot.command(name="to")
@commands.has_permissions(moderate_members=True)
async def prefix_to(ctx, member: discord.Member = None, *, reason: str = "No reason provided"):
    if not member:
        return await ctx.reply("❌ **Usage:** `.to @user [reason]`")
    
    dm_embed = discord.Embed(
        title="⚠️ **YOU HAVE BEEN TIMED OUT**",
        description="> *You have received a 30-minute timeout in the server.*",
        color=0xffaa00
    )
    dm_embed.add_field(name="🏠 Server", value=ctx.guild.name, inline=False)
    dm_embed.add_field(name="🛡️ Action By", value=str(ctx.author), inline=False)
    dm_embed.add_field(name="📄 Reason", value=reason, inline=False)
    dm_embed.set_footer(text="⚡ Spike.lol Moderation System")

    try:
        await member.send(embed=dm_embed)
    except Exception:
        pass

    try:
        duration = datetime.timedelta(minutes=30)
        await member.timeout(duration, reason=reason)
        success_embed = discord.Embed(
            title="✅ **Action Success: Timeout**",
            description=f"Successfully timed out **{member.tag}** for 30 minutes and dispatched DM notification.",
            color=0x00ff00
        )
        await ctx.reply(embed=success_embed)
    except Exception as e:
        await ctx.reply(f"❌ Failed to apply timeout. Error: {e}")

# 5. .w @user [reason] (Warn System)
@bot.command(name="w")
@commands.has_permissions(manage_messages=True)
async def prefix_warn(ctx, member: discord.Member = None, *, reason: str = "No reason specified"):
    if not member:
        return await ctx.reply("❌ **Usage:** `.w @user [reason]`")
    
    dm_embed = discord.Embed(
        title="⚠️ **YOU HAVE BEEN WARNED**",
        description="> *Please follow server rules to avoid further penalties.*",
        color=0xffaa00
    )
    dm_embed.add_field(name="🏠 Server", value=ctx.guild.name, inline=False)
    dm_embed.add_field(name="🛡️ Warned By", value=str(ctx.author), inline=False)
    dm_embed.add_field(name="📄 Reason", value=reason, inline=False)
    dm_embed.set_footer(text="⚡ Spike.lol Official Warning")

    try:
        await member.send(embed=dm_embed)
    except Exception:
        pass

    success_embed = discord.Embed(
        title="✅ **Action Success: Warn**",
        description=f"Successfully issued warning to **{member.tag}** and dispatched DM notification.",
        color=0x00ff00
    )
    await ctx.reply(embed=success_embed)

# 6. .ban @user [reason]
@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def prefix_ban(ctx, member: discord.Member = None, *, reason: str = "No reason provided"):
    if not member:
        return await ctx.reply("❌ **Usage:** `.ban @user [reason]`")
    
    dm_embed = discord.Embed(
        title="🔨 **YOU HAVE BEEN BANNED**",
        color=0xff0000
    )
    dm_embed.add_field(name="🏠 Server", value=ctx.guild.name, inline=False)
    dm_embed.add_field(name="🛡️ Action By", value=str(ctx.author), inline=False)
    dm_embed.add_field(name="📄 Reason", value=reason, inline=False)
    dm_embed.set_footer(text="⚡ Spike.lol Ban System")
    
    try:
        await member.send(embed=dm_embed)
    except Exception:
        pass

    try:
        await member.ban(reason=reason)
        success_embed = discord.Embed(
            title="✅ **Action Success: Ban**",
            description=f"Successfully banned **{member.tag}** and dispatched DM notification.",
            color=0x00ff00
        )
        await ctx.reply(embed=success_embed)
    except Exception:
        await ctx.reply("❌ Failed to execute ban action.")

# 7. .snipe (Last 24h deleted messages)
@bot.command(name="snipe")
@commands.has_permissions(manage_messages=True)
async def prefix_snipe(ctx):
    guild_id = ctx.guild.id
    messages = snipe_storage.get(guild_id, [])

    if not messages:
        return await ctx.reply("📌 No deleted messages recorded in the last 24 hours.")

    description = ""
    for idx, m in enumerate(messages[:10], 1):
        description += f"**{idx}.** **{m['author']}** in `#{m['channel']}`:\n> {m['content']}\n\n"

    embed = discord.Embed(
        title="📋 **24-Hour Snipe Logs**",
        description=description,
        color=0x2b2d31
    )
    embed.set_footer(text=f"Showing latest {min(len(messages), 10)} deleted messages | Spike.lol")
    await ctx.reply(embed=embed)

# 8. .join (VC Join)
@bot.command(name="join")
async def join_vc(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        return await ctx.reply("❌ Pehle kisi Voice Channel (VC) me jaao bhai!")
    
    channel = ctx.author.voice.channel
    if ctx.voice_client:
        await ctx.voice_client.move_to(channel)
        return await ctx.reply(f"✅ Successfully moved to **{channel.name}**!")
    
    try:
        await channel.connect()
        await ctx.reply(f"🔊 Successfully joined **{channel.name}** for 24/7 vibe!")
    except Exception as e:
        await ctx.reply(f"❌ Error joining VC: {e}")

# 9. .leave (VC Leave)
@bot.command(name="leave")
async def leave_vc(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.reply("👋 Disconnected from Voice Channel.")
    else:
        await ctx.reply("❌ Bot is not in any VC!")

if __name__ == "__main__":
    bot.run(TOKEN)
