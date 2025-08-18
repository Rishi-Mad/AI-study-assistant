from transformers import pipeline
from typing import Optional
import re

_model_name = "t5-small"
_pipe: Optional[any] = None

def _lazy():
    global _pipe
    if _pipe is None:
        _pipe = pipeline(
            "text2text-generation",
            model=_model_name,
            tokenizer=_model_name,
            framework="pt",
            device=-1
        )

def _tidy(s: str) -> str:
    s = re.sub(r"\s+([.,!?;:])", r"\1", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def paraphrase(text: str, max_len: int = 128, num_beams: int = 4) -> str:
    _lazy()
    text = (text or "").strip()
    if not text:
        return ""
    prompt = f"paraphrase: {text}"
    out = _pipe(
        prompt,
        max_length=max_len,
        num_beams=num_beams,
        do_sample=False
    )[0]["generated_text"]
    return _tidy(out)
