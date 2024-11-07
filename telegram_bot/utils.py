def escaped_string(text: str) -> str:
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '{', '}', '.', '!', "'"]
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text