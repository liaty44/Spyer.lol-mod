import os
import json
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

load_dotenv()
TOKEN = os.getenv("TOKEN")

# Render Port Binding Keep-Alive HTTP Server
app = Flask('')

@app.route('/')
def home():
    main_port = os.getenv("PORT", "3000")
    return f"Bot is Alive and Running Live 24/7 on Port {main_port}!"

def run_web():
    port = int(os.getenv("PORT", 3000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

keep_alive()

# Discord Bot Setup (help_command=None added to fix the crash)
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.dm_messages = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)

# Database Setup for Autoresponder
DB_FILE = "src/database.json"
if not os.path.exists("src"):
    os.makedirs("src")
if not os.path.exists(DB_FILE):
    with open(DB_FILE, "w") as f:
        json.dump({"autoresponders": {}}, f, indent=4)

def load_db():
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

@bot.event
async def on_ready():
    print(f"[BOT] Logged in as {bot.user.tag}!")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="ADVANCED SOON FEAUTURES | .help"))
    try:
        synced = await bot.tree.sync()
        print(f"[SLASH] Synced {len(synced)} commands successfully.")
    except Exception as e:
        print(f"[SLASH ERROR] {e}")

# Autoresponder Listener & Prefix Command Handler
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Autoresponder Check
    db = load_db()
    guild_id = str(message.guild.id) if message.guild else None
    if guild_id and guild_id in db["autoresponders"]:
        for keyword, data in db["autoresponders"][guild_id].items():
            content = message.content.lower()
            kw = keyword.lower()
            matched = False
            if data["matchmode"] == "exact" and content == kw:
                matched = True
            elif data["matchmode"] == "contains" and kw in content:
                matched = True
            
            if matched:
                embed = discord.Embed(
                    title=data["title"],
                    description=data["description"],
                    color=0x2b2d31
                )
                embed.set_footer(text="⚡ VIP Autoresponder")
                await message.reply(embed=embed)
                return

    await bot.process_commands(message)

# 1. .help Command
@bot.command(name="help")
async def help_cmd(ctx):
    embed = discord.Embed(
        title="✨ 𝐕𝐈𝐏 𝐌𝐎𝐃𝐄𝐑𝐀𝐓𝐈𝐎𝐍 & 𝐔𝐓𝐈𝐋𝐈𝐓𝐘 𝐇𝐄𝐋𝐏 ✨",
        description="`⚡` Premium embeds & automated DM notifications enabled.",
        color=0x2b2d31
    )
    embed.add_field(name="🛡️ Moderation Actions", value="`.ban @user [reason]`\n`.kick @user [reason]`", inline=False)
    embed.add_field(name="💬 Direct Messaging", value="`.dm @user [message]`", inline=False)
    embed.add_field(name="🤖 Slash Features", value="Use `/to`, `/dm`, and `/autoresponse` for rich interactive menus.", inline=False)
    embed.set_footer(text="ADVANCED SOON FEAUTURES | .help")
    await ctx.reply(embed=embed)

# 2. .dm @user [msg]
@bot.command(name="dm")
@commands.has_permissions(manage_messages=True)
async def prefix_dm(ctx, member: discord.Member = None, *, text: str = None):
    if not member or not text:
        return await ctx.reply("⚠️ Usage: `.dm @user [message]`")
    try:
        embed = discord.Embed(
            title="📩 Direct Message Received",
            description=text,
            color=0x2b2d31
        )
        embed.add_field(name="👤 Sender", value=str(ctx.author))
        embed.add_field(name="🏰 Server", value=ctx.guild.name)
        embed.set_footer(text="⚡ Secure DM Dispatcher")
        await member.send(embed=embed)
        await ctx.reply(f"✅ Successfully sent DM to **{member.tag}**.")
    except Exception:
        await ctx.reply("❌ Could not send DM to this user (DMs might be closed).")

# 3. .ban @user [reason]
@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def prefix_ban(ctx, member: discord.Member = None, *, reason: str = "No reason provided"):
    if not member:
        return await ctx.reply("⚠️ Usage: `.ban @user [reason]`")
    try:
        dm_embed = discord.Embed(
            title="🔨 You have been BANNED",
            color=0xff0000
        )
        dm_embed.add_field(name="🏰 Server", value=ctx.guild.name)
        dm_embed.add_field(name="⚖️ Action By", value=str(ctx.author))
        dm_embed.add_field(name="📄 Reason", value=reason)
        await member.send(embed=dm_embed)
    except Exception:
        pass

    try:
        await member.ban(reason=reason)
        success_embed = discord.Embed(
            title="✅ Action Success: Ban",
            description=f"Successfully banned **{member.tag}** and dispatched DM notification.",
            color=0x00ff00
        )
        await ctx.reply(embed=success_embed)
    except Exception:
        await ctx.reply("❌ Failed to execute ban action.")

# --- SLASH COMMANDS ---

@bot.tree.command(name="to", description="Action user with automated direct message reason notification")
@app_commands.describe(user="Target user", reason="Reason for action")
async def slash_to(interaction: discord.Interaction, user: discord.Member, reason: str):
    if not interaction.user.guild_permissions.moderate_members:
        return await interaction.response.send_message("❌ Missing permissions.", ephemeral=True)
    
    dm_embed = discord.Embed(
        title="⚠️ Moderation Action Notice",
        color=0xffaa00
    )
    dm_embed.add_field(name="🏰 Server", value=interaction.guild.name)
    dm_embed.add_field(name="🛡️ Action By", value=str(interaction.user))
    dm_embed.add_field(name="📄 Reason", value=reason)

    try:
        await user.send(embed=dm_embed)
        await interaction.response.send_message(f"✅ Action logged and DM successfully dispatched to **{user.tag}** with reason!", ephemeral=True)
    except Exception:
        await interaction.response.send_message(f"⚠️ Action processed, but could not send DM to **{user.tag}** (DMs closed).", ephemeral=True)

@bot.tree.command(name="dm", description="Send a custom premium embed DM to a user")
@app_commands.describe(user="Target user", title="Embed Title", message="Embed Message content")
async def slash_dm(interaction: discord.Interaction, user: discord.Member, title: str, message: str):
    if not interaction.user.guild_permissions.manage_messages:
        return await interaction.response.send_message("❌ Missing permissions.", ephemeral=True)

    embed = discord.Embed(
        title=title,
        description=message,
        color=0x2b2d31
    )
    embed.set_footer(text=f"From {interaction.guild.name}")

    try:
        await user.send(embed=embed)
        await interaction.response.send_message(f"✅ Custom embed DM sent to **{user.tag}**!", ephemeral=True)
    except Exception:
        await interaction.response.send_message("❌ Failed to send DM.", ephemeral=True)

# Autoresponse Slash Command Group
autoresponse_group = app_commands.Group(name="autoresponse", description="Manage custom autoresponders")

@autoresponse_group.command(name="add", description="Add an autoresponse keyword")
@app_commands.describe(keyword="Trigger keyword", title="Embed Title", description="Embed Description", matchmode="Match Mode")
@app_commands.choices(matchmode=[
    app_commands.Choice(name="Exact Match", value="exact"),
    app_commands.Choice(name="Contains Keyword", value="contains")
])
async def ar_add(interaction: discord.Interaction, keyword: str, title: str, description: str, matchmode: str):
    if not interaction.user.guild_permissions.manage_guild:
        return await interaction.response.send_message("❌ Missing Manage Server permissions.", ephemeral=True)
    
    db = load_db()
    guild_id = str(interaction.guild.id)
    if guild_id not in db["autoresponders"]:
        db["autoresponders"][guild_id] = {}
    
    db["autoresponders"][guild_id][keyword.lower()] = {
        "title": title,
        "description": description,
        "matchmode": matchmode
    }
    save_db(db)

    embed = discord.Embed(
        title="🤖 Autoresponder Added",
        color=0x00ff00
    )
    embed.add_field(name="🔑 Keyword", value=keyword, inline=False)
    embed.add_field(name="🎯 Match Mode", value=matchmode, inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@autoresponse_group.command(name="list", description="List all server autoresponses")
async def ar_list(interaction: discord.Interaction):
    db = load_db()
    guild_id = str(interaction.guild.id)
    entries = db["autoresponders"].get(guild_id, {})
    
    if not entries:
        return await interaction.response.send_message("📂 No autoresponses configured yet.", ephemeral=True)
    
    list_text = "\n".join([f"• `{k}` ({v['matchmode']})" for k, v in entries.items()])
    embed = discord.Embed(
        title="📋 Server Autoresponders",
        description=list_text,
        color=0x2b2d31
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

@autoresponse_group.command(name="delete", description="Delete an autoresponse keyword")
@app_commands.describe(keyword="Keyword to delete")
async def ar_delete(interaction: discord.Interaction, keyword: str):
    if not interaction.user.guild_permissions.manage_guild:
        return await interaction.response.send_message("❌ Missing permissions.", ephemeral=True)
    
    db = load_db()
    guild_id = str(interaction.guild.id)
    if guild_id not in db["autoresponders"] or keyword.lower() not in db["autoresponders"][guild_id]:
        return await interaction.response.send_message("❌ Keyword not found.", ephemeral=True)
    
    del db["autoresponders"][guild_id][keyword.lower()]
    save_db(db)
    await interaction.response.send_message(f"🗑️ Deleted autoresponse for keyword: `{keyword}`", ephemeral=True)

bot.tree.add_command(autoresponse_group)

if __name__ == "__main__":
    bot.run(TOKEN)
