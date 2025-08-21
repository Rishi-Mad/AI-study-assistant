import re
from typing import List, Dict, Tuple
from collections import Counter
from utils.text import normalize_space

_STOP = {
    "a","an","and","the","or","but","if","then","so","of","to","in","on","for","with","at","by","from","as",
    "is","are","was","were","be","been","being","it","that","this","these","those","i","you","he","she","we",
    "they","them","his","her","their","our","your","my","me","can","could","should","would","may","might",
    "will","just","not","no","do","does","did","done","than","into","over","under","about","between","also"
}

WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9\-']+")

def _tokens(text: str) -> List[str]:
    return [t.lower() for t in WORD_RE.findall(text)]

def _is_good(tok: str) -> bool:
    return tok not in _STOP and len(tok) > 2 and not tok.isnumeric()

def extract_keywords(text: str, top_k: int = 10) -> List[Dict[str, float]]:
    text = normalize_space(text or "")
    if not text:
        return []

    toks = _tokens(text)
    good = [t for t in toks if _is_good(t)]

    uni = Counter(good)
    bi: Counter[Tuple[str,str]] = Counter()
    for i in range(len(good) - 1):
        a, b = good[i], good[i+1]
        if a != b:
            bi[(a,b)] += 1

    pos_weight = {}
    for idx, t in enumerate(good):
        if t not in pos_weight:
            pos_weight[t] = 1.0 + 0.2 * (1.0 - idx / max(1, len(good)-1))

    scores: Dict[str, float] = {}
    max_uni = max(uni.values()) if uni else 1
    for w, c in uni.items():
        scores[w] = (c / max_uni) * pos_weight.get(w, 1.0)

    for (a,b), c in bi.items():
        pair = f"{a} {b}"
        if uni[a] >= 1 and uni[b] >= 1 and c >= 1:
            scores[pair] = scores.get(a,0) * 0.6 + scores.get(b,0) * 0.6 + c * 0.4

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

    if ranked:
        m = ranked[0][1]
        ranked = [(k, v / m if m > 0 else 0.0) for k, v in ranked]


    return [{"keyword": k, "score": round(v, 3)} for k, v in ranked]
