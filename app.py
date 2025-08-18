from flask import Flask, request, jsonify
from flask_cors import CORS
import re
from collections import Counter

app = Flask(__name__)
CORS(app)  # allow requests from Vite

@app.get("/")
def home():
    return {"message": "AI Study Assistant backend is running"}

@app.get("/health")
def health():
    return {"status": "ok"}


def simple_summarize(text: str, ratio: float = 0.25, max_sentences: int | None = None) -> str:
    """
    Extractive summary:
      1) split into sentences
      2) score sentences by word frequency (stopwords down-weighted)
      3) return top N sentences in original order
    """
    if not text or not text.strip():
        return ""

    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    if len(sentences) <= 2:
        return text 

    words = re.findall(r"[A-Za-z']+", text.lower())
    stop = {
        "the","a","an","and","or","but","if","then","when","so","of","to","in","on","for","with","at","by",
        "from","as","is","are","was","were","be","been","being","it","that","this","these","those","i","you",
        "he","she","we","they","them","his","her","their","our","your","my","me"
    }
    freq = Counter(w for w in words if w not in stop)
    if not freq:
        return sentences[0]

    def score(sent: str) -> int:
        tokens = re.findall(r"[A-Za-z']+", sent.lower())
        return sum(freq.get(t, 0) for t in tokens)

    scored = [(idx, s, score(s)) for idx, s in enumerate(sentences)]

    n = max(1, int(len(sentences) * ratio)) if max_sentences is None else max_sentences
    n = min(n, len(sentences))

    top = sorted(sorted(scored, key=lambda x: x[2], reverse=True)[:n], key=lambda x: x[0])
    return " ".join(s for _, s, _ in top)

@app.post("/summarize")
def summarize():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    ratio = data.get("ratio", 0.25)

    try:
        ratio = float(ratio)
    except Exception:
        return jsonify({"error": "ratio must be a number"}), 400
    if not text:
        return jsonify({"error": "Missing 'text'"}), 400
    if not (0.05 <= ratio <= 0.9):
        return jsonify({"error": "ratio must be between 0.05 and 0.9"}), 400

    summary = simple_summarize(text, ratio=ratio)
    return jsonify({"summary": summary})

if __name__ == "__main__":
    app.run(debug=True)
