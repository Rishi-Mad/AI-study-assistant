from flask import Flask, request, jsonify
from flask_cors import CORS
from services.summarizer import summarize_t5
from services.flashcards import extract_flashcards
from services.quiz import build_quiz

app = Flask(__name__)
CORS(app)

@app.get("/")
def home():
    return {"message": "AI Study Assistant backend is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

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
        summary = summarize_t5(text, min_len=min_len, max_len=max_len)
        return jsonify({"model": "t5-small", "summary": summary})
    except Exception as e:
        print("Summarization error:", e)
        return jsonify({"error": "Summarization failed"}), 500

@app.post("/flashcards")
def flashcards():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    max_cards = int(data.get("max_cards", 10))

    if not text:
        return jsonify({"error": "Missing 'text'"}), 400
    if not (1 <= max_cards <= 50):
        return jsonify({"error": "max_cards must be between 1 and 50"}), 400

    cards = extract_flashcards(text, max_cards=max_cards)
    return jsonify({"count": len(cards), "cards": cards})

@app.post("/quiz")
def quiz():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    max_qs = int(data.get("max_qs", 5))

    if not text:
        return jsonify({"error": "Missing 'text'"}), 400
    if not (1 <= max_qs <= 20):
        return jsonify({"error": "max_qs must be between 1 and 20"}), 400

    questions = build_quiz(text, max_qs=max_qs)
    return jsonify({"count": len(questions), "quiz": questions})


if __name__ == "__main__":
    app.run(debug=True)
