from telegram import Update
from telegram.ext import CallbackContext

from profile.mgmt_utils import get_inline_markup, normalise_option
from profile.nutrition_mgmt import nutrition_option_caller
from profile.lifestyle_mgmt import lifestyle_option_caller
from profile.profile_mgmt import profile_option_caller


#All mgmt
OPTIONS = ["Nutrition", "Lifestyle", "Profile", "Others"]

#Nutrition mgmt
NUTRITION_OPTIONS = ["Meals", "First/Last Meal", "Dietary Restrictions", "Home Cooked Meals", "Water Intake", "Finish"]
MEAL_OPTIONS = ["1", "2", "3", "4+"]
MEAL_TIMES_OPTIONS = ["8am, 8pm", "8am, 9pm", "8am, 10pm"]
HOME_COOKED_MEALS_OPTIONS = ["Daily", "Few times Weekly", "Rarely"]
WATER_OPTIONS = ["<1 litre", "1-2 litres", ">2 litres"]
DIETARY_RESTRICTIONS_OPTIONS = ["Yes", "No"]

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
    match cbq:
        case "onboarding": await callback_data_handler(
            update, context, OPTIONS, [nutrition_option_caller, lifestyle_option_caller, profile_option_caller], 
            ["setup_nutrition", "setup_lifestyle", "setup_profile"])

        case "Nutrition": await callback_data_handler(update, context, NUTRITION_OPTIONS, 
        [nutrition_option_caller], ["ask_meals", "ask_meal_times", "ask_dietary_restrictions","ask_home_cooked_meals", "ask_water_intake"])
            
        case "Lifestyle": await callback_data_handler(update, context, LIFESTYLE_OPTIONS, 
        [lifestyle_option_caller], ["ask_sleep", "ask_rested", "ask_stress", "ask_movement"])
        
        case "Profile": await callback_data_handler(update, context, [""], 
        [profile_option_caller], ["ask_name", "ask_age", "ask_height", "ask_weight"])
        
        case "nutrition_meals": await callback_data_handler(
            update, context, MEAL_OPTIONS, [nutrition_option_caller], ["setup_nutrition"], ["nutrition_info", "Meals"])

        case "nutrition_meal_times": await callback_data_handler(
            update, context, MEAL_TIMES_OPTIONS, [nutrition_option_caller], ["setup_nutrition"], ["nutrition_info", "First/Last Meal"])

        case "nutrition_home_cooked_meals": await callback_data_handler(
            update, context, HOME_COOKED_MEALS_OPTIONS, [nutrition_option_caller], ["setup_nutrition"], ["nutrition_info", "Home Cooked Meals"])

        case "nutrition_water_intake": await callback_data_handler(
            update, context, WATER_OPTIONS, [nutrition_option_caller], ["setup_nutrition"], ["nutrition_info", "Water Intake"])

        case "nutrition_dietary_restrictions": await callback_data_handler(
            update, context, DIETARY_RESTRICTIONS_OPTIONS, [nutrition_option_caller], ["setup_nutrition"], ["nutrition_info", "Dietary Restrictions"])

        case "lifestyle_sleep": await callback_data_handler(
            update, context, SLEEP_OPTIONS, [lifestyle_option_caller], ["setup_lifestyle"], ["lifestyle_info", "Sleep"])

        case "lifestyle_rested": await callback_data_handler(
            update, context, RESTED_OPTIONS, [lifestyle_option_caller], ["setup_lifestyle"], ["lifestyle_info", "Rested"])

        case "lifestyle_stress": await callback_data_handler(
            update, context, STRESS_OPTIONS, [lifestyle_option_caller], ["setup_lifestyle"], ["lifestyle_info", "Stress"])

        case "lifestyle_movement": await callback_data_handler(
            update, context, MOVEMENT_OPTIONS, [lifestyle_option_caller], ["setup_lifestyle"], ["lifestyle_info", "Movement"])

        case "nutrition_finish" | "lifestyle_finish": await callback_data_handler(
            update, context, ["Finish"], [setup])

        

async def callback_data_handler(update, context, options, functions, params=[], set_info=[]):
    callback_data = normalise_option(update.callback_query.data)
    if callback_data not in options: return
    if callback_data == "Finish": await setup(update, context); return
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

async def setup(update: Update, context: CallbackContext) -> None:
    context.user_data["callbackquery"] = "onboarding"
    msg = "Please set up your profile by selecting an option:"
    keyboard = get_inline_markup([OPTIONS])
    if update.message:
        setup_msg = await update.message.reply_text(msg, reply_markup=keyboard)
        context.user_data["setup_msg_id"] = setup_msg.message_id
    elif update.callback_query:
        await update.callback_query.message.edit_text(msg, reply_markup=keyboard)


