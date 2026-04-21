# Inflection Daily Briefing — Setup Guide

Daily agentic payments intelligence delivered to your Telegram, powered by Claude + web search.

---

## What it does

Every morning the script:
1. Calls `claude-sonnet-4-6` with `web_search_20250305` enabled
2. Searches 12 topic areas across agentic payments, AI wallets, competing startups, x402, Base, Solana, Mastercard/Visa, etc.
3. Produces a structured briefing with top stories, competitor radar, and a concrete Inflection improvement note
4. Sends it to your Telegram via bot

---

## Prerequisites

| Tool | Purpose |
|------|---------|
| Python 3.11+ | Runtime |
| Anthropic API key | Claude + web search |
| Telegram Bot token | Delivery |
| Your Telegram chat ID | Target |

---

## Step 1 — Install dependencies

```bash
pip install anthropic python-telegram-bot
```

Or pin versions for production:

```bash
pip install anthropic==0.49.0 python-telegram-bot==21.10
```

---

## Step 2 — Create your Telegram bot

1. Open Telegram → search **@BotFather** → `/newbot`
2. Follow prompts → copy the **bot token** (looks like `7123456789:AAF...`)
3. Start a chat with your new bot (send it `/start`)
4. Get your **chat ID**:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
   Look for `"chat":{"id": <NUMBER>}` in the JSON — that number is your chat ID.

---

## Step 3 — Set environment variables

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export TELEGRAM_BOT_TOKEN="7123456789:AAF..."
export TELEGRAM_CHAT_ID="123456789"
```

Test locally:
```bash
python briefing.py
```

---

## Deployment Options

### Option A — GitHub Actions (recommended for zero-infra)

Create `.github/workflows/briefing.yml`:

```yaml
name: Daily Agentic Payments Briefing

on:
  schedule:
    - cron: '30 4 * * *'   # 10:00 AM IST (04:30 UTC)
  workflow_dispatch:         # manual trigger for testing

jobs:
  send-briefing:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install deps
        run: pip install anthropic python-telegram-bot

      - name: Run briefing
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python briefing.py
```

Add secrets in: **GitHub repo → Settings → Secrets → Actions**
- `ANTHROPIC_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Push `briefing.py` and the workflow file → done. Runs daily at 10 AM IST.

---

### Option B — Railway

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Add environment variables in Railway dashboard:
   - `ANTHROPIC_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
4. Add a **Cron Service** in Railway:
   - Command: `python briefing.py`
   - Schedule: `30 4 * * *` (10 AM IST)

Railway gives you logs, retries, and a free tier that covers this easily.

---

### Option C — Local cron (Linux/Mac)

```bash
crontab -e
```

Add:
```
30 4 * * * ANTHROPIC_API_KEY=sk-ant-... TELEGRAM_BOT_TOKEN=7123... TELEGRAM_CHAT_ID=123... /usr/bin/python3 /path/to/briefing.py >> /var/log/briefing.log 2>&1
```

---

## Customization

### Change delivery time

Edit the cron expression. For IST (UTC+5:30):

| Desired IST time | Cron (UTC) |
|-----------------|------------|
| 7:00 AM | `30 1 * * *` |
| 8:00 AM | `30 2 * * *` |
| 9:00 AM | `30 3 * * *` |
| **10:00 AM** | **`30 4 * * *`** ← default |

### Add/remove search topics

Edit `SEARCH_TOPICS` list in `briefing.py`:

```python
SEARCH_TOPICS = [
    "agentic payments 2025",
    "your new topic here",
    ...
]
```

### Adjust the briefing format

Edit `SYSTEM_PROMPT` in `briefing.py`. The Inflection improvement note section is
intentionally opinionated — update it if your focus areas shift.

---

## Cost estimate

Each run makes ~8-15 web search calls through Claude.
Approximate cost per run: **$0.05–0.15** depending on search depth.
Monthly: ~**$2–5**.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `KeyError: ANTHROPIC_API_KEY` | Environment variables not set |
| Telegram `Unauthorized` | Bot token is wrong |
| Telegram `Chat not found` | Send `/start` to your bot first, then re-fetch chat ID |
| Empty briefing | Claude found no news — rare, usually a transient API issue |
| Message too long | The chunker handles up to 4000 chars per Telegram message automatically |
