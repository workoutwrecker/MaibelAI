from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

from utils import format_dict, get_limitation_id_by_label, get_limitation_label_by_id

AGE_OPTIONS = ["18-24", "25-34", "35-44", "45+"]
GENDER_OPTIONS = ["Female", "Male", "Other"]
WORKOUTS_OPTIONS = ["1-2", "3-4", "5+"]
GOAL_OPTIONS = ["Lose weight", "Get stronger"]
GOAL_OPTIONS_2 = ["Build muscle", "Mix"]
WEAKNESS_OPTIONS = ["Bodily Pain", "Intensity Limit"]
WEAKNESS_OPTIONS_2 = ["Womens issues", "Go Back"]
BODILY_PAIN_OPTIONS = ["Low back pain", "Knee pain"]
BODILY_PAIN_OPTIONS_2 = ["Migraines", "Wrist pain"]
INTENSITY_OPTIONS = ["Can't sweat", "Low"]
INTENSITY_OPTIONS_2 = ["Medium"]
WOMENS_ISSUES_OPTIONS = ["Pregnancy", "Postpartum"]
GO_BACK_OPTION = ["Go Back"]
REMOVE_OPTION = ["Remove"]


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
    user_id = update.effective_user.id
    user_info = context.user_data.setdefault("user_info", {})
    user_limitations = context.user_data.setdefault("user_limitations", {})
    setup_context = context.user_data["setup"]
    async def update_user_info(callback_data: str, category: str, options: list) -> None:
        if callback_data in options:
            user_info[category] = callback_data
            context.user_data["setup"] = "init"
            await(setup(update, context))
    match setup_context:
        case "age": await update_user_info(callback_data, "Age", AGE_OPTIONS)
        case "gender": await update_user_info(callback_data, "Gender", GENDER_OPTIONS)
        case "workouts": await update_user_info(callback_data, "Workouts", WORKOUTS_OPTIONS)
        case "goal": await update_user_info(callback_data, "Goal", GOAL_OPTIONS + GOAL_OPTIONS_2)
        case "limitations":
            if callback_data in WEAKNESS_OPTIONS + WEAKNESS_OPTIONS_2 + REMOVE_OPTION:
                match callback_data:
                    case "Bodily Pain": await ask_bodily_pain(update, context)
                    case "Intensity Limit": await ask_intensity_limit(update, context)
                    case "Womens issues": await ask_womens_issues(update, context)
                    case "Remove": await ask_remove_limtitations(update, context)
                    case "Go Back":
                        context.user_data["setup"] = "init"
                        await(setup(update, context))
        case "Bodily Pain" | "Intensity Limit" | "Womens Issues":
            if callback_data in GO_BACK_OPTION:
                context.user_data["setup"] = "limitations"
                await ask_limitations(update, context)
            else:
                if callback_data not in BODILY_PAIN_OPTIONS + BODILY_PAIN_OPTIONS_2 \
                + INTENSITY_OPTIONS + INTENSITY_OPTIONS_2 + WOMENS_ISSUES_OPTIONS: return
                if callback_data not in user_limitations.setdefault(setup_context, []):
                    user_limitations[setup_context].append(get_limitation_id_by_label(callback_data))
                context.user_data["setup"] = "init"
                await(setup(update, context))
        case "remove_limitations":
            if callback_data in GO_BACK_OPTION:
                context.user_data["setup"] = "limitations"
                await ask_limitations(update, context)
            else:
                category, callback_value = callback_data.split(": ", 1)
                user_limitations[category].remove(get_limitation_id_by_label(callback_value))
                if user_limitations:
                    await ask_remove_limtitations(update, context)
            
        case "init":
            match callback_data:
                case "Age❔" | "Age✅": await ask_age(update, context)
                case "Gender❔" | "Gender✅": await ask_gender(update, context)
                case "Workouts❔" | "Workouts✅": await ask_workouts(update, context)
                case "Goal❔" | "Goal✅": await ask_goal(update, context)
                case "Limitations": await ask_limitations(update, context)
                case "Finish": await finish_setup(update, context)
                case _: print("else init")
        case _: return
        

async def setup(update: Update, context) -> None:
    """Display the main setup menu"""
    msg = "Please set up your profile by selecting an option:"
    user_info = context.user_data.get("user_info", {})
    options = [
        ("Age ✅" if "Age" in user_info else "Age❔"),
        ("Gender ✅" if "Gender" in user_info else "Gender❔"),
        ("Workouts ✅" if "Workouts" in user_info else "Workouts❔"),
        ("Goal ✅" if "Goal" in user_info else "Goal❔"),
    ]
    keyboard = get_inline_markup([[options[0], options[1], options[2],], [options[3], "Limitations", "Finish"]])
    if update.message: 
        setup_msg = await update.message.reply_text(msg, reply_markup=keyboard)
        bot_message_id = setup_msg.message_id
        context.user_data["setup_msg_id"] = bot_message_id
          
    elif update.callback_query: await update.callback_query.message.edit_text(msg, reply_markup=keyboard)

async def ask_age(update: Update, context: CallbackContext) -> None:
    context.user_data["setup"] = "age"
    keyboard = get_inline_markup([AGE_OPTIONS])
    await update.callback_query.message.edit_text("Please select your age range:", reply_markup=keyboard)
    
async def ask_gender(update: Update, context: CallbackContext) -> None:
    context.user_data["setup"] = "gender"
    keyboard = get_inline_markup([GENDER_OPTIONS])
    await update.callback_query.message.edit_text("Please select your gender:", reply_markup=keyboard)

async def ask_workouts(update: Update, context: CallbackContext) -> None:
    context.user_data["setup"] = "workouts"
    keyboard = get_inline_markup([WORKOUTS_OPTIONS])
    await update.callback_query.message.edit_text("How many workouts do you do per week?", reply_markup=keyboard)

async def ask_goal(update: Update, context: CallbackContext) -> None:
    context.user_data["setup"] = "goal"
    keyboard = get_inline_markup([GOAL_OPTIONS, GOAL_OPTIONS_2])
    await update.callback_query.message.edit_text("What is your fitness goal?", reply_markup=keyboard)

async def ask_limitations(update: Update, context: CallbackContext) -> None:
    context.user_data["setup"] = "limitations"
    
    user_limitations = context.user_data.get("user_limitations", {})
    keyboard = get_inline_markup([
        WEAKNESS_OPTIONS + REMOVE_OPTION, 
        WEAKNESS_OPTIONS_2
    ])
    await update.callback_query.message.edit_text(
        "Select or type any physical limitations you have!",
        reply_markup=keyboard
    )

async def ask_bodily_pain(update: Update, context: CallbackContext) -> None:
    context.user_data["setup"] = "Bodily Pain"
    keyboard = get_inline_markup([
        BODILY_PAIN_OPTIONS, BODILY_PAIN_OPTIONS_2, GO_BACK_OPTION
    ])
    await update.callback_query.message.edit_text(
        "Please select specific bodily pain:",
        reply_markup=keyboard
    )

async def ask_intensity_limit(update: Update, context: CallbackContext) -> None:
    context.user_data["setup"] = "Intensity Limit"
    keyboard = get_inline_markup([
        INTENSITY_OPTIONS, INTENSITY_OPTIONS_2, GO_BACK_OPTION
    ])
    await update.callback_query.message.edit_text(
        "Please select your intensity limitation:",
        reply_markup=keyboard
    )

async def ask_womens_issues(update: Update, context: CallbackContext) -> None:
    context.user_data["setup"] = "Womens Issues"
    keyboard = get_inline_markup([
        WOMENS_ISSUES_OPTIONS, GO_BACK_OPTION
    ])
    await update.callback_query.message.edit_text(
        "Please select a specific women's option:",
        reply_markup=keyboard
    )

async def ask_remove_limtitations(update: Update, context: CallbackContext) -> None:
    context.user_data["setup"] = "remove_limitations"
    user_limitations = context.user_data.get("user_limitations", {})
    print(user_limitations)
    limitations_list = [
        f"{category}: {get_limitation_label_by_id(value)}"
        for category, values in user_limitations.items()
        for value in values
    ]

    # Group limitations into rows of 2–3 items
    rows = [limitations_list[i:i + 2] for i in range(0, len(limitations_list), 2)]
    rows.append(GO_BACK_OPTION)

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

