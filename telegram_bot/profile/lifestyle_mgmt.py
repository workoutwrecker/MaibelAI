from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

from profile.mgmt_utils import get_inline_markup
from utils import format_dict

SLEEP_OPTIONS = ["<5h", "5-6h", "7-8h", ">8h"]
RESTED_OPTIONS = ["Rarely", "Sometimes", "Always"]
STRESS_OPTIONS = ["1", "2", "3", "4", "5"]
MOVEMENT_OPTIONS = ["Calculate Now", "<10mins", "10-30mins", "30mins-1hr", ">1hr"]

async def setup_lifestyle(update: Update, context: CallbackContext) -> None:
    """Display the main lifestyle setup menu"""
    context.user_data["callbackquery"] = "Lifestyle"
    msg = "Please set up your lifestyle profile by selecting an option:"
    user_info = context.user_data.get("lifestyle_info", {})
    options = [
        ("Sleep ✅" if "Sleep" in user_info else "Sleep❔"),
        ("Rested ✅" if "Rested" in user_info else "Rested❔"),
        ("Stress ✅" if "Stress" in user_info else "Stress❔"),
        ("Movement ✅" if "Movement" in user_info else "Movement❔"),
    ]
    keyboard = get_inline_markup([[options[0], options[1]], [options[2], options[3], "Finish"]])
    if update.message:
        setup_msg = await update.message.reply_text(msg, reply_markup=keyboard)
        context.user_data["setup_msg_id"] = setup_msg.message_id
    elif update.callback_query:
        await update.callback_query.message.edit_text(msg, reply_markup=keyboard)

async def lifestyle_option_caller(update: Update, context: CallbackContext, function_name:str) -> None:
    function = globals().get(function_name)
    if function:
        await function(update, context)

async def ask_sleep(update: Update, context: CallbackContext) -> None:
    context.user_data["callbackquery"] = "lifestyle_sleep"
    keyboard = get_inline_markup([SLEEP_OPTIONS])
    await update.callback_query.message.edit_text("How many hours of sleep do you get on an average night?", reply_markup=keyboard)

async def ask_rested(update: Update, context: CallbackContext) -> None:
    context.user_data["callbackquery"] = "lifestyle_rested"
    keyboard = get_inline_markup([RESTED_OPTIONS])
    await update.callback_query.message.edit_text("Do you feel rested when you wake up?", reply_markup=keyboard)

async def ask_stress(update: Update, context: CallbackContext) -> None:
    context.user_data["callbackquery"] = "lifestyle_stress"
    keyboard = get_inline_markup([STRESS_OPTIONS])
    await update.callback_query.message.edit_text(
        "On a scale of 1 to 5, how stressed do you feel daily? (1 = Not at all, 5 = Very stressed)", reply_markup=keyboard)

async def ask_movement(update: Update, context: CallbackContext) -> None:
    context.user_data["callbackquery"] = "lifestyle_movement"
    keyboard = get_inline_markup([[MOVEMENT_OPTIONS[0], MOVEMENT_OPTIONS[1]], [MOVEMENT_OPTIONS[2], MOVEMENT_OPTIONS[3]], [MOVEMENT_OPTIONS[4]]])
    await update.callback_query.message.edit_text("How much time do you spend moving around daily?", reply_markup=keyboard)

async def finish_lifestyle(update: Update, context: CallbackContext) -> None:
    user_info = context.user_data.get("lifestyle_info", {})
    context.user_data["callbackquery"] = "lifestyle_finish"
    await update.callback_query.message.edit_text(
        f"-------- Lifestyle Profile --------\n"
        f"{format_dict(user_info)}"
    )