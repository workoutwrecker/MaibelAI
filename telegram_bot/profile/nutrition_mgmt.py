from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

from profile.mgmt_utils import get_inline_markup
from utils import format_dict

MEAL_OPTIONS = ["1", "2", "3", "4+"]
MEAL_TIMES_OPTIONS = ["8am, 8pm", "8am, 9pm", "8am, 10pm"]
HOME_COOKED_MEALS_OPTIONS = ["Daily", "Few times Weekly", "Rarely"]
WATER_OPTIONS = ["<1 litre", "1-2 litres", ">2 litres"]
DIETARY_RESTRICTIONS_OPTIONS = ["Yes", "No"]


async def setup_nutrition(update: Update, context: CallbackContext) -> None:
    """Display the main nutrition setup menu"""
    context.user_data["callbackquery"] = "Nutrition"
    msg = "Please set up your nutrition profile by selecting an option:"
    user_info = context.user_data.get("user_info", {})
    options = [
        ("Meals ✅" if "Meals" in user_info else "Meals❔"),
        ("First/Last Meal ✅" if "First/Last Meal" in user_info else "First/Last Meal❔"),
        ("Dietary Restrictions ✅" if "Dietary Restrictions" in user_info else "Dietary Restrictions❔"),
        ("Home Cooked Meals ✅" if "Home Cooked Meals" in user_info else "Home Cooked Meals❔"),
        ("Water Intake ✅" if "Water Intake" in user_info else "Water Intake❔"),
    ]
    keyboard = get_inline_markup([[options[0], options[1]], [options[2], options[3]], [options[4], "Finish"]])
    if update.message:
        setup_msg = await update.message.reply_text(msg, reply_markup=keyboard)
        context.user_data["setup_msg_id"] = setup_msg.message_id #For deleting previous setup message
    elif update.callback_query:
        await update.callback_query.message.edit_text(msg, reply_markup=keyboard)

async def nutrition_option_caller(update: Update, context: CallbackContext, function_name:str) -> None:
    print("Nutrition option caller: ", function_name)
    function = globals().get(function_name)
    if function:
        await function(update, context)

async def ask_meals(update: Update, context: CallbackContext) -> None: #TODO: Turn into a more dynamic option
    context.user_data["callbackquery"] = "nutrition_meals"
    keyboard = get_inline_markup([MEAL_OPTIONS])
    await update.callback_query.message.edit_text("How many meals do you eat in a day?", reply_markup=keyboard)

async def ask_meal_times(update: Update, context: CallbackContext) -> None:
    context.user_data["callbackquery"] = "nutrition_meal_times"
    keyboard = get_inline_markup([MEAL_TIMES_OPTIONS])
    await update.callback_query.message.edit_text("When’s your first and last meal?", reply_markup=keyboard)

async def ask_dietary_restrictions(update: Update, context: CallbackContext) -> None:
    context.user_data["callbackquery"] = "nutrition_dietary_restrictions"
    keyboard = get_inline_markup([DIETARY_RESTRICTIONS_OPTIONS])
    await update.callback_query.message.edit_text("Do you have any dietary restrictions?", reply_markup=keyboard)

async def ask_home_cooked_meals(update: Update, context: CallbackContext) -> None:
    context.user_data["callbackquery"] = "nutrition_home_cooked_meals"
    keyboard = get_inline_markup([HOME_COOKED_MEALS_OPTIONS])
    await update.callback_query.message.edit_text("How often do you eat home-cooked meals?", reply_markup=keyboard)

async def ask_water_intake(update: Update, context: CallbackContext) -> None:
    context.user_data["callbackquery"] = "nutrition_water_intake"
    keyboard = get_inline_markup([WATER_OPTIONS])
    await update.callback_query.message.edit_text("How much water do you drink daily?", reply_markup=keyboard)

async def finish_nutrition(update: Update, context: CallbackContext) -> None:
    user_info = context.user_data.get("user_info", {})
    context.user_data["callbackquery"] = "nutrition_finish"
    msg = f"-------- Nutrition Profile --------\n"\
        f"{format_dict(user_info)}"
    await update.message.reply_text(msg)
    
    