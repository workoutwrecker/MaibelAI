from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

from profile.mgmt_utils import get_inline_markup
from utils import format_dict

async def setup_profile(update: Update, context: CallbackContext) -> None:
    """Display the main profile setup menu"""
    msg = "Please set up your profile by selecting an option:"
    user_info = context.user_data.get("profile_info", {})
    options = [
        ("Name ✅" if "Name" in user_info else "Name❔"),
        ("Age ✅" if "Age" in user_info else "Age❔"),
        ("Height ✅" if "Height" in user_info else "Height❔"),
        ("Weight ✅" if "Weight" in user_info else "Weight❔"),
    ]
    keyboard = get_inline_markup([[options[0], options[1]], [options[2], options[3]], ["Finish"]])
    if update.message:
        setup_msg = await update.message.reply_text(msg, reply_markup=keyboard)
        context.user_data["setup_msg_id"] = setup_msg.message_id
    elif update.callback_query:
        await update.callback_query.message.edit_text(msg, reply_markup=keyboard)

async def ask_name(update: Update, context: CallbackContext) -> None:
    context.user_data["callbackquery"] = "name"
    await update.callback_query.message.edit_text("What’s your name?")

async def ask_age(update: Update, context: CallbackContext) -> None:
    context.user_data["callbackquery"] = "age"
    await update.callback_query.message.edit_text("How old are you?")

async def ask_height(update: Update, context: CallbackContext) -> None:
    context.user_data["callbackquery"] = "height"
    await update.callback_query.message.edit_text("What’s your height?")

async def ask_weight(update: Update, context: CallbackContext) -> None:
    context.user_data["callbackquery"] = "weight"
    await update.callback_query.message.edit_text("How much do you weigh?")

async def finish_profile(update: Update, context: CallbackContext) -> None:
    user_info = context.user_data.get("profile_info", {})
    context.user_data["callbackquery"] = "finish"
    await update.callback_query.message.edit_text(
        f"-------- Profile --------\n"
        f"{format_dict(user_info)}"
    )