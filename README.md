# USDT Airdrop Telegram Bot — Setup Guide

## 1. Install dependencies
```bash
pip install python-telegram-bot==20.7
```

## 2. Create your bot
1. Open Telegram and message **@BotFather**
2. Send `/newbot` and follow the prompts
3. Copy the **token** you receive

## 3. Configure `airdrop_bot.py`
Open the file and edit the top section:

```python
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"        # ← Paste your token here

REQUIRED_CHANNELS = {
    "Official Channel":      "@your_channel_1",   # ← Your channel usernames
    "Announcement Channel":  "@your_channel_2",
}

BOT_USERNAME = "YourBotUsername"          # ← Your bot's username (no @)
```

> **Important:** Add your bot as an **Administrator** to every channel listed
> in `REQUIRED_CHANNELS`, otherwise membership checks will fail.

## 4. Run the bot
```bash
python airdrop_bot.py
```

---

## Features

| Feature | Details |
|---|---|
| Force-join gate | Users must join all listed channels before using the bot |
| Joining bonus | 10 USDT credited on first `/start` |
| Referral system | 10 USDT per referral, instant credit |
| Balance check | Shows current USDT balance |
| Referral link | Unique link per user |
| Withdrawal | Min 25 USDT; requests stored in SQLite DB |
| Persistent storage | SQLite (`airdrop_bot.db`) — no extra setup needed |

---

## Customisation

| Setting | Variable | Default |
|---|---|---|
| Joining bonus | `JOINING_BONUS` | 10 USDT |
| Per-referral bonus | `REFERRAL_BONUS` | 10 USDT |
| Min withdrawal | `MIN_WITHDRAWAL` | 25 USDT |

---

## Notes
- The bot stores all data in `airdrop_bot.db` (created automatically).
- Withdrawals are saved with `status = 'pending'` — you process them manually or connect to a payment API.
- To run 24/7, deploy on a VPS (e.g. DigitalOcean, Hetzner) or use a service like Railway.app.
