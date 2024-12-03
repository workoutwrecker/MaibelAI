from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

from profile.mgmt_utils import get_inline_markup
from utils import format_dict

AGE_OPTIONS = ["18-24", "25-34", "35-44", "45+"]
HEIGHT_OPTIONS_0 = ["<", "4'4 (132.1cm)", "4'5 (134.6cm)", "4'6 (137.2cm)", "4'7 (139.7cm)", ">"] 
HEIGHT_OPTIONS_1 = ["<", "4'8 (152.4cm)", "4'9 (154.9cm)", "4'10 (157.4cm)", "4'11 (160cm)", ">"] 
HEIGHT_OPTIONS_2 = ["<", "5'0 (152.4cm)", "5'1 (154.9cm)", "5'2 (157.4cm)", "5'3 (160cm)", ">"] 
HEIGHT_OPTIONS_3 = ["<", "5'4 (162.6cm)", "5'5 (165.1cm)", "5'6 (167.6cm)", "5'7 (170.2cm)", ">"]
HEIGHT_OPTIONS_4 = ["<", "5'8 (172.7cm)", "5'9 (175.3cm)", "5'10 (177.8cm)", "5'11 (180.3cm)", ">"]
HEIGHT_OPTIONS_5 = ["<", "6'0 (182.9cm)", "6'1 (185.4cm)", "6'2 (188cm)", "6'3 (190.5cm)", ">"]
WEIGHT_OPTIONS_0 = ["<", "100lbs (45.4kg)", "110lbs (49.9kg)", "120lbs (54.4kg)", "130lbs (59kg)", ">"]
WEIGHT_OPTIONS_1 = ["<", "140lbs (63.5kg)", "150lbs (68kg)", "160lbs (72.6kg)", "170lbs (77.1kg)", ">"]
WEIGHT_OPTIONS_2 = ["<", "180lbs (81.6kg)", "190lbs (86.2kg)", "200lbs (90.7kg)", "210lbs (95.3kg)", ">"]
WEIGHT_OPTIONS_3 = ["<", "220lbs (99.8kg)", "230lbs (104.3kg)", "240lbs (108.9kg)", "250lbs (113.4kg)", ">"]
WEIGHT_OPTIONS_4 = ["<", "260lbs (117.9kg)", "270lbs (122.5kg)", "280lbs (127kg)", "290lbs (131.5kg)", ">"]
WEIGHT_OPTIONS_5 = ["<", "300lbs (136.1kg)", "310lbs (140.6kg)", "320lbs (145.1kg)", "330lbs (149.7kg)", ">"]
GENDER_OPTIONS = ["Female", "Male", "Other"]
WORKOUTS_OPTIONS = ["1-2", "3-4", "5+"]
GOAL_OPTIONS = ["Lose weight", "Get stronger", "Build muscle", "Mix"]
WEAKNESS_OPTIONS = ["Bodily Pain", "Intensity Limit", "Womens issues", "Go Back"]
BODILY_PAIN_OPTIONS = ["Low back pain", "Knee pain", "Migraines", "Wrist pain"]
INTENSITY_OPTIONS = ["Can't sweat", "Low", "Medium"]
WOMENS_ISSUES_OPTIONS = ["Pregnancy", "Postpartum"]
GO_BACK_OPTION = ["Go Back"]
REMOVE_OPTION = ["Remove"]

async def setup_profile(update: Update, context: CallbackContext) -> None:
    """Display the main profile setup menu"""
    context.user_data["callbackquery"] = "Profile"
    msg = "Please set up your profile by selecting an option:"
    user_info = context.user_data.get("user_info", {})
    options = [
        ("Age ✅" if "Age" in user_info else "Age❔"),
        ("Height ✅" if "Height" in user_info else "Height❔"),
        ("Weight ✅" if "Weight" in user_info else "Weight❔"),
    ]
    keyboard = get_inline_markup([[options[0], options[1]], [options[2]], ["Finish"]])
    if update.message:
        setup_msg = await update.message.reply_text(msg, reply_markup=keyboard)
        context.user_data["setup_msg_id"] = setup_msg.message_id
    elif update.callback_query:
        await update.callback_query.message.edit_text(msg, reply_markup=keyboard)

async def profile_option_caller(update: Update, context: CallbackContext, function_name:str, function_params:list=[]) -> None:
    function = globals().get(function_name)
    if function and not function_params:
        await function(update, context)
    elif function and function_params:
        await function(update, context, *function_params)

async def ask_age(update: Update, context: CallbackContext) -> None:
    context.user_data["callbackquery"] = "profile_age"
    keyboard = get_inline_markup([AGE_OPTIONS])
    await update.callback_query.message.edit_text("How old are you?", reply_markup=keyboard)

async def ask_height(update: Update, context: CallbackContext, height_option_index: int = 0) -> None:
    height_options_map = [
        HEIGHT_OPTIONS_0, HEIGHT_OPTIONS_1, HEIGHT_OPTIONS_2,
        HEIGHT_OPTIONS_3, HEIGHT_OPTIONS_4, HEIGHT_OPTIONS_5
    ]
    print("height_option_index: ", height_option_index)
    selected_options = height_options_map[height_option_index]
    context.user_data["callbackquery"] = f"profile_height_{height_option_index}"
    keyboard = get_inline_markup([selected_options])
    await update.callback_query.message.edit_text("What's your height?", reply_markup=keyboard)

async def ask_weight(update: Update, context: CallbackContext, weight_option_index: int = 0) -> None:
    weight_options_map = [
        WEIGHT_OPTIONS_0, WEIGHT_OPTIONS_1, WEIGHT_OPTIONS_2,
        WEIGHT_OPTIONS_3, WEIGHT_OPTIONS_4, WEIGHT_OPTIONS_5
    ]
    selected_options = weight_options_map[weight_option_index]
    context.user_data["callbackquery"] = f"profile_weight_{weight_option_index}"
    keyboard = get_inline_markup([selected_options])
    await update.callback_query.message.edit_text("How much do you weigh?", reply_markup=keyboard)

async def finish_profile(update: Update, context: CallbackContext) -> None:
    user_info = context.user_data.get("user_info", {})
    context.user_data["callbackquery"] = "profile_finish"
    await update.callback_query.message.edit_text(
        f"-------- Profile --------\n"
        f"{format_dict(user_info)}"
    )