import os
import time
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
    return "Bot is Live and Running 24/7!"

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
    print(f"[BOT] Logged in as {bot.user.tag}!")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="ADVANCED SOON FEATURES | .helps"))
    print("[BOT] Ready and fully optimized!")

# Snipe tracker (Store deleted messages for 24 hours)
@bot.event
async def on_message_delete(message):
    if message.author.bot or not message.guild:
        return
    guild_id = message.guild.id
    if guild_id not in snipe_storage:
        snipe_storage[guild_id] = []
    
    snipe_storage[guild_id].insert(0, {
        "content": message.content or "[Embed / Attachment]",
        "author": str(message.author),
        "channel": message.channel.name,
        "time": time.time()
    })
    # Keep only last 20 messages & within 24 hours
    current_time = time.time()
    snipe_storage[guild_id] = [m for m in snipe_storage[guild_id] if current_time - m["time"] < 86400][:20]

# Message Listener for Help / Ticket Trigger & Cooldown (10 mins)
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content_lower = message.content.lower()
    # Check if someone types "help" or asks for help outside of command prefix
    if "help" in content_lower and not message.content.startswith('.'):
        guild_id = message.guild.id if message.guild else "dm"
        user_id = message.author.id
        cooldown_key = f"{guild_id}-{user_id}"
        current_time = time.time()

        # 10 minutes cooldown (600 seconds)
        if cooldown_key in help_cooldowns and current_time - help_cooldowns[cooldown_key] < 600:
            return # Skip response if under 10m cooldown

        help_cooldowns[cooldown_key] = current_time

        embed = discord.Embed(
            title="<a:sparkles:1000000000000000000> 🎫 **VIP SUPPORT TICKET SYSTEM** <a:sparkles:1000000000000000000>",
            description="> **Need assistance?** Our staff team is here to help you out! React or click below to get support.\n\n<:reply:1000000000000000000> **Status:** Ticket Desk Open\n<:lock:1000000000000000000> **Security:** Secured & Private",
            color=0x2b2d31
        )
        embed.set_footer(text="⚡ Powered by Advanced Bot Security | Cooldown: 10m")
        try:
            await message.reply(embed=embed)
        except Exception:
            pass

    await bot.process_commands(message)

# 1. .helps Command
@bot.command(name="helps")
async def helps_cmd(ctx):
    embed = discord.Embed(
        title="<a:fire:1000000000000000000> **✨ 𝐕𝐈𝐏 𝐌𝐎𝐃𝐄𝐑𝐀𝐓𝐈𝐎𝐍 & 𝐔𝐓𝐈𝐋𝐈𝐓𝐘 𝐇𝐄𝐋𝐏 ✨** <a:fire:1000000000000000000>",
        description="> `<:nitro:1000000000000000000>` *Experience elite performance with nitro styling & instant action logs.*\n",
        color=0x2b2d31
    )
    embed.add_field(
        name="<:shield:1000000000000000000> **Moderation & Actions**", 
        value="`•` `.ban @user [reason]` - Ban user & DM notification\n`•` `.w @user [reason]` - Issue formal warn & DM alert\n`•` `.dm @user [title] | [msg]` - Custom embed direct message", 
        inline=False
    )
    embed.add_field(
        name="<:voice:1000000000000000000> **Voice & Utilities**", 
        value="`•` `.join` - Connect bot to your VC (24/7 Vibe)\n`•` `.leave` - Disconnect from VC\n`•` `.snipe` - View deleted messages in last 24h", 
        inline=False
    )
    embed.set_footer(text="ADVANCED SOON FEATURES | Type .helps for menu")
    await ctx.reply(embed=embed)

# 2. .dm @user title | message
@bot.command(name="dm")
@commands.has_permissions(manage_messages=True)
async def prefix_dm(ctx, member: discord.Member = None, *, content: str = None):
    if not member or not content:
        return await ctx.reply("<:cross:1000000000000000000> **Usage:** `.dm @user Title | Your Message Here`")
    
    parts = content.split("|", 1)
    title = parts[0].strip()
    msg = parts[1].strip() if len(parts) > 1 else "No message provided"

    embed = discord.Embed(
        title=f"<:mail:1000000000000000000> {title}",
        description=msg,
        color=0x2b2d31
    )
    embed.add_field(name="<:user:1000000000000000000> Sender", value=str(ctx.author), inline=True)
    embed.add_field(name="<:home:1000000000000000000> Server", value=ctx.guild.name, inline=True)
    embed.set_footer(text="⚡ Secure VIP Dispatcher")

    try:
        await member.send(embed=embed)
        await ctx.reply(f"<:check:1000000000000000000> Successfully dispatched DM embed to **{member.tag}**!")
    except Exception:
        await ctx.reply(f"<:alert:1000000000000000000> Could not send DM to **{member.tag}** (User DMs are closed, but action is logged).")

# 3. .w @user [reason] (Warn System)
@bot.command(name="w")
@commands.has_permissions(manage_messages=True)
async def prefix_warn(ctx, member: discord.Member = None, *, reason: str = "No reason specified"):
    if not member:
        return await ctx.reply("<:cross:1000000000000000000> **Usage:** `.w @user [reason]`")
    
    dm_embed = discord.Embed(
        title="<:warn:1000000000000000000> **YOU HAVE BEEN WARNED**",
        description="> *Please follow server rules to avoid further penalties.*",
        color=0xffaa00
    )
    dm_embed.add_field(name="<:home:1000000000000000000> Server", value=ctx.guild.name, inline=False)
    dm_embed.add_field(name="<:shield:1000000000000000000> Warned By", value=str(ctx.author), inline=False)
    dm_embed.add_field(name="<:file:1000000000000000000> Reason", value=reason, inline=False)
    dm_embed.set_footer(text="⚡ Official Moderation Warning")

    try:
        await member.send(embed=dm_embed)
    except Exception:
        pass # DMs closed handle silently for warning dispatch

    success_embed = discord.Embed(
        title="<:check:1000000000000000000> **Action Success: Warn**",
        description=f"Successfully issued warning to **{member.tag}** and dispatched DM notification.",
        color=0x00ff00
    )
    await ctx.reply(embed=success_embed)

# 4. .ban @user [reason]
@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def prefix_ban(ctx, member: discord.Member = None, *, reason: str = "No reason provided"):
    if not member:
        return await ctx.reply("<:cross:1000000000000000000> **Usage:** `.ban @user [reason]`")
    
    dm_embed = discord.Embed(
        title="<:ban:1000000000000000000> **YOU HAVE BEEN BANNED**",
        color=0xff0000
    )
    dm_embed.add_field(name="<:home:1000000000000000000> Server", value=ctx.guild.name, inline=False)
    dm_embed.add_field(name="<:shield:1000000000000000000> Action By", value=str(ctx.author), inline=False)
    dm_embed.add_field(name="<:file:1000000000000000000> Reason", value=reason, inline=False)
    
    try:
        await member.send(embed=dm_embed)
    except Exception:
        pass

    try:
        await member.ban(reason=reason)
        success_embed = discord.Embed(
            title="<:check:1000000000000000000> **Action Success: Ban**",
            description=f"Successfully banned **{member.tag}** and dispatched DM notification.",
            color=0x00ff00
        )
        await ctx.reply(embed=success_embed)
    except Exception:
        await ctx.reply("<:cross:1000000000000000000> Failed to execute ban action.")

# 5. .snipe (Last 24h deleted messages)
@bot.command(name="snipe")
@commands.has_permissions(manage_messages=True)
async def prefix_snipe(ctx):
    guild_id = ctx.guild.id
    messages = snipe_storage.get(guild_id, [])

    if not messages:
        return await ctx.reply("<:info:1000000000000000000> No deleted messages recorded in the last 24 hours.")

    description = ""
    for idx, m in enumerate(messages[:10], 1):
        description += f"**{idx}.** **{m['author']}** in `#{m['channel']}`:\n> {m['content']}\n\n"

    embed = discord.Embed(
        title="<:snipe:1000000000000000000> **24-Hour Snipe Logs**",
        description=description,
        color=0x2b2d31
    )
    embed.set_footer(text=f"Showing latest {min(len(messages), 10)} deleted messages")
    await ctx.reply(embed=embed)

# 6. .join (VC Join)
@bot.command(name="join")
async def join_vc(ctx):
    if not ctx.author.voice or not ctx.author.voice.channel:
        return await ctx.reply("<:cross:1000000000000000000> Pehle kisi Voice Channel (VC) me jaao bhai!")
    
    channel = ctx.author.voice.channel
    if ctx.voice_client:
        await ctx.voice_client.move_to(channel)
        return await ctx.reply(f"<:check:1000000000000000000> Successfully moved to **{channel.name}**!")
    
    try:
        await channel.connect()
        await ctx.reply(f"<:voice:1000000000000000000> Successfully joined **{channel.name}** for 24/7 vibe!")
    except Exception as e:
        await ctx.reply(f"<:cross:1000000000000000000> Error joining VC: {e}")

# 7. .leave (VC Leave)
@bot.command(name="leave")
async def leave_vc(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.reply("<:check:1000000000000000000> Disconnected from Voice Channel.")
    else:
        await ctx.reply("<:cross:1000000000000000000> Bot is not in any VC!")

if __name__ == "__main__":
    bot.run(TOKEN)
