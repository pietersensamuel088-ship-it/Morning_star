# TTVRecod Mentee Bot

Discord bot for managing mentees. Handles weekly check-ins, ticket system, question forwarding, and auto-roles.

Made by a Sa1nt — [sa1nt.xyz](https://sa1nt.xyz)

---

## Features

- **Weekly Check-In** — Automated DMs every Monday 8:00 AM (GMT+2)
- **Mentor Reminder** — DMs TTVRecod at 3:00 AM Monday
- **Opt-Out** — Mentees can disable automated check-ins; TTVRecod gets notified
- **Question Forwarding** — Mentees ask via button/modal → forwarded to TTVRecod DMs
- **DM Forwarding** — Any DM to the bot gets forwarded to TTVRecod
- **Ticket System** — Private channels, 2-hour reminder, `/close`
- **Welcome DM** — Auto-role + welcome message on join
- **Debug** — `/debug` previews all embeds in your DMs

---

## Setup (Local)

```bash
git clone https://github.com/pietersensamuel088-ship-it/Morning_star.git
cd Morning_star
cp .env.example .env
# Paste your bot token in .env
pip install -r requirements.txt
python bot.py
```

## Setup (Docker)

```bash
git clone https://github.com/pietersensamuel088-ship-it/Morning_star.git
cd Morning_star
cp .env.example .env
# Paste your bot token in .env
docker compose up -d --build
```

---

## Commands

| Command | Access | Description |
|---------|--------|-------------|
| `/debug` | TTVRecod | Preview all bot embeds in your DMs |
| `/setup-tickets` | TTVRecod | Post ticket panel in current channel |
| `/setup-checkin` | TTVRecod | Post check-in info embed |
| `/mentees` | TTVRecod | View mentee roster |
| `/re-enable @user` | TTVRecod | Re-enable auto check-ins for a mentee |
| `/close` | TTVRecod / ticket owner | Close current ticket channel |

---

## Bot Permissions

- Manage Channels, Manage Roles, Send Messages, Embed Links, Read Message History, Use Application Commands

**Privileged Intents:** Server Members, Message Content

---

## Files

```
Morning_star/
├── bot.py
├── .env              # Token (never commit)
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

*Made by a Sa1nt — [sa1nt.xyz](https://sa1nt.xyz)*
