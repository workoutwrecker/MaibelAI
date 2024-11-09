from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

user_prefs = {}

# Helper function to create reply markup for the profile stages
def get_reply_markup(options: list) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[KeyboardButton(option) for option in option_row] for option_row in options],
        one_time_keyboard=True,
        resize_keyboard=True
    )

# Update user_prefs with collected profile information
async def update_user_profile(update: Update, context) -> None:
    global user_prefs

    if "profile_stage" not in context.user_data:
        context.user_data["profile_stage"] = "ask_age"
        await ask_age(update, context)
    else: 
        profile_stage = context.user_data.get("profile_stage")
        match profile_stage:
            case "ask_age":
                await ask_gender(update, context)
            case "ask_gender":
                await ask_workouts_per_week(update, context)
            case "ask_workouts":
                await ask_goal(update, context)
            case "ask_goal":
                await profile_complete(update, context)
            case _:
                await handle_error(update)

# Ask for age
async def ask_age(update: Update, context) -> None:
    context.user_data["profile_stage"] = "ask_age"
    await update.message.reply_text(
        "To start, please enter your age.",
        reply_markup=get_reply_markup([["18-24", "25-34", "35-44", "45+"]])
    )

# Ask for gender
async def ask_gender(update: Update, context) -> None:
    user_prefs["age"] = update.message.text
    context.user_data["profile_stage"] = "ask_gender"
    await update.message.reply_text(
        "Please select your gender.",
        reply_markup=get_reply_markup([["Female", "Male", "Other"]])
    )

# Ask for workouts per week
async def ask_workouts_per_week(update: Update, context) -> None:
    user_prefs["gender"] = update.message.text
    context.user_data["profile_stage"] = "ask_workouts"
    await update.message.reply_text(
        "How many workouts do you do per week on average?",
        reply_markup=get_reply_markup([["1-2", "3-4", "5+"]])
    )

# Ask for fitness goal
async def ask_goal(update: Update, context) -> None:
    user_prefs["workouts_per_week"] = update.message.text
    context.user_data["profile_stage"] = "ask_goal"
    await update.message.reply_text(
        "What is your fitness goal? Choose one:",
        reply_markup=get_reply_markup([["Lose weight", "Get stronger"], ["Build muscle", "Mix"]])
    )

# Profile is complete
async def profile_complete(update: Update, context) -> None:
    user_prefs["goal"] = update.message.text
    context.user_data["profile_stage"] = "profile_complete"
    await update.message.reply_text(
        "Thank you🙏🏻 Your profile is complete💯. Let's Go!😄",
        reply_markup=ReplyKeyboardRemove()
    )

# Handle any unexpected errors
async def handle_error(update: Update) -> None:
    await update.message.reply_text(
        "I think something went wrong. See you later👋. Error pr-0",
        reply_markup=ReplyKeyboardRemove()
    )
