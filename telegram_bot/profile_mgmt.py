from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

user_info = {}

def get_inline_markup(options: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(option, callback_data=option) for option in option_row] for option_row in options]
    )

def check_user_info() -> list:
    required_fields = ['Age', 'Gender', 'Workouts', 'Goal']
    missing_fields = [field for field in required_fields if field not in user_info]
    
    return missing_fields

async def update_user_profile(update: Update, context: CallbackContext) -> None:
    # Data from chosen button
    callback_data = update.callback_query.data
    print("callback: ", callback_data)

    setup_context = context.user_data["setup"]
    print("Setup Context: ", setup_context)
    match setup_context:
        case "age":
            user_info["Age"] = callback_data
            context.user_data["setup"] = "init"
            await(setup(update))
        case "gender":
            user_info["Gender"] = callback_data
            context.user_data["setup"] = "init"
            await(setup(update))
        case "workouts":
            user_info["Workouts"] = callback_data
            context.user_data["setup"] = "init"
            await(setup(update))
        case "goal":
            user_info["Goal"] = callback_data
            context.user_data["setup"] = "init"
            await(setup(update))
        case "init":
            match callback_data:
                case "Age": await ask_age(update, context)
                case "Gender": await ask_gender(update, context)
                case "Workouts": await ask_workouts(update, context)
                case "Goal": await ask_goal(update, context)
                case "Finish": await finish_setup(update, context)
                case _: print(f"Init Else Caught. Callback: {callback_data}, SetupContext: {setup_context}")
        case _: return
        

async def setup(update: Update) -> None:
    """Display the main setup menu"""
    msg = "Please set up your profile by selecting an option:"
    keyboard = get_inline_markup([["Age", "Gender", "Workouts",], ["Goal", "Finish"]])
    if update.message: await update.message.reply_text(msg, reply_markup=keyboard)
    elif update.callback_query: await update.callback_query.message.edit_text(msg, reply_markup=keyboard)

async def ask_age(update: Update, context: CallbackContext) -> None:
    context.user_data["setup"] = "age"
    keyboard = get_inline_markup([["18-24", "25-34", "35-44", "45+"]])
    await update.callback_query.message.edit_text("Please select your age range:", reply_markup=keyboard)
    
async def ask_gender(update: Update, context: CallbackContext) -> None:
    context.user_data["setup"] = "gender"
    keyboard = get_inline_markup([["Female", "Male", "Other"]])
    await update.callback_query.message.edit_text("Please select your gender:", reply_markup=keyboard)

async def ask_workouts(update: Update, context: CallbackContext) -> None:
    context.user_data["setup"] = "workouts"
    keyboard = get_inline_markup([["1-2", "3-4", "5+"]])
    await update.callback_query.message.edit_text("How many workouts do you do per week?", reply_markup=keyboard)

async def ask_goal(update: Update, context: CallbackContext) -> None:
    context.user_data["setup"] = "goal"
    keyboard = get_inline_markup([["Lose weight", "Get stronger"], ["Build muscle", "Mix"]])
    await update.callback_query.message.edit_text("What is your fitness goal?", reply_markup=keyboard)

async def finish_setup(update: Update, context: CallbackContext) -> None:
    context.user_data["setup"] = "finish"
    await update.callback_query.message.edit_text(f"Setup complete! Here is your profile:\n{user_info}")

