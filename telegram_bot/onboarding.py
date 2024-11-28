import asyncio
from datetime import datetime, timedelta, time
from telegram import Update
from telegram.ext import CallbackContext
from database import db_update_user_profile

async def start_onboarding(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    context.user_data["onboardDay"] = 1
    context.user_data["onboardTIme"] = datetime.now()
    db_update_user_profile(user_id, "onboardDay", 1)
    db_update_user_profile(user_id, "onboardTime", datetime.now())
    await send_onboarding_message(update, context)

async def send_onboarding_message(update: Update, context: CallbackContext) -> None:
    day = context.user_data.get("onboardDay", [])
    await update.message.reply_text(f"Welcome to Day {day} of your onboarding!")

async def check_onboarding_progress(context: CallbackContext) -> None:
    """Function to check whether the user has NOT completed their onboarding challenge
    Halfway through the time period, we nudge the user
    After 24h of challenge start, we give them the option to restart the challenge"""
    user_data = context.user_data
    onboard_time = user_data.get("onboardTime", [])
    onboard_day = user_data.get("onboardDay", [])
    if not onboard_time or onboard_day == 99:
        return
    
    is_completed = user_data.get("onboardChallengeStatus", False)
    if is_completed:
        return
    
    if isinstance(onboard_time, str):
        onboard_time = datetime.fromisoformat(onboard_time)

    now = datetime.now(onboard_time.tzinfo) # Use the same timezone as `onboard_time`
    elapsed_time = now - onboard_time
    if timedelta(hours=12) <= elapsed_time < timedelta(hours=24): # Send a nudge after 12 hours
        await context.bot.send_message(
            chat_id=context.job.chat_id,
            text="Reminder: It's been 12 hours since you started your onboarding challenge. Keep going!"
        )
    elif elapsed_time >= timedelta(hours=24):
        await context.bot.send_message(
            chat_id=context.job.chat_id,
            text="It's been 24 hours, and your onboarding challenge isn't complete. Click to restart."
        )

async def finish_onboarding(context: CallbackContext) -> None:
    user_data = context.user_data
    user_data["onboardDay"] = 99
    await context.bot.send_message(chat_id=context.job.context, text="Onboarding complete!")