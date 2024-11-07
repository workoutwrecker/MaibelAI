import logging
from telegram import Update
from telegram.ext import ContextTypes
from utils import escaped_string
from profile_manager import update_user_profile

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Start command handler
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    msg = "! I'm a bot powered by AI. Ask me anything related to women's fitness or just chat!"
    final_msg = f"Hi {user.mention_markdown_v2()}{escaped_string(msg)}"
    await update.message.reply_text(final_msg, parse_mode="MarkdownV2")
    await update_user_profile(update, context)


# Call command handler
async def call_bot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    link = "https://th.bing.com/th/id/OIP._M8xq8ZqE859erXkR0SD8QHaEo?w=289&h=180&c=7&r=0&o=5&dpr=1.3&pid=1.7"
    msg = f"Here's the link to get on a call with me right now!\n{link}"
    await update.message.reply_text(escaped_string(msg), parse_mode="MarkdownV2")

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if update.message:
        await update.message.reply_text(f"An error occured, but don't worry. I'll be back...")
