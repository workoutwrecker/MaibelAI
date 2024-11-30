from telegram import Update
from telegram.ext import CallbackContext

from profile.mgmt_utils import get_inline_markup
from profile.nutrition_mgmt import setup_nutrition, nutrition_option_caller
from profile.profile_mgmt import setup_profile
from profile.lifestyle_mgmt import setup_lifestyle

#All mgmt
OPTIONS = ["Nutrition", "Lifestyle", "Profile", "Others"]

#Nutrition mgmt
MEAL_OPTIONS = ["1", "2", "3", "4+"]
MEAL_TIMES_OPTIONS = ["8am, 8pm", "8am, 9pm", "8am, 10pm"]
HOME_COOKED_OPTIONS = ["Daily", "Few times a week", "Rarely"]
WATER_OPTIONS = ["<1 litre", "1-2 litres", "More than 2 litres"]
DIETARY_RESTRICTIONS_OPTIONS = ["Yes", "No"]

async def update_user_profile(update: Update, context: CallbackContext) -> None:
    """Very dynamic callback query handler"""
    cbq = context.user_data["callbackquery"]
    match cbq:
        case "onboarding":
            callback_data = update.callback_query.data
            match callback_data:
                case "Nutrition": await setup_nutrition(update, context)
                case "Lifestyle": await setup_lifestyle(update, context)
                case "Profile": await setup_profile(update, context)
                case "Others": return
                case _: return
        case "nutrition_meals": callback_data_handler(
            update, context, MEAL_OPTIONS, nutrition_option_caller, "ask_meals")
        case "nutrition_meal_times": callback_data_handler(
            update, context, MEAL_TIMES_OPTIONS, nutrition_option_caller, "ask_meal_times")
        case "nutrition_home_cooked": callback_data_handler(
            update, context, HOME_COOKED_OPTIONS, nutrition_option_caller, "ask_home_cooked")
        case "nutrition_water_intake": callback_data_handler(
            update, context, WATER_OPTIONS, nutrition_option_caller, "ask_water_intake")
        case "nutrition_dietary_restrictions": callback_data_handler(
            update, context, DIETARY_RESTRICTIONS_OPTIONS, nutrition_option_caller, "ask_dietary_restrictions")
            
async def callback_data_handler(update, context, options, function, params=None):
    callback_data = update.callback_query.data
    if callback_data in options:
        if params is None: await function(update, context)
        else: await function(update, context, params)

async def setup(update: Update, context: CallbackContext) -> None:
    msg = "Please set up your profile by selecting an option:"
    keyboard = get_inline_markup([OPTIONS])
    if update.message:
        setup_msg = await update.message.reply_text(msg, reply_markup=keyboard)
        context.user_data["setup_msg_id"] = setup_msg.message_id
    elif update.callback_query:
        await update.callback_query.message.edit_text(msg, reply_markup=keyboard)


