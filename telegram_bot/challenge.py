from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import CallbackContext

from utils import get_current_time_in_singapore

async def start_challenge(update: Update, context: CallbackContext) -> None:
    context.user_data["challengeDay"] = 1
    context.user_data["challengeTime"] = get_current_time_in_singapore
    await send_challenge_message(update, context)

async def send_challenge_message(update: Update, context: CallbackContext) -> None:
    """Send Challenge + Scenery Photo"""
    day = context.user_data.get("challengeDay", [])
    await update.message.reply_text(f"Welcome to Day {day} of your challenge!")

async def check_challenge_progress(context: CallbackContext) -> None:
    """Function to check whether the user has NOT completed their challenge
    Halfway through the time period, we nudge the user
    After 24h of challenge start, we give them the option to restart the challenge"""

    user_data = context.user_data
    print("User data: ", user_data)
    challenge_time = user_data.get("challengeTime", [])
    challenge_day = user_data.get("challengeDay", [])
    if not challenge_time: return
    
    is_completed = user_data.get("challengeStatus", False)
    if is_completed: return
    
    if isinstance(challenge_time, str): challengeTime = datetime.fromisoformat(challenge_time)

    elapsed_time = get_current_time_in_singapore() - challenge_time
    if timedelta(hours=12) <= elapsed_time < timedelta(hours=24): # Send a nudge after 12 hours
        await context.bot.send_message(
            chat_id=context.job.chat_id,
            text="Reminder: It's been 12 hours since you started your challenge. Keep going!"
        )
    elif elapsed_time >= timedelta(hours=24):
        await context.bot.send_message(
            chat_id=context.job.chat_id,
            text="It's been 24 hours, and your challenge isn't complete. Click to restart."
        )

async def finish_challenge(context: CallbackContext) -> None:
    user_data = context.user_data
    user_data["challengeDay"] = 99
    await context.bot.send_message(chat_id=context.job.context, text="Challenge complete!")