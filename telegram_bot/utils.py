from datetime import datetime
import pytz, re

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

LIMITATION_ID_MAP = { 
    "Low back pain": "Bo1",
    "Knee pain": "Bo2",
    "Migraines": "Bo3",
    "Wrist pain": "Bo4",
    "Can't sweat": "In1",
    "Low": "In2",
    "Medium": "In3",
    "Pregnancy": "Wo1",
    "Postpartum": "Wo2"
}

LIMITATION_CATEGORY_MAP = {
    "Bo": "Bodily Pain",
    "In": "Intensity Limit",
    "Wo": "Womens Issues"
}

def get_limitation_label_by_id(limitation_id: str) -> str:
    for label, id_ in LIMITATION_ID_MAP.items():
        if id_ == limitation_id:
            return label
    return None

def get_limitation_id_by_label(label: str) -> str:
    return LIMITATION_ID_MAP.get(label)

def get_limitation_category_by_id(limitation_id: str) -> str:
    category_key = re.split(r'\d+', limitation_id, maxsplit=1)[0] #Split at first digit
    return LIMITATION_CATEGORY_MAP.get(category_key)
