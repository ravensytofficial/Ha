import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
from captcha.image import ImageCaptcha

import os
import random
import string
from datetime import timedelta

# ---------------- BOT SETUP ---------------- #

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

warnings = {}
captcha_codes = {}

ALLOWED_ROLES = [
    "Owner",
    "Admin",
    "Staff"
]

# ---------------- READY ---------------- #

@bot.event
async def on_ready():

    try:
        synced = await bot.tree.sync()

        print(f"✅ Logged in as {bot.user}")
        print(f"✅ Synced {len(synced)} commands")

    except Exception as e:
        print(f"❌ Sync Error: {e}")

# ---------------- CAPTCHA ---------------- #

class VerifyView(View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Verify",
        style=discord.ButtonStyle.green
    )
    async def verify_button(
        self,
        interaction: discord.Interaction,
        button: Button
    ):

        code = ''.join(
            random.choices(
                string.ascii_uppercase + string.digits,
                k=5
            )
        )

        captcha = ImageCaptcha(
            width=280,
            height=90
        )

        image_path = f"{interaction.user.id}.png"

        captcha.write(code, image_path)

        captcha_codes[interaction.user.id] = code

        await interaction.response.send_message(
            "Type the CAPTCHA below.",
            file=discord.File(image_path),
            ephemeral=True
        )

@bot.tree.command(
    name="setupverify",
    description="Setup verification system"
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def setupverify(
    interaction: discord.Interaction
):

    embed = discord.Embed(
        title="🔒 Verification",
        description="Press the button below to verify.",
        color=discord.Color.blurple()
    )

    await interaction.channel.send(
        embed=embed,
        view=VerifyView()
    )

    await interaction.response.send_message(
        "✅ Verification setup complete.",
        ephemeral=True
    )

@bot.event
async def on_message(message):

    if message.author.bot:
        return

    if message.author.id in captcha_codes:

        if (
            message.content.upper()
            ==
            captcha_codes[message.author.id]
        ):

            role = discord.utils.get(
                message.guild.roles,
                name="Verified"
            )

            if role:
                await message.author.add_roles(role)

            del captcha_codes[message.author.id]

            await message.channel.send(
                f"✅ {message.author.mention} verified."
            )

        else:

            await message.channel.send(
                "❌ Wrong CAPTCHA."
            )

    await bot.process_commands(message)

# ---------------- FORUM TICKETS ---------------- #

class CloseTicketView(View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Close Ticket",
        style=discord.ButtonStyle.red
    )
    async def close_ticket(
        self,
        interaction: discord.Interaction,
        button: Button
    ):

        allowed = False

        for role in interaction.user.roles:

            if role.name in ALLOWED_ROLES:
                allowed = True
                break

        if not allowed:

            return await interaction.response.send_message(
                "❌ Staff only.",
                ephemeral=True
            )

        messages = []

        async for msg in interaction.channel.history(
            limit=None,
            oldest_first=True
        ):

            timestamp = msg.created_at.strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            content = msg.content

            if not content:
                content = "[Embed/Attachment]"

            messages.append(
                f"[{timestamp}] {msg.author}: {content}"
            )

        transcript_text = "\n".join(messages)

        transcript_file = (
            f"{interaction.channel.name}.txt"
        )

        with open(
            transcript_file,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(transcript_text)

        transcript_channel = discord.utils.get(
            interaction.guild.text_channels,
            name="ticket-transcripts"
        )

        await interaction.response.send_message(
            "🗑️ Closing ticket..."
        )

        if transcript_channel:

            await transcript_channel.send(
                content=(
                    f"📁 Transcript from "
                    f"{interaction.channel.name}"
                ),
                file=discord.File(transcript_file)
            )

        await interaction.channel.delete()

class TicketView(View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Create Ticket",
        style=discord.ButtonStyle.blurple
    )
    async def ticket_button(
        self,
        interaction: discord.Interaction,
        button: Button
    ):

        forum = discord.utils.get(
            interaction.guild.forums,
            name="tickets"
        )

        if forum is None:

            return await interaction.response.send_message(
                "❌ Create a forum channel named 'tickets'",
                ephemeral=True
            )

        embed = discord.Embed(
            title="🎫 Support Ticket",
            description="Explain your issue here.",
            color=discord.Color.green()
        )

        thread = await forum.create_thread(
            name=f"{interaction.user.name}-ticket",
            content=(
                f"{interaction.user.mention} "
                f"created a ticket."
            ),
            embed=embed
        )

        await thread.thread.send(
            embed=embed,
            view=CloseTicketView()
        )

        await interaction.response.send_message(
            (
                f"✅ Ticket created: "
                f"{thread.thread.mention}"
            ),
            ephemeral=True
        )

@bot.tree.command(
    name="setuptickets",
    description="Setup forum tickets"
)
@app_commands.checks.has_permissions(
    administrator=True
)
async def setuptickets(
    interaction: discord.Interaction
):

    embed = discord.Embed(
        title="🎫 Support",
        description=(
            "Press the button below "
            "to create a ticket."
        ),
        color=discord.Color.blurple()
    )

    await interaction.channel.send(
        embed=embed,
        view=TicketView()
    )

    await interaction.response.send_message(
        "✅ Ticket system setup complete.",
        ephemeral=True
    )

# ---------------- PING ---------------- #

@bot.tree.command(
    name="ping",
    description="Check latency"
)
async def ping(
    interaction: discord.Interaction
):

    latency = round(bot.latency * 1000)

    embed = discord.Embed(
        title="🏓 Pong!",
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="Latency",
        value=f"{latency}ms"
    )

    await interaction.response.send_message(
        embed=embed
    )

# ---------------- PURGE ---------------- #

@bot.tree.command(
    name="purge",
    description="Delete messages"
)
@app_commands.checks.has_permissions(
    manage_messages=True
)
async def purge(
    interaction: discord.Interaction,
    amount: int
):

    if amount < 1 or amount > 100:

        return await interaction.response.send_message(
            "❌ Amount must be 1-100.",
            ephemeral=True
        )

    await interaction.response.defer(
        ephemeral=True
    )

    deleted = await interaction.channel.purge(
        limit=amount
    )

    await interaction.followup.send(
        f"🧹 Deleted {len(deleted)} messages.",
        ephemeral=True
    )

# ---------------- KICK ---------------- #

@bot.tree.command(
    name="kick",
    description="Kick a member"
)
@app_commands.checks.has_permissions(
    kick_members=True
)
async def kick(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason provided"
):

    await member.kick(reason=reason)

    await interaction.response.send_message(
        f"👢 Kicked {member.mention}"
    )

# ---------------- BAN ---------------- #

@bot.tree.command(
    name="ban",
    description="Ban a member"
)
@app_commands.checks.has_permissions(
    ban_members=True
)
async def ban(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason provided"
):

    await member.ban(
        reason=reason,
        delete_message_seconds=604800
    )

    await interaction.response.send_message(
        f"🔨 Banned {member.mention}"
    )

# ---------------- UNBAN ---------------- #

@bot.tree.command(
    name="unban",
    description="Unban a user"
)
@app_commands.checks.has_permissions(
    ban_members=True
)
async def unban(
    interaction: discord.Interaction,
    user_id: str
):

    try:

        user = await bot.fetch_user(
            int(user_id)
        )

        await interaction.guild.unban(user)

        await interaction.response.send_message(
            f"✅ Unbanned {user}"
        )

    except Exception:

        await interaction.response.send_message(
            "❌ Invalid user ID.",
            ephemeral=True
        )

# ---------------- SOFTBAN ---------------- #

@bot.tree.command(
    name="softban",
    description="Softban a member"
)
@app_commands.checks.has_permissions(
    ban_members=True
)
async def softban(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str = "No reason provided"
):

    await member.ban(
        reason=reason,
        delete_message_seconds=604800
    )

    await interaction.guild.unban(member)

    await interaction.response.send_message(
        f"🧽 Softbanned {member.mention}"
    )

# ---------------- WARN ---------------- #

@bot.tree.command(
    name="warn",
    description="Warn a member"
)
@app_commands.checks.has_permissions(
    moderate_members=True
)
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

    warnings[guild_id][member.id].append(
        reason
    )

    embed = discord.Embed(
        title="⚠️ Warning",
        description=(
            f"You were warned in "
            f"{interaction.guild.name}"
        ),
        color=discord.Color.orange()
    )

    embed.add_field(
        name="Reason",
        value=reason
    )

    try:
        await member.send(embed=embed)
    except Exception:
        pass

    await interaction.response.send_message(
        f"⚠️ Warned {member.mention}"
    )

# ---------------- WARNINGS ---------------- #

@bot.tree.command(
    name="warnings",
    description="View warnings"
)
async def warnings_cmd(
    interaction: discord.Interaction,
    member: discord.Member
):

    guild_id = interaction.guild.id

    user_warnings = warnings.get(
        guild_id,
        {}
    ).get(member.id, [])

    if not user_warnings:

        return await interaction.response.send_message(
            "✅ No warnings."
        )

    embed = discord.Embed(
        title=f"Warnings for {member}",
        color=discord.Color.orange()
    )

    for i, reason in enumerate(
        user_warnings,
        start=1
    ):

        embed.add_field(
            name=f"Warning {i}",
            value=reason,
            inline=False
        )

    await interaction.response.send_message(
        embed=embed
    )

# ---------------- LOCK ---------------- #

@bot.tree.command(
    name="lock",
    description="Lock channel"
)
@app_commands.checks.has_permissions(
    manage_channels=True
)
async def lock(
    interaction: discord.Interaction
):

    overwrite = (
        interaction.channel.overwrites_for(
            interaction.guild.default_role
        )
    )

    overwrite.send_messages = False

    await interaction.channel.set_permissions(
        interaction.guild.default_role,
        overwrite=overwrite
    )

    await interaction.response.send_message(
        "🔒 Channel locked."
    )

# ---------------- UNLOCK ---------------- #

@bot.tree.command(
    name="unlock",
    description="Unlock channel"
)
@app_commands.checks.has_permissions(
    manage_channels=True
)
async def unlock(
    interaction: discord.Interaction
):

    overwrite = (
        interaction.channel.overwrites_for(
            interaction.guild.default_role
        )
    )

    overwrite.send_messages = True

    await interaction.channel.set_permissions(
        interaction.guild.default_role,
        overwrite=overwrite
    )

    await interaction.response.send_message(
        "🔓 Channel unlocked."
    )

# ---------------- MUTE ---------------- #

@bot.tree.command(
    name="mute",
    description="Timeout a member"
)
@app_commands.checks.has_permissions(
    moderate_members=True
)
async def mute(
    interaction: discord.Interaction,
    member: discord.Member,
    minutes: int,
    reason: str = "No reason provided"
):

    await member.timeout(
        timedelta(minutes=minutes),
        reason=reason
    )

    await interaction.response.send_message(
        f"🔇 Muted {member.mention}"
    )

# ---------------- UNMUTE ---------------- #

@bot.tree.command(
    name="unmute",
    description="Remove timeout"
)
@app_commands.checks.has_permissions(
    moderate_members=True
)
async def unmute(
    interaction: discord.Interaction,
    member: discord.Member
):

    await member.timeout(None)

    await interaction.response.send_message(
        f"🔊 Unmuted {member.mention}"
    )

# ---------------- SLOWMODE ---------------- #

@bot.tree.command(
    name="slowmode",
    description="Set slowmode"
)
@app_commands.checks.has_permissions(
    manage_channels=True
)
async def slowmode(
    interaction: discord.Interaction,
    seconds: int
):

    await interaction.channel.edit(
        slowmode_delay=seconds
    )

    await interaction.response.send_message(
        f"🐢 Slowmode set to {seconds}s"
    )

# ---------------- NICK ---------------- #

@bot.tree.command(
    name="nick",
    description="Change nickname"
)
@app_commands.checks.has_permissions(
    manage_nicknames=True
)
async def nick(
    interaction: discord.Interaction,
    member: discord.Member,
    nickname: str
):

    await member.edit(
        nick=nickname
    )

    await interaction.response.send_message(
        (
            f"✏️ Nickname changed for "
            f"{member.mention}"
        )
    )

# ---------------- SAY ---------------- #

@bot.tree.command(
    name="say",
    description="Bot says something"
)
@app_commands.checks.has_permissions(
    manage_messages=True
)
async def say(
    interaction: discord.Interaction,
    message: str
):

    await interaction.response.send_message(
        "✅ Sent.",
        ephemeral=True
    )

    await interaction.channel.send(message)

# ---------------- AVATAR ---------------- #

@bot.tree.command(
    name="avatar",
    description="Show avatar"
)
async def avatar(
    interaction: discord.Interaction,
    user: discord.Member = None
):

    user = user or interaction.user

    embed = discord.Embed(
        title=f"{user.display_name}'s Avatar",
        color=discord.Color.blurple()
    )

    embed.set_image(
        url=user.display_avatar.url
    )

    await interaction.response.send_message(
        embed=embed
    )

# ---------------- SERVERINFO ---------------- #

@bot.tree.command(
    name="serverinfo",
    description="Server info"
)
async def serverinfo(
    interaction: discord.Interaction
):

    guild = interaction.guild

    embed = discord.Embed(
        title=guild.name,
        color=discord.Color.blurple()
    )

    embed.add_field(
        name="Members",
        value=guild.member_count
    )

    embed.add_field(
        name="Owner",
        value=guild.owner
    )

    if guild.icon:

        embed.set_thumbnail(
            url=guild.icon.url
        )

    await interaction.response.send_message(
        embed=embed
    )

# ---------------- MEMBERCOUNT ---------------- #

@bot.tree.command(
    name="membercount",
    description="Show member count"
)
async def membercount(
    interaction: discord.Interaction
):

    await interaction.response.send_message(
        (
            f"👥 Members: "
            f"{interaction.guild.member_count}"
        )
    )

# ---------------- ERROR HANDLER ---------------- #

@bot.event
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError
):

    if isinstance(
        error,
        app_commands.MissingPermissions
    ):

        await interaction.response.send_message(
            "❌ Missing permissions.",
            ephemeral=True
        )

    else:

        try:

            await interaction.response.send_message(
                f"❌ Error: {error}",
                ephemeral=True
            )

        except Exception:
            pass

# ---------------- RUN ---------------- #

bot.run(TOKEN)