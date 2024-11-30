import logging
from datetime import timedelta
from telegram import Update
from telegram.ext import ContextTypes

from profile_mgmt import setup
from utils import escaped_string, get_current_time_in_singapore, get_limitation_category_by_id, get_limitation_label_by_id, format_dict
from database import db_get_user_profile, db_set_user_profile
from jobs import sync_data_job

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

leaderboard = []

# Start command handler
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data["setup"] = "standby"
    user = update.effective_user
    user_profile = db_get_user_profile(str(user.id))
    user_info = context.user_data.setdefault("user_info", {})

    if user_profile: #Existing User
        final_msg = f"Welcome back, {user.mention_markdown_v2()}"
        
        user_limitations = context.user_data.setdefault("user_limitations", {})

        #TODO: Ask user if they want to load from database at {time}
        for key in ["challengeDay", "challengeTime", "Age", "Gender", "Workouts", "Goal", "Streak", "Last Check-in", "Max Streak"]:
            if user_profile.get(key, ''):
                user_info[key] = user_profile[key]

        user_info["Username"] = user.username

        if not user_limitations:
            for limitation_id in user_profile.get("Limitations", []):
                category = get_limitation_category_by_id(limitation_id)
                if category not in user_limitations:
                    user_limitations[category] = []
                user_limitations[category].append(get_limitation_label_by_id(limitation_id))

    else:
        msg = f"Hi {user.mention_markdown_v2()}"
        msg_2 = escaped_string(
            "! I'm a bot powered by AI. Ask me anything related to women's fitness or just chat!\n\n"
            "/setup - Profile Setup ℹ️\n"
            "/call - Call 📞\n"
            "/app - Download our app!\n\n"
            "Let's get started with your profile setup!"
        )
        final_msg = f"{msg}{msg_2}"
        user_info["Username"] = user.username
        user_info["Streak"] = 0

    await sync_data_job(context, user.id)
    await update.message.reply_text(final_msg, parse_mode="MarkdownV2")

    # Trigger profile setup for new users
    if not user_profile:
        await setup_handler(update, context)

# Call command handler
async def call_bot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    link = "https://thumbs.dreamstime.com/z/indian-call-center-agent-shows-ok-gesture-showing-against-working-operators-bright-office-173649185.jpg"
    msg = f"Here's the link to get on a call with me right now!\n{link}"
    await update.message.reply_text(msg)

async def setup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    setup_data = context.user_data.get("setup", "standby")
    if setup_data == "finish" or setup_data == "standby":
        context.user_data["setup"] = "init"; await setup(update, context)
    else:
        try:
            # Delete prev setup message
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=context.user_data["setup_msg_id"]
            )
            context.user_data["setup"] = "init"; await setup(update, context)
        except Exception as e:
            await update.message.reply_text(f"An error occured, but don't worry. I'll be back... Error ha-1")
            print(f"Failed to delete message: {e}")

async def checkin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    now = get_current_time_in_singapore()
    today = now.date()
    user = update.effective_user
    username = user.username or f"User {user.id}"
    user_data = context.user_data.setdefault("user_info", {})

    if user_data: last_checkin, current_streak = user_data.get("Last Check-in", None), user_data.get("Streak", 0)
    else: last_checkin, current_streak = None, 0

    if not last_checkin:
        current_streak = 1
        user_data["Streak"] = current_streak
        user_data["Max Streak"] = current_streak
        user_data["Last Check-in"] = today.strftime("%Y-%m-%d")
        await update.message.reply_text("Welcome to your streak journey! Current Streak: 1 day! 🚀")
    elif last_checkin == today:
        await update.message.reply_text("You've already checked in today! Keep it going tomorrow. 🌟")
    elif last_checkin == today - timedelta(days=1):
        current_streak += 1
        user_data["Streak"] = current_streak
        if user_data.get("Max Streak", 0) < current_streak:
            user_data["Max Streak"] = current_streak
        await update.message.reply_text(f"Great job! Your streak is now {current_streak} days! 🔥")
    else:
        current_streak = 1
        await update.message.reply_text("Welcome back! Your streak is reset to 1."
                                        f"\nPrevious streak: {user_data.get('Max Streak', 0)}🌈")
        user_data["Streak"] = current_streak
        user_data["Last Check-in"] = today.strftime("%Y-%m-%d")
        await db_set_user_profile(context, str(user.id))

    logger.info(f"User {username} streak data: {{'Last Check-in': {today}, 'current streak': {current_streak}}}")


async def leaderboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not leaderboard:
        await update.message.reply_text("No streaks yet! Be the first to start a streak. 🌟")
        return

    leaderboard_msg = "🏆 Leaderboard 🏆\n\n"
    for rank, (username, streak) in enumerate(leaderboard, start=1):
        leaderboard_msg += f"{rank}. {username}: {streak} days\n"

    await update.message.reply_text(leaderboard_msg)

async def id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(f"Here's your User ID:\n{user.id}")

async def save_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Use latest context data for data sync"""
    await sync_data_job(context, update.effective_user.id)

async def profile_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_info = context.user_data.get("user_info", {})
    user_limitations = context.user_data.get("user_limitations", {})
    await update.message.reply_text(
        f"-------- {user.first_name}'s Profile --------\n"
        f"{format_dict(user_info)}\n"
        f"\n-------- {user.first_name}'s Limitations --------\n"
        f"{format_dict(user_limitations)}"
    )


# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if update.message:
        await update.message.reply_text(f"An error occured, but don't worry. I'll be back... Error ha-0")