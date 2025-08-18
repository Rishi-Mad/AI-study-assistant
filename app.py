from flask import Flask, request, jsonify
from flask_cors import CORS
import re
from typing import List
from transformers import pipeline

app = Flask(__name__)
CORS(app)  # allow requests from Vite

@app.get("/")
def home():
    return {"message": "AI Study Assistant backend is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

SUMM_MODEL = "t5-small"
try:
    summarizer = pipeline(
        "summarization",
        model=SUMM_MODEL,
        tokenizer=SUMM_MODEL,
        framework="pt",   # use PyTorch
        device=-1         # -1 = CPU
    )
except Exception as e:
    summarizer = None
    print("Failed to load summarizer:", e)

def split_into_chunks(text: str, max_chars: int = 1200) -> List[str]:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks, cur = [], ""
    for s in sentences:
        # start new chunk if adding this sentence would exceed size
        if len(cur) + len(s) + 1 > max_chars:
            if cur:
                chunks.append(cur.strip())
            cur = s
        else:
            cur = (cur + " " + s).strip() if cur else s
    if cur:
        chunks.append(cur.strip())
    return chunks

def ml_summarize(text: str, min_len: int = 40, max_len: int = 140) -> str:
    if not summarizer:
        raise RuntimeError("Summarizer model not loaded")
    text = text.strip()
    if not text:
        return ""
    
    # chunk long text, summarize each, then (optionally) summarize the summaries
    chunks = split_into_chunks(text, max_chars=1200)
    partials = []
    for ch in chunks:
        out = summarizer(
            ch,
            min_length=min_len,
            max_length=max_len,
            do_sample=False
        )[0]["summary_text"]
        partials.append(out)

    combined = " ".join(partials)

    # If many chunks, do a second pass to compress combined text
    if len(partials) > 1 and len(combined) > 1200:
        combined = summarizer(
            combined,
            min_length=min_len,
            max_length=max_len,
            do_sample=False
        )[0]["summary_text"]

    return combined

@app.post("/summarize")
def summarize():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    min_len = int(data.get("min_length", 40))
    max_len = int(data.get("max_length", 140))

    if not text:
        return jsonify({"error": "Missing 'text'"}), 400
    if max_len <= min_len:
        return jsonify({"error": "max_length must be > min_length"}), 400

    try:
        summary = ml_summarize(text, min_len=min_len, max_len=max_len)
        return jsonify({
            "model": SUMM_MODEL,
            "summary": summary
        })
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        # log and return a clean error to client
        print("Summarization error:", e)
        return jsonify({"error": "Summarization failed"}), 500

if __name__ == "__main__":
    app.run(debug=True)
