import re
from typing import List

def sentences(text: str) -> List[str]:
    return re.split(r'(?<=[.!?])\s+', (text or "").strip())

def normalize_space(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())
