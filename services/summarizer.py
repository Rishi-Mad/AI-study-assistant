import re
from typing import List
from transformers import pipeline

_SUMM_MODEL = "t5-small"
_summarizer = None

def _lazy_load():
    global _summarizer
    if _summarizer is None:
        _summarizer = pipeline(
            "summarization",
            model=_SUMM_MODEL,
            tokenizer=_SUMM_MODEL,
            framework="pt",
            device=-1,  # CPU
        )

def _tidy(s: str) -> str:
    s = re.sub(r"\s+([.,!?;:])", r"\1", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def split_into_chunks(text: str, max_chars: int = 1200) -> List[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks, cur = [], ""
    for s in sentences:
        if len(cur) + len(s) + 1 > max_chars:
            if cur:
                chunks.append(cur.strip())
            cur = s
        else:
            cur = (cur + " " + s).strip() if cur else s
    if cur:
        chunks.append(cur.strip())
    return chunks

def summarize_t5(text: str, min_len: int = 40, max_len: int = 140) -> str:
    _lazy_load()
    text = (text or "").strip()
    if not text:
        return ""

    chunks = split_into_chunks(text, max_chars=1200)
    parts: List[str] = []
    for ch in chunks:
        out = _summarizer(ch, min_length=min_len, max_length=max_len, do_sample=False)[0]["summary_text"]
        parts.append(out)

    combined = " ".join(parts)
    if len(parts) > 1 and len(combined) > 1200:
        combined = _summarizer(combined, min_length=min_len, max_length=max_len, do_sample=False)[0]["summary_text"]
    return _tidy(combined)

