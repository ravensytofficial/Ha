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
# ---------------- MODERATION ----------------

@bot.tree.command(name="warn", description="Warn a member")
@app_commands.checks.has_permissions(moderate_members=True)
async def warn(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason provided"
):

    embed = discord.Embed(
        title="⚠️ Warning",
        description=f"You were warned in **{interaction.guild.name}**",
        color=discord.Color.orange()
    )

    embed.add_field(name="Reason", value=reason)

    try:
        await member.send(embed=embed)
    except:
        pass

    await interaction.response.send_message(
        f"⚠️ {member.mention} has been warned."
    )

# ---------------- LOCKDOWN ----------------

@bot.tree.command(name="lock", description="Lock the channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def lock(interaction: discord.Interaction):

    overwrite = interaction.channel.overwrites_for(
        interaction.guild.default_role
    )

    overwrite.send_messages = False

    await interaction.channel.set_permissions(
        interaction.guild.default_role,
        overwrite=overwrite
    )

    await interaction.response.send_message(
        "🔒 Channel locked."
    )

@bot.tree.command(name="unlock", description="Unlock the channel")
@app_commands.checks.has_permissions(manage_channels=True)
async def unlock(interaction: discord.Interaction):

    overwrite = interaction.channel.overwrites_for(
        interaction.guild.default_role
    )

    overwrite.send_messages = True

    await interaction.channel.set_permissions(
        interaction.guild.default_role,
        overwrite=overwrite
    )

    await interaction.response.send_message(
        "🔓 Channel unlocked."
    )

# ---------------- CLEAR ----------------

@bot.tree.command(name="clear", description="Delete messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(
    interaction: discord.Interaction,
    amount: int
):

    await interaction.response.defer(ephemeral=True)

    deleted = await interaction.channel.purge(limit=amount)

    await interaction.followup.send(
        f"🧹 Deleted {len(deleted)} messages.",
        ephemeral=True
    )

# ---------------- MUTE ----------------

@bot.tree.command(name="mute", description="Timeout a member")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(
    interaction: discord.Interaction,
    member: discord.Member,
    minutes: int,
    reason: str = "No reason provided"
):

    from datetime import timedelta

    await member.timeout(
        timedelta(minutes=minutes),
        reason=reason
    )

    await interaction.response.send_message(
        f"🔇 {member.mention} muted for {minutes} minutes."
    )

# ---------------- UNMUTE ----------------

@bot.tree.command(name="unmute", description="Remove timeout")
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute(
    interaction: discord.Interaction,
    member: discord.Member
):

    await member.timeout(None)

    await interaction.response.send_message(
        f"🔊 {member.mention} unmuted."
    )

# ---------------- SETADMIN ----------------

@bot.tree.command(name="setadmin", description="Give admin role")
@app_commands.checks.has_permissions(administrator=True)
async def setadmin(
    interaction: discord.Interaction,
    member: discord.Member
):

    role = discord.utils.get(
        interaction.guild.roles,
        permissions=discord.Permissions(administrator=True)
    )

    if role is None:
        return await interaction.response.send_message(
            "❌ No admin role found."
        )

    await member.add_roles(role)

    await interaction.response.send_message(
        f"👑 {member.mention} is now admin."
    )

# ---------------- SLOWMODE ----------------

@bot.tree.command(name="slowmode", description="Set slowmode")
@app_commands.checks.has_permissions(manage_channels=True)
async def slowmode(
    interaction: discord.Interaction,
    seconds: int
):

    await interaction.channel.edit(
        slowmode_delay=seconds
    )

    await interaction.response.send_message(
        f"🐢 Slowmode set to {seconds}s."
    )

# ---------------- NICK ----------------

@bot.tree.command(name="nick", description="Change nickname")
@app_commands.checks.has_permissions(manage_nicknames=True)
async def nick(
    interaction: discord.Interaction,
    member: discord.Member,
    nickname: str
):

    await member.edit(nick=nickname)

    await interaction.response.send_message(
        f"✏️ Changed nickname for {member.mention}"
    )

# ---------------- SAY ----------------

@bot.tree.command(name="say", description="Make the bot say something")
@app_commands.checks.has_permissions(manage_messages=True)
async def say(
    interaction: discord.Interaction,
    message: str
):

    await interaction.response.send_message(
        "✅ Sent.",
        ephemeral=True
    )

    await interaction.channel.send(message)

# ---------------- EMBED ----------------

@bot.tree.command(name="embed", description="Create an embed")
@app_commands.checks.has_permissions(manage_messages=True)
async def embed(
    interaction: discord.Interaction,
    title: str,
    description: str
):

    em = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.blurple()
    )

    await interaction.response.send_message(embed=em)

# ---------------- SERVER ICON ----------------

@bot.tree.command(name="servericon", description="Show server icon")
async def servericon(interaction: discord.Interaction):

    if interaction.guild.icon:

        embed = discord.Embed(
            title=f"{interaction.guild.name} Icon",
            color=discord.Color.blurple()
        )

        embed.set_image(url=interaction.guild.icon.url)

        await interaction.response.send_message(embed=embed)

# ---------------- MEMBER COUNT ----------------

@bot.tree.command(name="membercount", description="Show member count")
async def membercount(interaction: discord.Interaction):

    await interaction.response.send_message(
        f"👥 Members: {interaction.guild.member_count}"
    )
# ---------------- RUN ---------------- #

bot.run(os.getenv("TOKEN"))
