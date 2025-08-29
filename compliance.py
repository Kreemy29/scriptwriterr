import re

BANNED = {r"\b(naked|explicit|porn|onlyfans\.com)\b"}
CAUTION = {r"\b(hot|naughty|spicy|thirsty)\b"}

def compliance_level(text: str):
    low = text.lower()
    for pat in BANNED:
        if re.search(pat, low):
            return "fail", ["banned phrase"]
    reasons = []
    for pat in CAUTION:
        if re.search(pat, low):
            reasons.append("caution phrase")
    return ("warn" if reasons else "pass"), reasons

def score_script(blob: str):
    return compliance_level(blob)

def blob_from(script: dict) -> str:
    parts = [
        script.get("title",""), script.get("hook",""),
        " ".join(script.get("beats",[])),
        script.get("voiceover",""), script.get("caption",""), script.get("cta","")
    ]
    return " ".join(parts)
