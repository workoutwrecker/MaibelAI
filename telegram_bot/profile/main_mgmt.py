from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

from profile.mgmt_utils import get_inline_markup, normalise_option, check_user_info
from profile.nutrition_mgmt import nutrition_option_caller
from profile.lifestyle_mgmt import lifestyle_option_caller
from profile.profile_mgmt import profile_option_caller
from utils import format_dict
from actions import start_challenges

#All mgmt
OPTIONS = ["Nutrition", "Profile", "Finish"]

#Nutrition mgmt
NUTRITION_OPTIONS = ["Meals", "First/Last Meal", "Dietary Restrictions", "Home Cooked Meals", "Water Intake", "Finish"]
MEAL_OPTIONS = ["1", "2", "3", "4+"]
MEAL_TIMES_OPTIONS = ["8am, 8pm", "8am, 9pm", "8am, 10pm"]
HOME_COOKED_MEALS_OPTIONS = ["Daily", "Few times Weekly", "Rarely"]
WATER_OPTIONS = ["<1 litre", "1-2 litres", ">2 litres"]
DIETARY_RESTRICTIONS_OPTIONS = ["Yes", "No"]

#Profile mgmt
PROFILE_OPTIONS = ["Age", "Height", "Weight", "Finish"]
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
ALL_HEIGHT_OPTIONS = [HEIGHT_OPTIONS_0, HEIGHT_OPTIONS_1, HEIGHT_OPTIONS_2, HEIGHT_OPTIONS_3, HEIGHT_OPTIONS_4, HEIGHT_OPTIONS_5]
ALL_WEIGHT_OPTIONS = [WEIGHT_OPTIONS_0, WEIGHT_OPTIONS_1, WEIGHT_OPTIONS_2, WEIGHT_OPTIONS_3, WEIGHT_OPTIONS_4, WEIGHT_OPTIONS_5]

#Lifestyle mgmt
LIFESTYLE_OPTIONS = ["Sleep", "Rested", "Stress", "Movement", "Finish"]
SLEEP_OPTIONS = ["<5h", "5-6h", "7-8h", ">8h"]
RESTED_OPTIONS = ["Rarely", "Sometimes", "Always"]
STRESS_OPTIONS = ["1", "2", "3", "4", "5"]
MOVEMENT_OPTIONS = ["Calculate Now", "<10mins", "10-30mins", "30mins-1hr", ">1hr"]


async def update_user_profile(update: Update, context: CallbackContext) -> None:
    """Very dynamic callback query handler"""
    cbq = context.user_data["callbackquery"]
    print("cbq: ", cbq)
    cur_handler = context.user_data["callback_handler"]
    match cur_handler:
        case "onboarding": await handle_onboard(update, context, cbq)
        case "challenge": await handle_challenge(update, context, cbq)
        case _: raise ValueError(f"Invalid callback handler: {cur_handler}")
    
async def handle_onboard(update, context, cbq):
    match cbq:
        # Onboarding
        case "onboarding": await callback_data_handler(
            update, context, OPTIONS, [nutrition_option_caller, profile_option_caller], 
            ["setup_nutrition", "setup_profile"])

        case "Nutrition": await callback_data_handler(update, context, NUTRITION_OPTIONS, 
        [nutrition_option_caller], ["ask_meals", "ask_meal_times", "ask_dietary_restrictions","ask_home_cooked_meals", "ask_water_intake"])
        
        case "Profile": await callback_data_handler(update, context, PROFILE_OPTIONS, 
        [profile_option_caller], ["ask_age", "ask_height", "ask_weight"])
        
        case "nutrition_meals": await callback_data_handler(
            update, context, MEAL_OPTIONS, [nutrition_option_caller], ["setup_nutrition"], ["user_info", "Meals"])

        case "nutrition_meal_times": await callback_data_handler(
            update, context, MEAL_TIMES_OPTIONS, [nutrition_option_caller], ["setup_nutrition"], ["user_info", "First/Last Meal"])

        case "nutrition_home_cooked_meals": await callback_data_handler(
            update, context, HOME_COOKED_MEALS_OPTIONS, [nutrition_option_caller], ["setup_nutrition"], ["user_info", "Home Cooked Meals"])

        case "nutrition_water_intake": await callback_data_handler(
            update, context, WATER_OPTIONS, [nutrition_option_caller], ["setup_nutrition"], ["user_info", "Water Intake"])

        case "nutrition_dietary_restrictions": await callback_data_handler(
            update, context, DIETARY_RESTRICTIONS_OPTIONS, [nutrition_option_caller], ["setup_nutrition"], ["user_info", "Dietary Restrictions"])

        case "profile_age": await callback_data_handler(
            update, context, AGE_OPTIONS, [profile_option_caller], ["setup_profile"], ["user_info", "Age"])

        case "profile_height_0" | "profile_height_1" | "profile_height_2" | "profile_height_3" | "profile_height_4" | "profile_height_5": 
            index = int(cbq.split("_")[-1])
            options=ALL_HEIGHT_OPTIONS[index]
            await callback_data_handler_special(update, context, options, "ask_height", index, ["user_info", "Height"])

        case "profile_weight_0" | "profile_weight_1" | "profile_weight_2" | "profile_weight_3" | "profile_weight_4" | "profile_weight_5": 
            index = int(cbq.split("_")[-1])
            options=ALL_WEIGHT_OPTIONS[index]
            await callback_data_handler_special(update, context, options, "ask_weight", index, ["user_info", "Weight"])
            
        case "nutrition_finish" | "profile_finish": await callback_data_handler(update, context, ["Finish"], [onboard_setup])

        case "onboard_finish": 
            print("onboard_finish_yes")
            if update.callback_query.data == "onboard_finish_yes": await handle_onboard_finish_response(update, context)
            elif update.callback_query.data == "onboard_finish_no": 
                context.user_data["callbackquery"] = "onboarding"
                await onboard_setup(update, context)

async def handle_challenge(update, context, cbq):
    match cbq:
        case "challenge": await callback_data_handler(update, context, LIFESTYLE_OPTIONS)

        case "Lifestyle": await callback_data_handler(update, context, LIFESTYLE_OPTIONS, 
        [lifestyle_option_caller], ["ask_sleep", "ask_rested", "ask_stress", "ask_movement"])
            
        case "lifestyle_sleep": await callback_data_handler(
            update, context, SLEEP_OPTIONS, [lifestyle_option_caller], ["setup_lifestyle"], ["lifestyle_info", "Sleep"])

        case "lifestyle_rested": await callback_data_handler(
            update, context, RESTED_OPTIONS, [lifestyle_option_caller], ["setup_lifestyle"], ["lifestyle_info", "Rested"])

        case "lifestyle_stress": await callback_data_handler(
            update, context, STRESS_OPTIONS, [lifestyle_option_caller], ["setup_lifestyle"], ["lifestyle_info", "Stress"])

        case "lifestyle_movement": await callback_data_handler(
            update, context, MOVEMENT_OPTIONS, [lifestyle_option_caller], ["setup_lifestyle"], ["lifestyle_info", "Movement"])


async def onboard_setup(update: Update, context: CallbackContext) -> None:
    context.user_data["callbackquery"] = "onboarding"
    context.user_data["callback_handler"] = "onboarding"
    msg = "Please set up your profile by selecting an option:"
    keyboard = get_inline_markup([OPTIONS])
    if update.message:
        setup_msg = await update.message.reply_text(msg, reply_markup=keyboard)
        context.user_data["setup_msg_id"] = setup_msg.message_id
    elif update.callback_query:
        await update.callback_query.message.edit_text(msg, reply_markup=keyboard)

async def challenge_setup(update: Update, context: CallbackContext) -> None:
    context.user_data["callbackquery"] = "challenge"
    context.user_data["callback_handler"] = "challenge"
    msg = "Please set up your lifestyle by selecting an option:"
    keyboard = get_inline_markup([LIFESTYLE_OPTIONS])
    if update.message:
        setup_msg = await update.message.reply_text(msg, reply_markup=keyboard)
        context.user_data["setup_msg_id"] = setup_msg.message_id
    elif update.callback_query:
        await update.callback_query.message.edit_text(msg, reply_markup=keyboard)

async def callback_data_handler_special(update, context, options, function, index, set_info=[]):
    """Callback query handler for height and weight"""
    callback_data = normalise_option(update.callback_query.data)
    print("callback_data: ", callback_data)
    if callback_data not in options: return
    if callback_data == "<":
        if index == 0: index = 6 #Loop through options
        await profile_option_caller(update, context, function, [index-1])
    elif callback_data == ">":
        if index == 5: index = -1
        await profile_option_caller(update, context, function, [index+1])
    else:
        if set_info:
            if set_info[0] not in context.user_data: context.user_data[set_info[0]] = {}
            context.user_data[set_info[0]][set_info[1]] = callback_data
            print("Set info: ", set_info[0], set_info[1])
        await profile_option_caller(update, context, "setup_profile")



async def callback_data_handler(update, context, options, functions, params=[], set_info=[]):
    callback_data = normalise_option(update.callback_query.data)
    if callback_data not in options: return
    if callback_data == "Finish": 
        if options != OPTIONS: await onboard_setup(update, context); return
        elif options == OPTIONS and not context.user_data.get("Challenge Day", {}):
            missing_user_info = check_user_info(context)
            if missing_user_info:
                missing_nutrition, missing_profile = check_user_info(context)
                msg = f"Missing\nNutrition: {missing_nutrition}\nProfile: {missing_profile}."
                await context.bot.send_message(chat_id=update.effective_user.id, text=msg); return
            await onboard_finish(update, context); return #First time onboarding
        else: await handle_onboard_finish_response(update, context); return #Reseting profile information
    if set_info:
        if set_info[0] not in context.user_data: context.user_data[set_info[0]] = {}
        context.user_data[set_info[0]][set_info[1]] = callback_data #Set user data for relevant option
        print("Set info: ", set_info[0], set_info[1])

    functions_length = len(functions)
    params_length = len(params)
    #This should signal the final branch of setup
    if functions_length == 1:
        if params_length == 1: await functions[0](update, context, params[0]); return
        elif not params: await functions[0](update, context); return
        else: 
            index = options.index(callback_data)
            param = params[index]
            await functions[0](update, context, param); return 

    index = options.index(callback_data)
    param = params[index]
    await functions[index](update, context, param)

async def callback_data_handler_setinfo(update, context, set_info):
    callback_data = normalise_option(update.callback_query.data)
    if set_info[0] not in context.user_data: context.user_data[set_info[0]] = {}
    context.user_data[set_info[0]][set_info[1]] = callback_data #Set user data for relevant option
    print("Set info: ", set_info[0], set_info[1])


async def onboard_finish(update: Update, context: CallbackContext) -> None:
    """Ask the user if they are sure they want to proceed with onboarding completion."""

    context.user_data["callbackquery"] = "onboard_finish"
    msg = "Are you sure you want to finish onboarding? (You can always change your profile later)"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Yes, proceed", callback_data='onboard_finish_yes')],
        [InlineKeyboardButton("No, go back to setup", callback_data='onboard_finish_no')]
    ])
    await update.callback_query.message.edit_text(msg, reply_markup=keyboard)

async def handle_onboard_finish_response(update: Update, context: CallbackContext) -> None:
    """Handle the user's response to the finish onboarding confirmation."""
    user = update.effective_user
    user_info = context.user_data.get("user_info", {})
    query = update.callback_query
    await query.answer()
    has_user_started_challenges = context.user_data.get("user_info", {}).get("Challenge Day")

    await update.callback_query.message.edit_text(
        f"-------- {user.first_name}'s Profile --------\n"
        f"{format_dict(user_info)}\n")
    
    if has_user_started_challenges: return # User already started challenges
    if query.data != 'onboard_finish_yes': return
    await start_challenges(update, context)
        
