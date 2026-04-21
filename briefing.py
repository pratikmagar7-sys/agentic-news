"""
Inflection Network — Daily Agentic Payments News Briefing
Runs as a cron job; fetches news via Claude + web_search, sends to Telegram.
"""

import os
import asyncio
import logging
from datetime import datetime, timezone
import anthropic
import telegram

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY  = os.environ["ANTHROPIC_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID   = os.environ["TELEGRAM_CHAT_ID"]   # your personal chat ID

MODEL = "claude-sonnet-4-6"

SEARCH_TOPICS = [
    "agentic payments 2025",
    "AI agent wallets cryptocurrency",
    "x402 protocol HTTP payments AI agents",
    "agent-to-agent transactions blockchain",
    "Base Coinbase agent economy",
    "Solana AI agents finance",
    "autonomous agent finance infrastructure",
    "financial identity AI agents startups",
    "agentic web2 payments",
    "Mastercard Visa AI agent payments 2025",
    "delegated spend controls AI",
    "MCP payments protocol agents",
]

SYSTEM_PROMPT = """You are an expert intelligence analyst covering the emerging agentic payments 
and AI agent economy sector. Your reader is Pratik — founder of Inflection Network, 
which is building financial identity, delegated spend controls, and programmable settlement 
rails for AI agents. He needs high-signal, zero-fluff briefings.

Your output format must be exactly:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 INFLECTION DAILY BRIEFING
{date} · Agentic Payments Intel
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🔥 TOP STORIES (last 24h)

[For each story — max 6 stories — use this block:]
**[HEADLINE]**
↳ [2-3 sentence summary. Be direct. Include source name.]
🎯 Inflection angle: [1 sentence on how this affects/validates/threatens Inflection]

---

## ⚡ SIGNALS & MOVES
[3-5 bullet points of smaller but notable signals: funding rounds, partnerships, protocol updates, regulatory moves]

---

## 🏁 COMPETITOR RADAR
[Quick table or list: any competing startups / incumbents making moves in financial identity or delegated spend for AI agents]

---

## 🔧 INFLECTION IMPROVEMENT NOTE
[A concrete, specific, actionable suggestion for what Inflection should build, fix, or pursue this week, based on today's news landscape. Be direct and founder-minded.]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Powered by Inflection Network Intel
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Rules:
- Only include news from the last 24 hours where possible; flag older items with [older]
- No hallucination — if you can't find real news on a topic, skip it
- Keep the entire briefing under 3000 characters (Telegram limit awareness)
- Use plain text + minimal markdown that renders in Telegram"""


def build_user_prompt() -> str:
    today = datetime.now(timezone.utc).strftime("%A, %d %B %Y")
    topics_str = "\n".join(f"- {t}" for t in SEARCH_TOPICS)
    return f"""Today is {today} UTC.

Search the web for the latest news (last 24 hours) across these topics:
{topics_str}

Then produce the full Inflection Daily Briefing using the format specified.
Use the web_search tool multiple times as needed to cover all topic areas."""


def fetch_briefing() -> str:
    """Call Claude with web_search tool; return the final text briefing."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    log.info("Calling Claude %s with web_search …", MODEL)

    messages = [{"role": "user", "content": build_user_prompt()}]

    # Agentic loop — Claude may call web_search multiple times
    while True:
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=[{"type": "web_search_20250305", "name": "web_search"}],
            messages=messages,
        )

        log.info("stop_reason=%s  usage=%s", response.stop_reason, response.usage)

        # Collect text blocks from this turn
        text_blocks = [b.text for b in response.content if b.type == "text"]

        if response.stop_reason == "end_turn":
            if not text_blocks:
                raise RuntimeError("Claude returned no text content")
            return "\n".join(text_blocks).strip()

        if response.stop_reason == "tool_use":
            # Append assistant message, then resolve all tool calls
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_result":
                    # web_search tool results come back as tool_result blocks
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.tool_use_id,
                        "content": block.content,
                    })
                elif block.type == "tool_use" and block.name == "web_search":
                    # The SDK handles the actual search; results are in subsequent tool_result blocks.
                    # If the SDK streams tool_use + tool_result in the same response.content list,
                    # we only need to forward tool_result blocks.
                    pass

            # If there are no tool_result blocks yet, it means the SDK already resolved them
            # inside response.content as server_tool_use / tool_result pairs.
            # Just feed the whole response.content back as the assistant turn and continue.
            if not tool_results:
                # Nothing to add — loop will get next response
                # This shouldn't happen with server-side web_search, but guard anyway
                break

            messages.append({"role": "user", "content": tool_results})
            continue

        # Any other stop reason — return whatever text we have
        if text_blocks:
            return "\n".join(text_blocks).strip()

        raise RuntimeError(f"Unexpected stop_reason: {response.stop_reason}")


def chunk_message(text: str, limit: int = 4000) -> list[str]:
    """Split long messages into Telegram-safe chunks."""
    if len(text) <= limit:
        return [text]
    chunks = []
    while text:
        chunks.append(text[:limit])
        text = text[limit:]
    return chunks


async def send_telegram(text: str) -> None:
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    for chunk in chunk_message(text):
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=chunk,
            parse_mode="Markdown",
        )
        await asyncio.sleep(0.5)
    log.info("Telegram message sent ✓")


def main() -> None:
    log.info("=== Inflection Daily Briefing — starting ===")

    briefing = fetch_briefing()
    log.info("Briefing generated (%d chars)", len(briefing))

    asyncio.run(send_telegram(briefing))

    log.info("=== Done ===")


if __name__ == "__main__":
    main()
