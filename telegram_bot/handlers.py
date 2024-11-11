import logging
from telegram import Update
from telegram.ext import ContextTypes
from profile_mgmt import setup

from utils import escaped_string

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Start command handler
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    msg = ("! I'm a bot powered by AI. Ask me anything related to women's fitness or just chat!\n\n"
    "/setup - Profile Setup ℹ️\n"
    "/call - Call 📞\n"
    "/app - Download our app!\n\n"
    "Let's get started with your profile setup!")
    final_msg = f"Hi {user.mention_markdown_v2()}{escaped_string(msg)}"
    await update.message.reply_text(final_msg, parse_mode="MarkdownV2")
    await setup_handler(update, context)
    

# Call command handler
async def call_bot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    link = "https://thumbs.dreamstime.com/z/indian-call-center-agent-shows-ok-gesture-showing-against-working-operators-bright-office-173649185.jpg"
    msg = f"Here's the link to get on a call with me right now!\n{link}"
    await update.message.reply_text(escaped_string(msg), parse_mode="MarkdownV2")

async def setup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if "setup" not in context.user_data or context.user_data["setup"] == "finish": 
        context.user_data["setup"] = "init"; await setup(update)
    else:
        # Previous user setup session incomplete
        await update.message.reply_text(escaped_string("Finish your previous setup session first!"), parse_mode="MarkdownV2")
    

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if update.message:
        await update.message.reply_text(f"An error occured, but don't worry. I'll be back... Error ha-0")
