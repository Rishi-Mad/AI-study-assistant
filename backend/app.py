from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import sqlite3
import uuid

from services.summarizer import summarize_t5
from services.flashcards import extract_flashcards
from services.quiz import build_quiz
from services.keywords import extract_keywords
from services.paraphrase import paraphrase
from services.performance_tracker import PerformanceTracker
from services.adaptive_learning import AdaptiveLearningEngine
from services.visual_qa import VisualQAService

app = Flask(__name__)
CORS(app)

# Initialize services
performance_tracker = PerformanceTracker()
adaptive_engine = AdaptiveLearningEngine()
visual_qa_service = VisualQAService()

# Database initialization
def init_db():
    """Initialize SQLite database for user sessions and performance tracking"""
    conn = sqlite3.connect('study_assistant.db')
    cursor = conn.cursor()
    
    # User sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            session_id TEXT PRIMARY KEY,
            created_at TIMESTAMP,
            last_activity TIMESTAMP,
            user_preferences TEXT
        )
    ''')
    
    # Study activities table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS study_activities (
            activity_id TEXT PRIMARY KEY,
            session_id TEXT,
            activity_type TEXT,
            content_hash TEXT,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            performance_data TEXT,
            FOREIGN KEY (session_id) REFERENCES user_sessions (session_id)
        )
    ''')
    
    # Flashcard performance table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flashcard_performance (
            performance_id TEXT PRIMARY KEY,
            session_id TEXT,
            term TEXT,
            difficulty_level INTEGER,
            attempts INTEGER,
            correct_answers INTEGER,
            last_reviewed TIMESTAMP,
            next_review TIMESTAMP,
            retention_score REAL,
            FOREIGN KEY (session_id) REFERENCES user_sessions (session_id)
        )
    ''')
    
    # Quiz performance table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quiz_performance (
            performance_id TEXT PRIMARY KEY,
            session_id TEXT,
            question_text TEXT,
            correct_answer TEXT,
            user_answer TEXT,
            is_correct BOOLEAN,
            response_time REAL,
            difficulty_level INTEGER,
            timestamp TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES user_sessions (session_id)
        )
    ''')
    
    conn.commit()
    conn.close()

@app.before_first_request
def startup():
    init_db()

@app.get("/")
def home():
    return {"message": "AI Study Assistant backend is running", "version": "2.0"}

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.post("/session/create")
def create_session():
    """Create a new user session for tracking"""
    session_id = str(uuid.uuid4())
    timestamp = datetime.now()
    
    conn = sqlite3.connect('study_assistant.db')
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO user_sessions (session_id, created_at, last_activity, user_preferences) VALUES (?, ?, ?, ?)',
        (session_id, timestamp, timestamp, '{}')
    )
    conn.commit()
    conn.close()
    
    return jsonify({
        "session_id": session_id,
        "created_at": timestamp.isoformat()
    })

@app.post("/summarize")
def summarize():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    min_len = int(data.get("min_length", 40))
    max_len = int(data.get("max_length", 140))
    session_id = data.get("session_id")

    if not text:
        return jsonify({"error": "Missing 'text'"}), 400
    if max_len <= min_len:
        return jsonify({"error": "max_length must be > min_length"}), 400

    try:
        start_time = datetime.now()
        summary = summarize_t5(text, min_len=min_len, max_len=max_len)
        end_time = datetime.now()
        
        # Track activity if session provided
        if session_id:
            activity_data = {
                "input_length": len(text),
                "output_length": len(summary),
                "processing_time": (end_time - start_time).total_seconds()
            }
            performance_tracker.log_activity(
                session_id, "summarization", text, start_time, end_time, activity_data
            )
        
        return jsonify({
            "model": "t5-small",
            "summary": summary,
            "metadata": {
                "input_length": len(text),
                "summary_length": len(summary),
                "compression_ratio": round(len(summary) / len(text), 2)
            }
        })
    except Exception as e:
        print("Summarization error:", e)
        return jsonify({"error": "Summarization failed"}), 500

@app.post("/flashcards")
def flashcards():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    max_cards = int(data.get("max_cards", 10))
    session_id = data.get("session_id")
    difficulty_level = data.get("difficulty_level", "medium")

    if not text:
        return jsonify({"error": "Missing 'text'"}), 400
    if not (1 <= max_cards <= 50):
        return jsonify({"error": "max_cards must be between 1 and 50"}), 400

    start_time = datetime.now()
    cards = extract_flashcards(text, max_cards=max_cards)
    
    # Apply adaptive difficulty if session provided
    if session_id:
        cards = adaptive_engine.adjust_flashcard_difficulty(session_id, cards, difficulty_level)
        
        # Log activity
        activity_data = {
            "cards_generated": len(cards),
            "difficulty_level": difficulty_level,
            "avg_quality_score": sum(c.get("quality_score", 0) for c in cards) / max(len(cards), 1)
        }
        performance_tracker.log_activity(
            session_id, "flashcard_generation", text, start_time, datetime.now(), activity_data
        )
    
    return jsonify({
        "count": len(cards),
        "cards": cards,
        "metadata": {
            "difficulty_level": difficulty_level,
            "avg_quality_score": round(sum(c.get("quality_score", 0) for c in cards) / max(len(cards), 1), 2)
        }
    })

@app.post("/flashcards/review")
def review_flashcard():
    """Record flashcard review performance for adaptive learning"""
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    term = data.get("term")
    is_correct = data.get("is_correct")
    response_time = data.get("response_time", 0)
    
    if not all([session_id, term, is_correct is not None]):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Update performance tracking
    performance_data = performance_tracker.update_flashcard_performance(
        session_id, term, is_correct, response_time
    )
    
    # Get adaptive recommendations
    recommendations = adaptive_engine.get_next_review_recommendations(session_id)
    
    return jsonify({
        "performance_updated": True,
        "next_recommendations": recommendations,
        "current_performance": performance_data
    })

@app.post("/quiz")
def quiz():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    max_qs = int(data.get("max_qs", 5))
    session_id = data.get("session_id")
    difficulty_level = data.get("difficulty_level", "medium")

    if not text:
        return jsonify({"error": "Missing 'text'"}), 400
    if not (1 <= max_qs <= 20):
        return jsonify({"error": "max_qs must be between 1 and 20"}), 400

    start_time = datetime.now()
    questions = build_quiz(text, max_qs=max_qs)
    
    # Apply adaptive difficulty
    if session_id:
        questions = adaptive_engine.adjust_quiz_difficulty(session_id, questions, difficulty_level)
        
        activity_data = {
            "questions_generated": len(questions),
            "difficulty_level": difficulty_level
        }
        performance_tracker.log_activity(
            session_id, "quiz_generation", text, start_time, datetime.now(), activity_data
        )
    
    return jsonify({
        "count": len(questions),
        "quiz": questions,
        "metadata": {
            "difficulty_level": difficulty_level
        }
    })

@app.post("/quiz/submit")
def submit_quiz():
    """Submit quiz answers and get performance feedback"""
    data = request.get_json(silent=True) or {}
    session_id = data.get("session_id")
    answers = data.get("answers", [])  # List of {question_id, user_answer, correct_answer, response_time}
    
    if not session_id or not answers:
        return jsonify({"error": "Missing session_id or answers"}), 400
    
    # Process quiz results
    results = performance_tracker.process_quiz_results(session_id, answers)
    
    # Get adaptive recommendations
    recommendations = adaptive_engine.analyze_quiz_performance(session_id, results)
    
    return jsonify({
        "results": results,
        "recommendations": recommendations,
        "performance_summary": performance_tracker.get_performance_summary(session_id)
    })

@app.post("/visual-qa")
def visual_question_answering():
    """Handle visual question answering for uploaded images"""
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400
    
    image_file = request.files['image']
    question = request.form.get('question', '')
    session_id = request.form.get('session_id')
    subject = request.form.get('subject', 'general')  # math, science, general
    
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    try:
        start_time = datetime.now()
        
        # Process image and question
        result = visual_qa_service.process_image_question(image_file, question, subject)
        
        # Log activity if session provided
        if session_id:
            activity_data = {
                "subject": subject,
                "question_length": len(question),
                "confidence_score": result.get("confidence", 0)
            }
            performance_tracker.log_activity(
                session_id, "visual_qa", question, start_time, datetime.now(), activity_data
            )
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Visual QA error: {e}")
        return jsonify({"error": "Visual QA processing failed"}), 500

@app.get("/performance/<session_id>")
def get_performance_analytics(session_id: str):
    """Get comprehensive performance analytics for a session"""
    try:
        analytics = performance_tracker.get_comprehensive_analytics(session_id)
        adaptive_insights = adaptive_engine.get_learning_insights(session_id)
        
        return jsonify({
            "analytics": analytics,
            "adaptive_insights": adaptive_insights,
            "recommendations": adaptive_engine.get_personalized_recommendations(session_id)
        })
        
    except Exception as e:
        print(f"Analytics error: {e}")
        return jsonify({"error": "Failed to generate analytics"}), 500

@app.post("/keywords")
def keywords():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    top_k = int(data.get("top_k", 10))
    session_id = data.get("session_id")

    if not text:
        return jsonify({"error": "Missing 'text'"}), 400
    if not (1 <= top_k <= 50):
        return jsonify({"error": "top_k must be between 1 and 50"}), 400

    start_time = datetime.now()
    kws = extract_keywords(text, top_k=top_k)
    
    # Log activity
    if session_id:
        activity_data = {"keywords_extracted": len(kws)}
        performance_tracker.log_activity(
            session_id, "keyword_extraction", text, start_time, datetime.now(), activity_data
        )

    return jsonify({"count": len(kws), "keywords": kws})

@app.post("/paraphrase")
def paraphrase_route():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    max_len = int(data.get("max_length", 128))
    session_id = data.get("session_id")

    if not text:
        return jsonify({"error": "Missing 'text'"}), 400
    if not (16 <= max_len <= 512):
        return jsonify({"error": "max_length must be between 16 and 512"}), 400

    try:
        start_time = datetime.now()
        out = paraphrase(text, max_len=max_len)
        
        # Log activity
        if session_id:
            activity_data = {
                "input_length": len(text),
                "output_length": len(out)
            }
            performance_tracker.log_activity(
                session_id, "paraphrasing", text, start_time, datetime.now(), activity_data
            )
        
        return jsonify({
            "model": "t5-small",
            "paraphrase": out,
            "metadata": {
                "length_change": len(out) - len(text)
            }
        })
    except Exception as e:
        print("Paraphrase error:", e)
        return jsonify({"error": "Paraphrasing failed"}), 500

if __name__ == "__main__":
    app.run(debug=True)