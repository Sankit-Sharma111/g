import logging
import os
from collections import defaultdict, deque

from dotenv import load_dotenv
from google import genai
from google.genai import types
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID", "").strip()
SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "You are a friendly, helpful Telegram assistant. Reply naturally and concisely. "
    "Use the same language as the user. Never claim to be a human.",
)

if not TELEGRAM_BOT_TOKEN or not GEMINI_API_KEY:
    raise RuntimeError(
        "Set TELEGRAM_BOT_TOKEN and GEMINI_API_KEY in your environment or .env file."
    )

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("telegram-ai-bot")

ai_enabled = True
# Short in-memory conversation history. It resets when the bot restarts.
chat_history = defaultdict(lambda: deque(maxlen=12))
ai_client = genai.Client(api_key=GEMINI_API_KEY)


def is_admin(update: Update) -> bool:
    return bool(ADMIN_USER_ID) and str(update.effective_user.id) == ADMIN_USER_ID


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "नमस्ते! मैं AI assistant bot हूँ। आप मुझसे सीधे बात कर सकते हैं।\n\n"
        "Commands:\n/status - AI की स्थिति\n/reset - इस chat की बातचीत reset करें"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    state = "ON" if ai_enabled else "OFF"
    await update.effective_message.reply_text(f"AI auto-reply: {state}")


async def ai_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global ai_enabled
    if not is_admin(update):
        await update.effective_message.reply_text(
            "यह command केवल bot admin चला सकता है। ADMIN_USER_ID configure करें।"
        )
        return
    ai_enabled = True
    await update.effective_message.reply_text("AI auto-reply ON कर दिया गया है ✅")


async def ai_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global ai_enabled
    if not is_admin(update):
        await update.effective_message.reply_text(
            "यह command केवल bot admin चला सकता है। ADMIN_USER_ID configure करें।"
        )
        return
    ai_enabled = False
    await update.effective_message.reply_text("AI auto-reply OFF कर दिया गया है।")


async def reset_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_history.pop(update.effective_chat.id, None)
    await update.effective_message.reply_text("इस chat की AI conversation reset हो गई है।")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global ai_enabled

    # Respond only to direct/private chats, not groups or channels.
    if not update.effective_chat or update.effective_chat.type != "private":
        return
    if not update.effective_message or not update.effective_message.text:
        return
    if not ai_enabled:
        return

    user_text = update.effective_message.text.strip()
    if not user_text:
        return

    history = chat_history[update.effective_chat.id]
    contents = list(history)
    contents.append({"role": "user", "parts": [{"text": user_text}]})

    try:
        response = await context.application.bot_data["generate_reply"](contents)
        reply = (response or "").strip()
        if not reply:
            reply = "माफ़ कीजिए, अभी जवाब तैयार नहीं हो पाया। दोबारा कोशिश करें।"

        history.append({"role": "user", "parts": [{"text": user_text}]})
        history.append({"role": "model", "parts": [{"text": reply}]})

        # Telegram message limit is 4096 characters.
        for start_index in range(0, len(reply), 4000):
            await update.effective_message.reply_text(reply[start_index:start_index + 4000])
    except Exception:
        logger.exception("Failed to generate/send AI reply")
        await update.effective_message.reply_text(
            "अभी AI से जवाब नहीं मिल पाया। थोड़ी देर बाद फिर कोशिश करें।"
        )


async def generate_reply(contents: list) -> str:
    # Run the synchronous SDK call in a worker thread so Telegram stays responsive.
    import asyncio

    def call_gemini():
        result = ai_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
                max_output_tokens=700,
            ),
        )
        return result.text or ""

    return await asyncio.to_thread(call_gemini)


def main() -> None:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.bot_data["generate_reply"] = generate_reply

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("ai_on", ai_on))
    application.add_handler(CommandHandler("ai_off", ai_off))
    application.add_handler(CommandHandler("reset", reset_chat))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    logger.info("Telegram AI bot is starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
