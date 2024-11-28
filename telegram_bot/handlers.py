import logging
from datetime import timedelta
from telegram import Update
from telegram.ext import ContextTypes

from profile_mgmt import setup
from utils import escaped_string, get_current_time_in_singapore, get_limitation_category_by_id, get_limitation_label_by_id
from database import update_streak, get_leaderboard, get_db_connection, db_get_user_profile

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Start command handler
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users WHERE user_id = %s', (user.id,))
    result = cursor.fetchone()

    if result:
        final_msg = f"Welcome back, {user.mention_markdown_v2()}"
        user_limitations = context.user_data.get("user_limitations", {})
        user_profile = db_get_user_profile(user.id)
        user_info = context.user_data.get("user_info", {})
        context.user_data["setup"] = "standby"
        for index, key in enumerate(["onboardDay", "onboardTime","Age", "Gender", "Workouts", "Goal"]):
            if user_profile[index] != '':
                user_info[key] = user_profile[index]
        if not user_limitations:
            for limitation_id in user_profile[6]:
                category = get_limitation_category_by_id(limitation_id)
                if category not in user_limitations:
                    user_limitations[category] = [] #Initialise category if not exists
                user_limitations[category].append(get_limitation_label_by_id(limitation_id))
            context.user_data["user_limitations"] = user_limitations
            context.user_data["user_info"] = user_info
    else:
        cursor.execute('''
            INSERT INTO users (user_id, username, age, gender, workouts, goal, limitations)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (user.id, user.username, '', '', '', '', []))
        conn.commit()
        msg = (f"Hi {user.mention_markdown_v2()}")
        msg_2 = escaped_string("! I'm a bot powered by AI. Ask me anything related to women's fitness or just chat!\n\n"
                "/setup - Profile Setup ℹ️\n"
                "/call - Call 📞\n"
                "/app - Download our app!\n\n"
                "Let's get started with your profile setup!")
        final_msg = f"{msg}{msg_2}"

    conn.close()
    await update.message.reply_text(final_msg, parse_mode="MarkdownV2")
    if not result:
        await setup_handler(update, context)
    

# Call command handler
async def call_bot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    link = "https://thumbs.dreamstime.com/z/indian-call-center-agent-shows-ok-gesture-showing-against-working-operators-bright-office-173649185.jpg"
    msg = f"Here's the link to get on a call with me right now!\n{link}"
    await update.message.reply_text(msg)

async def setup_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_data = context.user_data
    if "setup" not in user_data:
        await start_handler(update, context)
    elif user_data["setup"] == "finish" or user_data["setup"] == "standby":
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

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT last_checkin, current_streak FROM streaks WHERE user_id = %s', (user.id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        last_checkin, current_streak = result
        last_checkin = last_checkin if last_checkin else None
    else:
        last_checkin, current_streak = None, 0

    if not last_checkin:
        current_streak = 1
        await update.message.reply_text("Welcome to your streak journey! Current Streak: 1 day! 🚀")
    elif last_checkin == today:
        await update.message.reply_text("You've already checked in today! Keep it going tomorrow. 🌟")
    elif last_checkin == today - timedelta(days=1):
        current_streak += 1
        await update.message.reply_text(f"Great job! Your streak is now {current_streak} days! 🔥")
    else:
        current_streak = 1
        await update.message.reply_text(f"Welcome back! Your streak is reset to 1. \nPrevious streak: {current_streak}🌈")

    update_streak(user.id, username, today.strftime("%Y-%m-%d"), current_streak)

    logger.info(f"User {username} streak data: {{'last_checkin': {today}, 'current_streak': {current_streak}}}")


async def leaderboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    leaderboard = get_leaderboard()
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

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if update.message:
        await update.message.reply_text(f"An error occured, but don't worry. I'll be back... Error ha-0")
