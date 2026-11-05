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

# Snipe storage
snipe_storage = {}

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


# --- COMMANDS ---

# 1. .helps Command
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
        name="🔊 **Voice & Utilities**", 
        value="`•` `.join` / `.leave` - Voice channel 24/7 utilities\n`•` `.snipe` - View deleted messages from last 24h", 
        inline=False
    )
    embed.set_footer(text="Spike.lol Security | Type .helps for menu")
    await ctx.reply(embed=embed)

# 2. .dm @user Title | Message
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

# 3. .to @user [reason] (Timeout System - 30 mins)
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

# 4. .w @user [reason] (Warn System)
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

# 5. .ban @user [reason]
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

# 6. .snipe (Last 24h deleted messages)
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

# 7. .join (VC Join)
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

# 8. .leave (VC Leave)
@bot.command(name="leave")
async def leave_vc(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.reply("👋 Disconnected from Voice Channel.")
    else:
        await ctx.reply("❌ Bot is not in any VC!")

if __name__ == "__main__":
    bot.run(TOKEN)
