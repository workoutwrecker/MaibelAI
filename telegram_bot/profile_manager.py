from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

user_prefs = {}

# Update user_prefs with collected profile information
async def update_user_profile(update: Update, context) -> None:
    global user_prefs
    user_input = update.message.text

    if "profile_stage" not in context.user_data:
        context.user_data["profile_stage"] = "ask_age"
        await update.message.reply_text(
        "To start, please enter your age.",
        reply_markup=ReplyKeyboardMarkup(
            [[KeyboardButton("18-24"), KeyboardButton("25-34"), KeyboardButton("35-44"), KeyboardButton("45+")]],
            one_time_keyboard=True,
            resize_keyboard=True
        )
    )
    elif context.user_data['profile_stage'] == "ask_age":
        user_prefs["age"] = user_input
        context.user_data["profile_stage"] = "ask_gender"
        await update.message.reply_text(
            "Please select your gender.",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("Female"), KeyboardButton("Male"), KeyboardButton("Other")]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
    elif context.user_data['profile_stage'] == "ask_gender":
        user_prefs["gender"] = user_input
        context.user_data["profile_stage"] = "ask_workouts_per_week"
        await update.message.reply_text(
            "How many workouts do you do per week?",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("1-2"), KeyboardButton("3-4"), KeyboardButton("5+")]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
    elif context.user_data['profile_stage'] == "ask_workouts_per_week":
        user_prefs["workouts_per_week"] = user_input
        context.user_data["profile_stage"] = "ask_goal"
        await update.message.reply_text(
            "What is your fitness goal? Choose one:",
            reply_markup=ReplyKeyboardMarkup(
                [[KeyboardButton("Lose weight"), KeyboardButton("Get stronger")],
                 [KeyboardButton("Build muscle"), KeyboardButton("Mix")]],
                one_time_keyboard=True,
                resize_keyboard=True
            )
        )
    elif context.user_data['profile_stage'] == "ask_goal":
        user_prefs["goal"] = user_input
        context.user_data["profile_stage"] = "profile_complete"
        await update.message.reply_text(
            "Thank you! Your profile is complete. You can now ask me anything related to fitness!",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await update.message.reply_text(
            "I think something went wrong. Error PRMA(0)",
            reply_markup=ReplyKeyboardRemove()
        )

    