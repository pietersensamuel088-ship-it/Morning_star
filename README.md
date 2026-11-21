# 🎮 Mutiny DarkRP — TTVRecod Mentee Bot

A Discord bot for managing mentees on the **Mutiny DarkRP** Garry's Mod server.  
Built for **TTVRecod** — Made by a Sa1nt | [sa1nt.xyz](https://sa1nt.xyz)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **Weekly Check-In** | Automated DMs every Monday at 8:00 AM (GMT+2) to all mentees |
| **Mentor Reminder** | DMs TTVRecod at 3:00 AM Monday to personally check in |
| **Opt-Out System** | Mentees can disable automated check-ins; TTVRecod gets notified |
| **Question Forwarding** | Mentees ask questions via button/modal → forwarded to TTVRecod's DMs |
| **DM Forwarding** | Any DM to the bot gets forwarded to TTVRecod |
| **Ticket System** | Private support channels with auto-create, 2-hour reminder, and `/close` |
| **Welcome DM** | Auto-roles + welcome embed on member join |
| **Debug Mode** | `/debug` previews all bot embeds in your DMs |

---

## 🚀 Quick Start (Local)

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/Morning_star.git
cd Morning_star

# 2. Create your .env
cp .env.example .env
# Edit .env and paste your bot token

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
python bot.py
```

---

## 🐳 Docker

```bash
# Build and run
docker compose up -d --build

# View logs
docker compose logs -f bot

# Stop
docker compose down
```

The bot's persistent data (`data.json`) is stored in a Docker volume so it survives restarts.

---

## ⚙️ Slash Commands

| Command | Access | Description |
|---------|--------|-------------|
| `/debug` | TTVRecod | Preview all bot DM embeds (welcome, check-in, tickets, etc.) |
| `/setup-tickets` | TTVRecod | Post the ticket panel embed in the current channel |
| `/setup-checkin` | TTVRecod | Post the check-in info embed |
| `/mentees` | TTVRecod | View mentee roster with online/check-in status |
| `/re-enable @user` | TTVRecod | Re-enable automated check-ins for a mentee |
| `/close` | TTVRecod / ticket owner | Close and delete the current ticket channel |

---

## 🔐 Required Bot Permissions

- Manage Channels
- Manage Roles
- Send Messages
- Embed Links
- Read Message History
- Use Application Commands

### Privileged Intents (Developer Portal)
- ✅ Server Members Intent
- ✅ Message Content Intent

---

## 📁 Project Structure

```
Morning_star/
├── bot.py              # Main bot code
├── .env                # Bot token (secret — never commit)
├── .env.example        # Template for .env
├── .gitignore          # Keeps secrets out of Git
├── requirements.txt    # Python dependencies
├── Dockerfile          # Container image definition
├── docker-compose.yml  # Docker Compose config
└── README.md           # This file
```

---

## 📄 License

MIT — do whatever you want with it.

---

*Made by a Sa1nt — [sa1nt.xyz](https://sa1nt.xyz)*
