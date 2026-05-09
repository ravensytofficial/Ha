import discord
from discord.ext import commands
from discord import app_commands
import os
from datetime import datetime

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

warnings = {}
admin_roles = {}

# ---------------- READY ---------------- #

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ Logged in as {bot.user}")
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print(f"❌ Sync Error: {e}")

# ---------------- PING ---------------- #

@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)

    embed = discord.Embed(
        title="🏓 Pong!",
        color=discord.Color.blurple()
    )

    embed.add_field(name="Latency", value=f"`{latency}ms`")

    await interaction.response.send_message(embed=embed)

# ---------------- PURGE ---------------- #

@bot.tree.command(name="purge", description="Delete messages")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.describe(amount="Messages to delete")
async def purge(interaction: discord.Interaction, amount: int):

    if amount < 1 or amount > 100:
        return await interaction.response.send_message(
            "Amount must be between 1-100.",
            ephemeral=True
        )

    await interaction.response.defer(ephemeral=True)

    deleted = await interaction.channel.purge(limit=amount)

    await interaction.followup.send(
        f"🧹 Deleted {len(deleted)} messages.",
        ephemeral=True
    )

# ---------------- KICK ---------------- #

@bot.tree.command(name="kick", description="Kick a member")
@app_commands.checks.has_permissions(kick_members=True)
@app_commands.describe(member="Member to kick", reason="Reason")
async def kick(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason provided"
):

    if member == interaction.user:
        return await interaction.response.send_message(
            "❌ You can't kick yourself.",
            ephemeral=True
        )

    await member.kick(reason=reason)

    embed = discord.Embed(
        title="👢 Member Kicked",
        color=discord.Color.red()
    )

    embed.add_field(name="User", value=member.mention)
    embed.add_field(name="Reason", value=reason)

    await interaction.response.send_message(embed=embed)

# ---------------- BAN ---------------- #

@bot.tree.command(name="ban", description="Ban a member")
@app_commands.checks.has_permissions(ban_members=True)
@app_commands.describe(member="Member to ban", reason="Reason")
async def ban(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason provided"
):

    if member == interaction.user:
        return await interaction.response.send_message(
            "❌ You can't ban yourself.",
            ephemeral=True
        )

    await member.ban(reason=reason)

    embed = discord.Embed(
        title="🔨 Member Banned",
        color=discord.Color.red()
    )

    embed.add_field(name="User", value=member.mention)
    embed.add_field(name="Reason", value=reason)

    await interaction.response.send_message(embed=embed)

# ---------------- UNBAN ---------------- #

@bot.tree.command(name="unban", description="Unban a user")
@app_commands.checks.has_permissions(ban_members=True)
@app_commands.describe(user_id="User ID")
async def unban(interaction: discord.Interaction, user_id: str):

    try:
        user = await bot.fetch_user(int(user_id))
        await interaction.guild.unban(user)

        await interaction.response.send_message(
            f"✅ Unbanned {user}"
        )

    except:
        await interaction.response.send_message(
            "❌ Invalid user ID.",
            ephemeral=True
        )

# ---------------- SOFTBAN ---------------- #

@bot.tree.command(name="softban", description="Softban a member")
@app_commands.checks.has_permissions(ban_members=True)
@app_commands.describe(member="Member", reason="Reason")
async def softban(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason provided"
):

    if member == interaction.user:
        return await interaction.response.send_message(
            "❌ You can't softban yourself.",
            ephemeral=True
        )

    await member.ban(reason=reason, delete_message_days=7)
    await interaction.guild.unban(member)

    embed = discord.Embed(
        title="🧽 Softban",
        description=f"{member.mention} was softbanned.",
        color=discord.Color.orange()
    )

    embed.add_field(name="Reason", value=reason)

    await interaction.response.send_message(embed=embed)

# ---------------- WARN ---------------- #

@bot.tree.command(name="warn", description="Warn a member")
@app_commands.checks.has_permissions(moderate_members=True)
@app_commands.describe(member="Member", reason="Reason")
async def warn(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason provided"
):

    guild_id = interaction.guild.id

    if guild_id not in warnings:
        warnings[guild_id] = {}

    if member.id not in warnings[guild_id]:
        warnings[guild_id][member.id] = []

    warnings[guild_id][member.id].append(reason)

    embed = discord.Embed(
        title="⚠️ Warning",
        color=discord.Color.yellow()
    )

    embed.add_field(name="Server", value=interaction.guild.name)
    embed.add_field(name="Reason", value=reason)

    try:
        await member.send(embed=embed)
    except:
        pass

    await interaction.response.send_message(
        f"⚠️ Warned {member.mention}"
    )

# ---------------- WARNS ---------------- #

@bot.tree.command(name="warnings", description="View warnings")
@app_commands.describe(member="Member")
async def warnings_cmd(
    interaction: discord.Interaction,
    member: discord.Member
):

    guild_id = interaction.guild.id

    user_warnings = warnings.get(guild_id, {}).get(member.id, [])

    if not user_warnings:
        return await interaction.response.send_message(
            "✅ No warnings."
        )

    embed = discord.Embed(
        title=f"Warnings for {member}",
        color=discord.Color.orange()
    )

    for i, warn_reason in enumerate(user_warnings, start=1):
        embed.add_field(
            name=f"Warning {i}",
            value=warn_reason,
            inline=False
        )

    await interaction.response.send_message(embed=embed)

# ---------------- SETADMIN ---------------- #

@bot.tree.command(name="setadmin", description="Set admin role")
@app_commands.checks.has_permissions(administrator=True)
@app_commands.describe(role="Role to set as admin")
async def setadmin(
    interaction: discord.Interaction,
    role: discord.Role
):

    admin_roles[interaction.guild.id] = role.id

    await interaction.response.send_message(
        f"✅ {role.mention} is now admin role."
    )

# ---------------- AVATAR ---------------- #

@bot.tree.command(name="avatar", description="Show avatar")
@app_commands.describe(user="User")
async def avatar(
    interaction: discord.Interaction,
    user: discord.Member = None
):

    user = user or interaction.user

    embed = discord.Embed(
        title=f"{user.display_name}'s Avatar",
        color=discord.Color.blurple()
    )

    embed.set_image(url=user.display_avatar.url)

    await interaction.response.send_message(embed=embed)

# ---------------- USERINFO ---------------- #

@bot.tree.command(name="userinfo", description="User info")
@app_commands.describe(user="User")
async def userinfo(
    interaction: discord.Interaction,
    user: discord.Member = None
):

    user = user or interaction.user

    embed = discord.Embed(
        title=f"👤 {user}",
        color=discord.Color.blurple()
    )

    embed.set_thumbnail(url=user.display_avatar.url)

    embed.add_field(name="ID", value=user.id)
    embed.add_field(
        name="Joined",
        value=user.joined_at.strftime("%Y-%m-%d")
    )

    embed.add_field(
        name="Created",
        value=user.created_at.strftime("%Y-%m-%d")
    )

    await interaction.response.send_message(embed=embed)

# ---------------- SERVERINFO ---------------- #

@bot.tree.command(name="serverinfo", description="Server info")
async def serverinfo(interaction: discord.Interaction):

    guild = interaction.guild

    embed = discord.Embed(
        title=guild.name,
        color=discord.Color.blurple()
    )

    embed.add_field(name="Members", value=guild.member_count)
    embed.add_field(name="Owner", value=guild.owner)
    embed.add_field(
        name="Created",
        value=guild.created_at.strftime("%Y-%m-%d")
    )

    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)

    await interaction.response.send_message(embed=embed)

# ---------------- ABOUT ---------------- #

@bot.tree.command(name="about", description="About bot")
async def about(interaction: discord.Interaction):

    embed = discord.Embed(
        title="🤖 About",
        description="Advanced moderation bot.",
        color=discord.Color.blurple()
    )

    embed.add_field(name="Developer", value="You 😎")
    embed.add_field(name="Library", value="discord.py 2.x")

    await interaction.response.send_message(embed=embed)

# ---------------- ERRORS ---------------- #

@bot.event
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError
):

    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ Missing permissions.",
            ephemeral=True
        )

    elif isinstance(error, app_commands.BotMissingPermissions):
        await interaction.response.send_message(
            "❌ Bot missing permissions.",
            ephemeral=True
        )

    else:
        try:
            await interaction.response.send_message(
                f"❌ Error: {error}",
                ephemeral=True
            )
        except:
            pass

# ---------------- RUN ---------------- #

bot.run(os.getenv("TOKEN"))
