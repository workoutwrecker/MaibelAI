from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

from profile.mgmt_utils import get_inline_markup
from utils import format_dict

SLEEP_OPTIONS = ["<5 hours", "5-6 hours", "7-8 hours", "9+ hours"]
RESTED_OPTIONS = ["Rarely", "Sometimes", "Always"]
STRESS_OPTIONS = ["1 (Not at all)", "2", "3", "4", "5 (Very stressed)"]

async def setup_lifestyle(update: Update, context: CallbackContext) -> None:
    """Display the main lifestyle setup menu"""
    msg = "Please set up your lifestyle profile by selecting an option:"
    user_info = context.user_data.get("lifestyle_info", {})
    options = [
        ("Sleep ✅" if "Sleep" in user_info else "Sleep❔"),
        ("Rested ✅" if "Rested" in user_info else "Rested❔"),
        ("Stress ✅" if "Stress" in user_info else "Stress❔"),
        ("Stress Management ✅" if "Stress Management" in user_info else "Stress Management❔"),
        ("Steps ✅" if "Steps" in user_info else "Steps❔"),
    ]
    keyboard = get_inline_markup([[options[0], options[1]], [options[2], options[3], options[4]], ["Finish"]])
    if update.message:
        setup_msg = await update.message.reply_text(msg, reply_markup=keyboard)
        context.user_data["setup_msg_id"] = setup_msg.message_id
    elif update.callback_query:
        await update.callback_query.message.edit_text(msg, reply_markup=keyboard)

async def ask_sleep(update: Update, context: CallbackContext) -> None:
    context.user_data["callbackquery"] = "sleep"
    keyboard = get_inline_markup([SLEEP_OPTIONS])
    await update.callback_query.message.edit_text("How many hours of sleep do you get on an average night?", reply_markup=keyboard)

async def ask_rested(update: Update, context: CallbackContext) -> None:
    context.user_data["callbackquery"] = "rested"
    keyboard = get_inline_markup([RESTED_OPTIONS])
    await update.callback_query.message.edit_text("Do you feel rested when you wake up?", reply_markup=keyboard)

async def ask_stress(update: Update, context: CallbackContext) -> None:
    context.user_data["callbackquery"] = "stress"
    keyboard = get_inline_markup([STRESS_OPTIONS])
    await update.callback_query.message.edit_text("On a scale of 1 to 5, how stressed do you feel daily?", reply_markup=keyboard)

async def ask_stress_management(update: Update, context: CallbackContext) -> None:
    context.user_data["callbackquery"] = "stress_management"
    await update.callback_query.message.edit_text("Do you have any habits to manage stress (e.g., journaling, deep breathing)?")

async def ask_steps(update: Update, context: CallbackContext) -> None:
    context.user_data["callbackquery"] = "steps"
    await update.callback_query.message.edit_text("How many steps do you clock daily?")

async def finish_lifestyle(update: Update, context: CallbackContext) -> None:
    user_info = context.user_data.get("lifestyle_info", {})
    context.user_data["callbackquery"] = "finish"
    await update.callback_query.message.edit_text(
        f"-------- Lifestyle Profile --------\n"
        f"{format_dict(user_info)}"
    )
    # Move to the next section, e.g., profile
    await setup_profile(update, context)