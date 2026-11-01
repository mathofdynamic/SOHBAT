import re


def polish(text: str, strip_fillers: bool = True) -> str:
    if strip_fillers:
        text = re.sub(r"\b(?:um|uh)\b[, ]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    text = text[0].upper() + text[1:]
    if text[-1] not in '.!?…"':
        text += "."
    return text
