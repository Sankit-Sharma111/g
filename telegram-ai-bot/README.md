# Telegram AI Auto-Reply Bot

A Telegram bot that automatically replies to text messages in private chats using the Google Gemini API.

## Features

- Automatic AI replies in private chats
- Hindi and English (the model follows the sender's language)
- Short conversation context per user
- `/ai_on` and `/ai_off` admin controls
- `/status` and `/reset` commands
- Secrets are read from environment variables, never hard-coded

## 1. Create the Telegram bot

1. Open [@BotFather](https://t.me/BotFather) in Telegram.
2. Use `/newbot` and follow the prompts.
3. Copy the bot token. Keep it private.

## 2. Get a Gemini API key

Create an API key in [Google AI Studio](https://aistudio.google.com/). Check the current model availability, free-tier quota and regional terms in Google AI Studio.

## 3. Configure environment variables

Copy `.env.example` to `.env` on your own computer and fill in:

- `TELEGRAM_BOT_TOKEN`
- `GEMINI_API_KEY`
- `ADMIN_USER_ID` — your numeric Telegram user ID

Do not commit the real `.env` file or paste keys into chat, source code, screenshots, or public GitHub.

## 4. Run locally

Python 3.10 or newer is recommended.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python bot.py
```

## Commands

- `/start` — welcome message
- `/status` — show whether auto-replies are on
- `/ai_on` — enable auto-replies (admin only)
- `/ai_off` — disable auto-replies (admin only)
- `/reset` — clear the current chat's short-term conversation context

Send a normal text message to the bot to receive an AI reply.

## Hosting

Deploy this folder as a Python worker/service on a host that supports always-on background processes. Add the three required environment variables in the host's secret/environment-variable settings, then run `python bot.py`. A free hosting plan may sleep or have usage limits, so 24/7 uptime is not guaranteed.

## Notes

- This version replies only in private chats; it ignores groups and channels.
- The AI ON/OFF switch is global for this bot process.
- Conversation history is stored in memory and is cleared when the process restarts.
- Gemini free-tier availability and quotas can change. API usage may become paid if you exceed the free allowance or enable a paid plan.
