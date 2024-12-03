from telegram import Update
from telegram.ext import CallbackContext
from utils import format_dict

async def start_challenges(update: Update, context: CallbackContext) -> None:
    """Right after onboarding is finished (See all_mgmt)"""
    user_info = context.user_data.setdefault("user_info", {})
    fade_away_emoji_fileid = "CgACAgQAAxkBAAINmGdPIDhoYYBoCl_-LqQQI0oZF-SHAAI0AwACQeAkU-xJ8F_Y3KzoNgQ"
    msg = "Alright, I've got the scoop. You're an interesting mix of strengths and struggles—and " \
        "that's perfect for the adventure ahead. Complete your first challenge tomorrow, and you'll " \
        "unlock something the secret letter Ji-ae's grandmother wrote."
    chat_id = update.effective_user.id #Chat id is user id

    if user_info.get("Challenge Day"): 
        await context.bot.send_message(chat_id=chat_id, text="You've already started a challenge! Keep it up!")
        return
    user_info["Challenge Day"] = 0
    
    await context.bot.send_animation(chat_id=chat_id, animation=fade_away_emoji_fileid)
    await context.bot.send_message(chat_id=chat_id, text=msg)

        