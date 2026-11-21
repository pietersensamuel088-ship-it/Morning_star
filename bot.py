"""
TTVRecod Mentee Bot
Made by a Sa1nt | https://sa1nt.xyz

Features:
  • Weekly automated check-in DMs (Monday 8 AM GMT+2)
  • Personal check-in reminder to TTVRecod (Monday 3 AM GMT+2)
  • Question forwarding from mentees → TTVRecod via DM
  • Ticket system with auto-created private channels
  • 2-hour ticket reminder DM to TTVRecod
  • Welcome DM + auto-role on member join
  • /debug command to preview all DM embeds
  • /close, /setup-tickets, /setup-checkin, /mentees, /re-enable commands
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands
import os
import json
import datetime
import asyncio
from dotenv import load_dotenv

load_dotenv()

# ─── Configuration ────────────────────────────────────────────────────────────

TOKEN = os.getenv("BOT_TOKEN")

MENTOR_ID               = 1162838607220965377        # TTVRecod
MENTEE_ROLE_ID          = 1573752064427688086        # Role assigned to every mentee
TICKET_CATEGORY_ID      = 1573756045673766922        # Category for ticket channels
TICKET_PANEL_CHANNEL_ID = 1573755700835000402        # Channel to auto-post the ticket panel

MENTEES = {
    251781667520380928:  {"name": "Hossa",   "role_id": 1573752061550395504},
    409459604339032064:  {"name": "Toasted", "role_id": 1573752059512094820},
    1052702737143451708: {"name": "Pepper",  "role_id": 1573752049861136425},
}

DATA_FILE = os.getenv("DATA_FILE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json"))

# ─── Persistence helpers ──────────────────────────────────────────────────────

def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"opted_out": [], "tickets": {}}

def save_data(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ─── Bot setup ────────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.members          = True
intents.message_content  = True
intents.dm_messages      = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ─── Helper: get mentor User object ──────────────────────────────────────────

async def get_mentor() -> discord.User | None:
    return bot.get_user(MENTOR_ID) or await bot.fetch_user(MENTOR_ID)

# ─────────────────────────────────────────────────────────────────────────────
#  EMBED BUILDERS  (reused by features AND /debug)
# ─────────────────────────────────────────────────────────────────────────────

def build_welcome_embed(member_name: str = "NewMentee", guild_icon_url: str | None = None) -> discord.Embed:
    embed = discord.Embed(
        title="👋 Welcome!",
        description=(
            f"Welcome to **TTVRecod's Mentee Server**.\n\n"
            "**What you need to know:**\n"
            "• 💬 Ask questions in the server channels\n"
            "• 🎫 Use the ticket system for private help\n"
            "• 📩 DM **TTVRecod** directly if needed\n"
            "• 📋 Every **Monday at 8:00 AM (GMT+2)** you'll get an automated check-in DM"
        ),
        color=discord.Color.purple(),
        timestamp=discord.utils.utcnow(),
    )
    embed.set_footer(text="Made by a Sa1nt | sa1nt.xyz")
    if guild_icon_url:
        embed.set_thumbnail(url=guild_icon_url)
    return embed


def build_checkin_embed() -> discord.Embed:
    return discord.Embed(
        title="📋 Weekly Check-In",
        description=(
            "This is an **automated mentee check-in** from **TTVRecod**.\n\n"
            "How's everything going?\n\n"
            "**Need help?**\n"
            "• 💬 Head to your private channel\n"
            "• 🎫 Create a support ticket\n"
            "• 📩 DM <@1162838607220965377> directly\n\n"
            "*Want TTVRecod to check in with you personally instead?\n"
            "Click the button below to disable automated messages.*"
        ),
        color=discord.Color.gold(),
        timestamp=discord.utils.utcnow(),
    ).set_footer(text="Mutiny DarkRP • Made by a Sa1nt | sa1nt.xyz")


def build_mentor_reminder_embed(opted_out_names: list[str] | None = None) -> discord.Embed:
    embed = discord.Embed(
        title="⏰ Monday Mentee Reminder",
        description="Hey TTVRecod! It's **Monday** — time to check in with your mentees!\n",
        color=discord.Color.red(),
        timestamp=discord.utils.utcnow(),
    )
    if opted_out_names:
        embed.add_field(
            name="🔕 Personal Check-In Required",
            value="\n".join(f"• **{n}**" for n in opted_out_names)
                  + "\n\n*These mentees disabled automated check-ins — message them yourself.*",
            inline=False,
        )
    else:
        embed.add_field(
            name="✅ All Mentees on Auto Check-In",
            value="No one has opted out — automated DMs will go out at 8 AM.",
            inline=False,
        )
    embed.set_footer(text="Made by a Sa1nt | sa1nt.xyz")
    return embed


def build_optout_notification_embed(user_name: str = "SomeMentee", user_id: int = 0) -> discord.Embed:
    return discord.Embed(
        title="⚠️ Automated Check-In Disabled",
        description=(
            f"**{user_name}** (`{user_id}`) has disabled automated check-ins.\n\n"
            "You need to personally check in with them."
        ),
        color=discord.Color.orange(),
        timestamp=discord.utils.utcnow(),
    )


def build_question_embed(user_name: str = "SomeMentee", user_id: int = 0,
                          question: str = "How do I handle RDM reports?",
                          avatar_url: str | None = None) -> discord.Embed:
    embed = discord.Embed(
        title="📩 New Question from a Mentee",
        color=discord.Color.blue(),
        timestamp=discord.utils.utcnow(),
    )
    embed.add_field(name="From", value=f"**{user_name}** (`{user_name}`)", inline=True)
    embed.add_field(name="User ID", value=f"`{user_id}`", inline=True)
    embed.add_field(name="Question", value=question, inline=False)
    if avatar_url:
        embed.set_thumbnail(url=avatar_url)
    embed.set_footer(text="Reply to them via DM")
    return embed


def build_dm_forward_embed(user_name: str = "SomeMentee", user_id: int = 0,
                            message: str = "Hey, can you help me with something?",
                            avatar_url: str | None = None) -> discord.Embed:
    embed = discord.Embed(
        title="📩 DM from a Mentee",
        color=discord.Color.blue(),
        timestamp=discord.utils.utcnow(),
    )
    embed.add_field(name="From", value=f"**{user_name}** (`{user_name}`)", inline=True)
    embed.add_field(name="User ID", value=f"`{user_id}`", inline=True)
    embed.add_field(name="Message", value=message, inline=False)
    if avatar_url:
        embed.set_thumbnail(url=avatar_url)
    embed.set_footer(text="Reply to them via DM")
    return embed


def build_ticket_opened_embed(user_mention: str = "@SomeMentee") -> discord.Embed:
    embed = discord.Embed(
        title="🎫 Support Ticket Opened",
        description=(
            f"Welcome {user_mention}!\n\n"
            "**TTVRecod** has been notified and will be with you shortly.\n"
            "Please describe your issue or question below.\n\n"
            "⏰ *If this ticket isn't responded to within **2 hours**, TTVRecod will be pinged.*"
        ),
        color=discord.Color.green(),
        timestamp=discord.utils.utcnow(),
    )
    embed.set_footer(text="Made by a Sa1nt | sa1nt.xyz")
    return embed


def build_ticket_2hr_embed(user_name: str = "SomeMentee", channel_id: int = 0) -> discord.Embed:
    return discord.Embed(
        title="⏰ Ticket Open for 2+ Hours!",
        description=f"**{user_name}**'s ticket has been open for over 2 hours!\nChannel: <#{channel_id}>",
        color=discord.Color.red(),
        timestamp=discord.utils.utcnow(),
    ).set_footer(text="Mutiny DarkRP • Made by a Sa1nt | sa1nt.xyz")


def build_ticket_panel_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🎫 Support Tickets",
        description=(
            "Need help with something? Have a question about your mentorship?\n\n"
            "Click the button below to create a **private support ticket**.\n"
            "**TTVRecod** will be notified and respond ASAP.\n\n"
            "🔗 [sa1nt.xyz](https://sa1nt.xyz)"
        ),
        color=discord.Color.purple(),
        timestamp=discord.utils.utcnow(),
    )
    embed.set_footer(text="Made by a Sa1nt | sa1nt.xyz")
    return embed


# ─────────────────────────────────────────────────────────────────────────────
#  VIEWS  (persistent — survive bot restarts)
# ─────────────────────────────────────────────────────────────────────────────

class QuestionModal(discord.ui.Modal, title="Ask TTVRecod a Question"):
    question = discord.ui.TextInput(
        label="Your Question",
        style=discord.TextStyle.paragraph,
        placeholder="Type your question here and TTVRecod will get back to you…",
        required=True,
        max_length=1000,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "✅ Your question has been sent to **TTVRecod**! They'll get back to you soon.",
            ephemeral=True,
        )
        mentor = await get_mentor()
        if mentor:
            embed = build_question_embed(
                user_name=interaction.user.display_name,
                user_id=interaction.user.id,
                question=self.question.value,
                avatar_url=interaction.user.display_avatar.url,
            )
            await mentor.send(embed=embed)


class CheckInView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔕 Disable Automated Check-In", style=discord.ButtonStyle.danger, custom_id="mutiny:disable_checkin")
    async def disable_checkin(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()
        uid = str(interaction.user.id)
        if uid in data.get("opted_out", []):
            await interaction.response.send_message("You've already disabled automated check-ins.", ephemeral=True)
            return

        data.setdefault("opted_out", []).append(uid)
        save_data(data)

        await interaction.response.send_message(
            "✅ Automated check-ins disabled. **TTVRecod** will personally check in with you instead!",
            ephemeral=True,
        )

        mentor = await get_mentor()
        if mentor:
            embed = build_optout_notification_embed(interaction.user.display_name, interaction.user.id)
            await mentor.send(embed=embed)

    @discord.ui.button(label="❓ Ask a Question", style=discord.ButtonStyle.primary, custom_id="mutiny:ask_question")
    async def ask_question(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(QuestionModal())


class TicketCreateView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Create a Ticket", style=discord.ButtonStyle.green, custom_id="mutiny:create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("❌ Tickets can only be created in a server.", ephemeral=True)
            return

        category = guild.get_channel(TICKET_CATEGORY_ID)
        if not category:
            await interaction.response.send_message("❌ Ticket category not found. Ask TTVRecod to fix the config.", ephemeral=True)
            return

        data = load_data()
        uid = str(interaction.user.id)
        if uid in data.get("tickets", {}):
            existing_ch = guild.get_channel(int(data["tickets"][uid]["channel_id"]))
            if existing_ch:
                await interaction.response.send_message(
                    f"❌ You already have an open ticket: {existing_ch.mention}", ephemeral=True
                )
                return

        await interaction.response.defer(ephemeral=True)

        mentor_member = guild.get_member(MENTOR_ID)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True, attach_files=True
            ),
        }
        if mentor_member:
            overwrites[mentor_member] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, read_message_history=True, manage_channels=True
            )

        channel = await category.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            overwrites=overwrites,
            topic=f"Support ticket for {interaction.user.display_name} ({interaction.user.id})",
        )

        data.setdefault("tickets", {})[uid] = {
            "channel_id": str(channel.id),
            "opened_at": discord.utils.utcnow().isoformat(),
            "notified": False,
        }
        save_data(data)

        embed = build_ticket_opened_embed(interaction.user.mention)
        await channel.send(embed=embed, view=TicketCloseView())
        await interaction.followup.send(f"✅ Your ticket has been created: {channel.mention}", ephemeral=True)


class TicketCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.danger, custom_id="mutiny:close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = load_data()
        ch_id = str(interaction.channel.id)

        owner_uid = None
        for uid, tdata in data.get("tickets", {}).items():
            if tdata["channel_id"] == ch_id:
                owner_uid = uid
                break

        if interaction.user.id != MENTOR_ID and str(interaction.user.id) != owner_uid:
            await interaction.response.send_message("❌ Only TTVRecod or the ticket owner can close this.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🔒 Ticket Closed",
            description="This channel will be deleted in **5 seconds**.",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow(),
        )
        await interaction.response.send_message(embed=embed)

        if owner_uid and owner_uid in data.get("tickets", {}):
            del data["tickets"][owner_uid]
            save_data(data)

        await asyncio.sleep(5)
        try:
            await interaction.channel.delete(reason="Ticket closed")
        except discord.NotFound:
            pass


# ─────────────────────────────────────────────────────────────────────────────
#  EVENTS
# ─────────────────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    print(f"✅  {bot.user}  is online!")

    # DND status — activity shows "Made by a Sa1nt"
    activity = discord.CustomActivity(name="Made by a Sa1nt")
    await bot.change_presence(status=discord.Status.dnd, activity=activity)

    # Register persistent views
    bot.add_view(CheckInView())
    bot.add_view(TicketCreateView())
    bot.add_view(TicketCloseView())

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        print(f"✅  Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"❌  Slash-command sync failed: {e}")

    # Auto-post ticket panel if not already present
    await auto_post_ticket_panel()

    # Start background loops
    if not weekly_checkin_loop.is_running():
        weekly_checkin_loop.start()
    if not mentor_reminder_loop.is_running():
        mentor_reminder_loop.start()
    if not ticket_watchdog_loop.is_running():
        ticket_watchdog_loop.start()


async def auto_post_ticket_panel():
    """Post the ticket panel embed in the designated channel if not already there."""
    channel = bot.get_channel(TICKET_PANEL_CHANNEL_ID)
    if not channel:
        print(f"⚠️  Ticket panel channel {TICKET_PANEL_CHANNEL_ID} not found — skipping auto-post")
        return

    # Check last 20 messages to see if the bot already posted the ticket panel
    try:
        async for msg in channel.history(limit=20):
            if msg.author == bot.user and msg.embeds:
                for emb in msg.embeds:
                    if emb.title and "Support Tickets" in emb.title:
                        print("ℹ️  Ticket panel already exists — skipping auto-post")
                        return
    except discord.Forbidden:
        print("⚠️  No permission to read ticket panel channel history")
        return

    embed = build_ticket_panel_embed()
    await channel.send(embed=embed, view=TicketCreateView())
    print(f"✅  Ticket panel auto-posted in #{channel.name}")


@bot.event
async def on_member_join(member: discord.Member):
    guild = member.guild

    # Assign the generic mentee role
    mentee_role = guild.get_role(MENTEE_ROLE_ID)
    if mentee_role:
        try:
            await member.add_roles(mentee_role, reason="New mentee joined")
        except discord.Forbidden:
            print(f"⚠️  Missing permissions to assign mentee role to {member}")

    # Assign individual role if applicable
    if member.id in MENTEES:
        individual_role = guild.get_role(MENTEES[member.id]["role_id"])
        if individual_role:
            try:
                await member.add_roles(individual_role, reason="Known mentee — individual role")
            except discord.Forbidden:
                pass

    # Welcome DM
    try:
        icon_url = guild.icon.url if guild.icon else None
        embed = build_welcome_embed(member.display_name, icon_url)
        await member.send(embed=embed)
    except discord.Forbidden:
        print(f"⚠️  Can't DM {member} (DMs closed)")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if message.guild is not None:
        await bot.process_commands(message)
        return

    # DM from someone — forward to mentor
    if message.author.id == MENTOR_ID:
        return

    mentor = await get_mentor()
    if mentor:
        embed = build_dm_forward_embed(
            user_name=message.author.display_name,
            user_id=message.author.id,
            message=message.content[:1024] or "*[no text]*",
            avatar_url=message.author.display_avatar.url,
        )
        await mentor.send(embed=embed)
        await message.reply("✅ Your message has been forwarded to **TTVRecod**! They'll get back to you soon.")

    await bot.process_commands(message)


# ─────────────────────────────────────────────────────────────────────────────
#  SCHEDULED LOOPS
# ─────────────────────────────────────────────────────────────────────────────

# GMT+2  8:00 AM  =  UTC 6:00 AM
@tasks.loop(time=datetime.time(hour=6, minute=0, tzinfo=datetime.timezone.utc))
async def weekly_checkin_loop():
    if datetime.datetime.now(datetime.timezone.utc).weekday() != 0:
        return

    data = load_data()
    opted_out = data.get("opted_out", [])

    for guild in bot.guilds:
        mentee_role = guild.get_role(MENTEE_ROLE_ID)
        if not mentee_role:
            continue
        for member in mentee_role.members:
            if str(member.id) in opted_out:
                continue
            try:
                embed = build_checkin_embed()
                await member.send(embed=embed, view=CheckInView())
            except discord.Forbidden:
                print(f"⚠️  Can't DM {member} for weekly check-in")


# GMT+2  3:00 AM  =  UTC 1:00 AM
@tasks.loop(time=datetime.time(hour=1, minute=0, tzinfo=datetime.timezone.utc))
async def mentor_reminder_loop():
    if datetime.datetime.now(datetime.timezone.utc).weekday() != 0:
        return

    mentor = await get_mentor()
    if not mentor:
        return

    data = load_data()
    opted_out = data.get("opted_out", [])

    names = []
    for uid_str in opted_out:
        try:
            user = bot.get_user(int(uid_str)) or await bot.fetch_user(int(uid_str))
            names.append(user.display_name)
        except Exception:
            names.append(f"Unknown ({uid_str})")

    embed = build_mentor_reminder_embed(names if names else None)
    await mentor.send(embed=embed)


@tasks.loop(minutes=30)
async def ticket_watchdog_loop():
    data = load_data()
    now = datetime.datetime.now(datetime.timezone.utc)
    changed = False

    for uid, tdata in data.get("tickets", {}).items():
        if tdata.get("notified"):
            continue
        opened = datetime.datetime.fromisoformat(tdata["opened_at"])
        if (now - opened).total_seconds() >= 7200:
            mentor = await get_mentor()
            if mentor:
                try:
                    user = bot.get_user(int(uid)) or await bot.fetch_user(int(uid))
                    name = user.display_name
                except Exception:
                    name = f"Unknown ({uid})"
                embed = build_ticket_2hr_embed(name, int(tdata["channel_id"]))
                await mentor.send(embed=embed)
            tdata["notified"] = True
            changed = True

    if changed:
        save_data(data)


# ─────────────────────────────────────────────────────────────────────────────
#  SLASH COMMANDS
# ─────────────────────────────────────────────────────────────────────────────

# ── /debug ────────────────────────────────────────────────────────────────────

class DebugChoice(discord.Enum):
    Welcome_DM = "welcome"
    Weekly_Check_In = "checkin"
    Mentor_Monday_Reminder = "mentor_reminder"
    Opt_Out_Notification = "optout"
    Question_Forwarded = "question"
    DM_Forwarded = "dm_forward"
    Ticket_Opened = "ticket_opened"
    Ticket_2hr_Reminder = "ticket_2hr"
    Ticket_Panel = "ticket_panel"
    All_Previews = "all"


@bot.tree.command(name="debug", description="Preview all bot DM embeds (TTVRecod only)")
@app_commands.describe(preview="Which embed to preview")
async def debug_cmd(interaction: discord.Interaction, preview: DebugChoice):
    if interaction.user.id != MENTOR_ID:
        await interaction.response.send_message("❌ Only TTVRecod can use this.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    embeds_to_send: list[tuple[discord.Embed, discord.ui.View | None]] = []
    choice = preview.value

    icon_url = interaction.guild.icon.url if interaction.guild and interaction.guild.icon else None
    avatar = interaction.user.display_avatar.url

    if choice in ("welcome", "all"):
        embeds_to_send.append((build_welcome_embed("DebugMentee", icon_url), None))

    if choice in ("checkin", "all"):
        embeds_to_send.append((build_checkin_embed(), CheckInView()))

    if choice in ("mentor_reminder", "all"):
        embeds_to_send.append((build_mentor_reminder_embed(["Hossa", "Toasted"]), None))

    if choice in ("optout", "all"):
        embeds_to_send.append((build_optout_notification_embed("DebugMentee", 123456789), None))

    if choice in ("question", "all"):
        embeds_to_send.append((build_question_embed("DebugMentee", 123456789,
                                                      "How do I handle RDM reports?", avatar), None))

    if choice in ("dm_forward", "all"):
        embeds_to_send.append((build_dm_forward_embed("DebugMentee", 123456789,
                                                        "Hey, can you help me with something?", avatar), None))

    if choice in ("ticket_opened", "all"):
        embeds_to_send.append((build_ticket_opened_embed(interaction.user.mention), TicketCloseView()))

    if choice in ("ticket_2hr", "all"):
        embeds_to_send.append((build_ticket_2hr_embed("DebugMentee", 000000000), None))

    if choice in ("ticket_panel", "all"):
        embeds_to_send.append((build_ticket_panel_embed(), TicketCreateView()))

    # Send all previews as DMs
    mentor = interaction.user
    count = 0
    for embed, view in embeds_to_send:
        kwargs = {"embed": embed}
        if view:
            kwargs["view"] = view
        try:
            await mentor.send(**kwargs)
            count += 1
        except discord.Forbidden:
            pass

    await interaction.followup.send(f"✅ Sent **{count}** preview embed(s) to your DMs!", ephemeral=True)


# ── /close ────────────────────────────────────────────────────────────────────

@bot.tree.command(name="close", description="Close the current ticket channel")
async def close_cmd(interaction: discord.Interaction):
    data = load_data()
    ch_id = str(interaction.channel.id)

    owner_uid = None
    for uid, tdata in data.get("tickets", {}).items():
        if tdata["channel_id"] == ch_id:
            owner_uid = uid
            break

    if owner_uid is None:
        await interaction.response.send_message("❌ This isn't a ticket channel.", ephemeral=True)
        return
    if interaction.user.id != MENTOR_ID and str(interaction.user.id) != owner_uid:
        await interaction.response.send_message("❌ Only TTVRecod or the ticket owner can close this.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🔒 Ticket Closed",
        description="This channel will be deleted in **5 seconds**.",
        color=discord.Color.red(),
        timestamp=discord.utils.utcnow(),
    )
    await interaction.response.send_message(embed=embed)

    if owner_uid in data.get("tickets", {}):
        del data["tickets"][owner_uid]
        save_data(data)

    await asyncio.sleep(5)
    try:
        await interaction.channel.delete(reason="Ticket closed via /close")
    except discord.NotFound:
        pass


# ── /setup-tickets ────────────────────────────────────────────────────────────

@bot.tree.command(name="setup-tickets", description="Post the ticket panel embed (TTVRecod only)")
async def setup_tickets_cmd(interaction: discord.Interaction):
    if interaction.user.id != MENTOR_ID:
        await interaction.response.send_message("❌ Only TTVRecod can use this.", ephemeral=True)
        return

    embed = build_ticket_panel_embed()
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.send(embed=embed, view=TicketCreateView())
    await interaction.followup.send("✅ Ticket panel created!", ephemeral=True)


# ── /setup-checkin ────────────────────────────────────────────────────────────

@bot.tree.command(name="setup-checkin", description="Post the check-in info embed (TTVRecod only)")
async def setup_checkin_cmd(interaction: discord.Interaction):
    if interaction.user.id != MENTOR_ID:
        await interaction.response.send_message("❌ Only TTVRecod can use this.", ephemeral=True)
        return

    embed = discord.Embed(
        title="📋 Mentee Check-In System",
        description=(
            "Every **Monday at 8:00 AM (GMT+2)**, all mentees will receive an automated check-in DM.\n\n"
            "**Features:**\n"
            "• 📩 Automated weekly check-in DMs\n"
            "• ❓ Ask questions directly through the bot\n"
            "• 🔕 Option to request personal check-ins from TTVRecod\n"
            "• 🎫 Ticket system for private support\n\n"
            "🔗 [sa1nt.xyz](https://sa1nt.xyz)"
        ),
        color=discord.Color.gold(),
        timestamp=discord.utils.utcnow(),
    )
    embed.set_footer(text="Made by a Sa1nt | sa1nt.xyz")

    await interaction.response.defer(ephemeral=True)
    await interaction.channel.send(embed=embed)
    await interaction.followup.send("✅ Check-in panel sent!", ephemeral=True)


# ── /mentees ──────────────────────────────────────────────────────────────────

@bot.tree.command(name="mentees", description="Show all mentees and their check-in status (TTVRecod only)")
async def mentees_cmd(interaction: discord.Interaction):
    if interaction.user.id != MENTOR_ID:
        await interaction.response.send_message("❌ Only TTVRecod can use this.", ephemeral=True)
        return

    data = load_data()
    opted_out = data.get("opted_out", [])

    embed = discord.Embed(title="👥 Mentee Roster", color=discord.Color.blue(), timestamp=discord.utils.utcnow())
    for uid, info in MENTEES.items():
        checkin_status = "🔕 Personal" if str(uid) in opted_out else "✅ Automated"
        member = interaction.guild.get_member(uid) if interaction.guild else None
        online = "🟢 Online" if member and member.status != discord.Status.offline else "⚫ Offline"
        embed.add_field(
            name=info["name"],
            value=f"ID: `{uid}`\nRole: <@&{info['role_id']}>\nCheck-In: {checkin_status}\n{online}",
            inline=True,
        )
    embed.set_footer(text="Made by a Sa1nt | sa1nt.xyz")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ── /re-enable ────────────────────────────────────────────────────────────────

@bot.tree.command(name="re-enable", description="Re-enable automated check-ins for a mentee (TTVRecod only)")
@app_commands.describe(user="The mentee to re-enable check-ins for")
async def reenable_cmd(interaction: discord.Interaction, user: discord.User):
    if interaction.user.id != MENTOR_ID:
        await interaction.response.send_message("❌ Only TTVRecod can use this.", ephemeral=True)
        return

    data = load_data()
    uid = str(user.id)
    if uid not in data.get("opted_out", []):
        await interaction.response.send_message(
            f"ℹ️ **{user.display_name}** already has automated check-ins enabled.", ephemeral=True
        )
        return

    data["opted_out"].remove(uid)
    save_data(data)
    await interaction.response.send_message(
        f"✅ Automated check-ins **re-enabled** for **{user.display_name}**.", ephemeral=True
    )


# ─────────────────────────────────────────────────────────────────────────────
#  RUN
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    bot.run(TOKEN)
