import re
from typing import List, Dict
from utils.text import sentences, normalize_space

_DEF_PATTERNS = [
    r"^\s*([A-Z][A-Za-z0-9\- ]{1,60})\s+is\s+(.*)$",
    r"^\s*([A-Z][A-Za-z0-9\- ]{1,60})\s+are\s+(.*)$",
    r"^\s*([A-Z][A-Za-z0-9\- ]{1,60})\s+refers to\s+(.*)$",
    r"^\s*([A-Z][A-Za-z0-9\- ]{1,60})\s+is defined as\s+(.*)$",
    r"^\s*([A-Z][A-Za-z0-9\- ]{1,60})\s*:\s*(.+)$",
]

def _clean_term(term: str) -> str:
    term = normalize_space(term)
    term = re.sub(r"[.:,;]+$", "", term)
    return term.strip()

def _clean_defn(defn: str) -> str:
    defn = normalize_space(defn)
    m = re.match(r"(.+?[.!?])(\s|$)", defn)
    return (m.group(1) if m else defn).strip()

def extract_flashcards(text: str, max_cards: int = 12) -> List[Dict[str, str]]:
    cards: List[Dict[str, str]] = []
    seen = set()
    for s in sentences(text):
        s_clean = normalize_space(s)
        for pat in _DEF_PATTERNS:
            m = re.match(pat, s_clean, flags=re.IGNORECASE)
            if not m: 
                continue
            term = _clean_term(m.group(1))
            ans  = _clean_defn(m.group(2))
            if len(term) < 2 or len(ans) < 5 or len(term.split()) > 8:
                continue
            key = term.lower()
            if key in seen: 
                break
            seen.add(key)
            cards.append({
                "term": term,
                "question": f"What is {term}?",
                "answer": ans
            })
            break
        if len(cards) >= max_cards:
            break
    return cards