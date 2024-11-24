from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

from utils import format_dict

age_options = ["18-24", "25-34", "35-44", "45+"]
gender_options = ["Female", "Male", "Other"]
workouts_options = ["1-2", "3-4", "5+"]
goal_options = ["Lose weight", "Get stronger"]
goal_options_2 = ["Build muscle", "Mix"]
weakness_options = ["Bodily Pain", "Intensity Limit"]
weakness_options_2 = ["Womens issues", "Go Back"]
bodily_pain_options = ["Low back pain", "Knee pain"]
bodily_pain_options_2 = ["Migraines", "Wrist pain"]
intensity_options = ["Can't sweat", "Low"]
intensity_options_2 = ["Medium"]
pregnancy_options = ["Pregnancy", "Postpartum"]
go_back_option = ["Go Back"]

def get_inline_markup(options: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(option, callback_data=option) for option in option_row] for option_row in options]
    )

def check_user_info(context: CallbackContext) -> list:
    user_info = context.user_data.setdefault("user_info", {})
    required_fields = ['Age', 'Gender', 'Workouts', 'Goal']
    missing_fields = [field for field in required_fields if field not in user_info]
    
    return missing_fields

async def update_user_profile(update: Update, context: CallbackContext) -> None:
    # Data from chosen button
    callback_data = update.callback_query.data
    user_info = context.user_data.setdefault("user_info", {})
    user_limitations = context.user_data.setdefault("user_limitations", {})
    print(f"callback_data: {callback_data}")
    setup_context = context.user_data["setup"]
    match setup_context:
        case "age":
            if callback_data not in age_options:
                return
            user_info["Age"] = callback_data
            context.user_data["setup"] = "init"
            await(setup(update, context))
        case "gender":
            if callback_data not in gender_options:
                return
            user_info["Gender"] = callback_data
            context.user_data["setup"] = "init"
            await(setup(update, context))
        case "workouts":
            if callback_data not in workouts_options:
                return
            user_info["Workouts"] = callback_data
            context.user_data["setup"] = "init"
            await(setup(update, context))
        case "goal":
            if callback_data not in goal_options + goal_options_2:
                return
            user_info["Goal"] = callback_data
            context.user_data["setup"] = "init"
            await(setup(update, context))
        case "limitations":
            if callback_data not in weakness_options + weakness_options_2:
                return
            match callback_data:
                case "Bodily Pain": await ask_bodily_pain(update, context)
                case "Intensity Limit": await ask_intensity_limit(update, context)
                case "Womens issues": await ask_womens_issues(update, context)
                case "Remove": await ask_remove_limtitations(update, context)
                case "Go Back":
                    context.user_data["setup"] = "init"
                    await(setup(update, context))
        case "Bodily Pain" | "Intensity Limit" | "Womens Issues":
            if callback_data in go_back_option:
                context.user_data["setup"] = "limitations"
                await ask_limitations(update, context)
            else:
                if callback_data not in bodily_pain_options + bodily_pain_options_2 \
                + intensity_options + intensity_options_2 + pregnancy_options:
                    return
                if callback_data not in user_limitations.setdefault(setup_context, []):
                    user_limitations[setup_context].append(callback_data)
                context.user_data["setup"] = "init"
                await(setup(update, context))
        case "remove_limitations":
            if callback_data in go_back_option:
                context.user_data["setup"] = "limitations"
                await ask_limitations(update, context)
            else:
                category, value = callback_data.split(": ", 1)
                user_limitations[category].remove(value)
                if len(user_limitations.keys()) > 0:
                    await ask_remove_limtitations(update, context)
            
        case "init":
            match callback_data:
                case "Age": await ask_age(update, context)
                case "Gender": await ask_gender(update, context)
                case "Workouts": await ask_workouts(update, context)
                case "Goal": await ask_goal(update, context)
                case "Limitations": await ask_limitations(update, context)
                case "Finish": await finish_setup(update, context)
                case _: print("else init")
        case _: return
        

async def setup(update: Update, context) -> None:
    """Display the main setup menu"""
    msg = "Please set up your profile by selecting an option:"
    keyboard = get_inline_markup([["Age", "Gender", "Workouts",], ["Goal", "Limitations", "Finish"]])
    if update.message: 
        setup_msg = await update.message.reply_text(msg, reply_markup=keyboard)
        bot_message_id = setup_msg.message_id
        context.user_data["setup_msg_id"] = bot_message_id
          
    elif update.callback_query: await update.callback_query.message.edit_text(msg, reply_markup=keyboard)

async def ask_age(update: Update, context: CallbackContext) -> None:
    context.user_data["setup"] = "age"
    keyboard = get_inline_markup([age_options])
    await update.callback_query.message.edit_text("Please select your age range:", reply_markup=keyboard)
    
async def ask_gender(update: Update, context: CallbackContext) -> None:
    context.user_data["setup"] = "gender"
    keyboard = get_inline_markup([gender_options])
    await update.callback_query.message.edit_text("Please select your gender:", reply_markup=keyboard)

async def ask_workouts(update: Update, context: CallbackContext) -> None:
    context.user_data["setup"] = "workouts"
    keyboard = get_inline_markup([workouts_options])
    await update.callback_query.message.edit_text("How many workouts do you do per week?", reply_markup=keyboard)

async def ask_goal(update: Update, context: CallbackContext) -> None:
    context.user_data["setup"] = "goal"
    keyboard = get_inline_markup([goal_options, goal_options_2])
    await update.callback_query.message.edit_text("What is your fitness goal?", reply_markup=keyboard)

async def ask_limitations(update: Update, context: CallbackContext) -> None:
    context.user_data["setup"] = "limitations"
    
    user_limitations = context.user_data.get("user_limitations", {})
    if len(user_limitations.keys()) > 0:
        weakness_options.append("Remove")
    keyboard = get_inline_markup([
        weakness_options,
        weakness_options_2
    ])
    await update.callback_query.message.edit_text(
        "Select or type any physical limitations you have!",
        reply_markup=keyboard
    )

async def ask_bodily_pain(update: Update, context: CallbackContext) -> None:
    context.user_data["setup"] = "Bodily Pain"
    keyboard = get_inline_markup([
        bodily_pain_options, bodily_pain_options_2, go_back_option
    ])
    await update.callback_query.message.edit_text(
        "Please select specific bodily pain:",
        reply_markup=keyboard
    )

async def ask_intensity_limit(update: Update, context: CallbackContext) -> None:
    context.user_data["setup"] = "Intensity Limit"
    keyboard = get_inline_markup([
        intensity_options, intensity_options_2, go_back_option
    ])
    await update.callback_query.message.edit_text(
        "Please select your intensity limitation:",
        reply_markup=keyboard
    )

async def ask_womens_issues(update: Update, context: CallbackContext) -> None:
    context.user_data["setup"] = "Womens Issues"
    keyboard = get_inline_markup([
        pregnancy_options, go_back_option
    ])
    await update.callback_query.message.edit_text(
        "Please select a specific women's option:",
        reply_markup=keyboard
    )

async def ask_remove_limtitations(update: Update, context: CallbackContext) -> None:
    context.user_data["setup"] = "remove_limitations"
    user_limitations = context.user_data.get("user_limitations", {})
    limitations_list = [
        f"{category}: {value}"
        for category, values in user_limitations.items()
        for value in values
    ]

    # Group limitations into rows of 2–3 items
    rows = [limitations_list[i:i + 2] for i in range(0, len(limitations_list), 2)]
    rows.append(["Go Back"])

    # Create inline keyboard markup
    keyboard = get_inline_markup(rows)

    # Send or edit the message with the dynamically created keyboard
    await update.callback_query.message.edit_text(
        "Please select a limitation you'd like to remove:",
        reply_markup=keyboard
    )
async def finish_setup(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    user_info = context.user_data.get("user_info", {})
    user_limitations = context.user_data.get("user_limitations", {})
    context.user_data["setup"] = "finish"
    await update.callback_query.message.edit_text(
        f"-------- {user.first_name}'s Profile --------\n"
        f"{format_dict(user_info)}\n"
        f"\n-------- {user.first_name}'s Limitations --------\n"
        f"{format_dict(user_limitations)}"
    )

