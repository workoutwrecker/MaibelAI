from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

def get_inline_markup(options: list) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(option, callback_data=option) for option in option_row] for option_row in options]
    )

def check_user_info(context: CallbackContext) -> list:
    user_info = context.user_data.setdefault("user_info", {})
    required_nutrition_fields = ["Meals", "First/Last Meal", "Dietary Restrictions", "Home Cooked Meals", "Water Intake"]
    required_profile_fields = ["Age", "Height", "Weight"]

    missing_nutrition_fields = [field for field in required_nutrition_fields if field not in user_info]
    missing_profile_fields = [field for field in required_profile_fields if field not in user_info]
    return missing_nutrition_fields, missing_profile_fields

def normalise_option(option: str) -> str:
    """Normalise an option string to a base form by removing ✅ or ❔."""
    return option.replace(" ✅", "").replace("❔", "").strip()