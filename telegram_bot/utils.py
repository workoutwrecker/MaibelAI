from datetime import datetime
import pytz

SINGAPORE_TZ = pytz.timezone("Asia/Singapore")

def escaped_string(text: str) -> str:
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '{', '}', '.', '!', "'"]
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

def format_dict(d: dict) -> str:
    return "\n".join(
        f"{key}: {', '.join(values) if isinstance(values, list) else values}" 
        for key, values in d.items()
    )

def get_current_time_in_singapore():
    singapore_tz = pytz.timezone("Asia/Singapore")
    return datetime.now(singapore_tz)

