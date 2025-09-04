import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List
import uuid
import statistics

class PerformanceTracker:
    """Tracks and analyzes student performance for adaptive learning"""
    
    def __init__(self, db_path: str = 'study_assistant.db'):
        self.db_path = db_path
    
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def _hash_content(self, content: str) -> str:
        """Create hash of content for anonymized tracking"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def log_activity(self, session_id: str, activity_type: str, content: str, 
                    started_at: datetime, completed_at: datetime, 
                    performance_data: Dict) -> str:
        """Log a study activity"""
        activity_id = str(uuid.uuid4())
        content_hash = self._hash_content(content)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO study_activities 
            (activity_id, session_id, activity_type, content_hash, started_at, completed_at, performance_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (activity_id, session_id, activity_type, content_hash, started_at, completed_at, json.dumps(performance_data)))
        
        # Update session last activity
        cursor.execute('''
            UPDATE user_sessions SET last_activity = ? WHERE session_id = ?
        ''', (completed_at, session_id))
        
        conn.commit()
        conn.close()
        
        return activity_id
    
    def update_flashcard_performance(self, session_id: str, term: str, 
                                   is_correct: bool, response_time: float) -> Dict:
        """Update flashcard performance using spaced repetition principles"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get existing performance
        cursor.execute('''
            SELECT performance_id, attempts, correct_answers, difficulty_level, retention_score, last_reviewed
            FROM flashcard_performance 
            WHERE session_id = ? AND term = ?
        ''', (session_id, term))
        
        existing = cursor.fetchone()
        now = datetime.now()
        
        if existing:
            perf_id, attempts, correct_answers, difficulty, retention_score, last_reviewed = existing
            attempts += 1
            if is_correct:
                correct_answers += 1
            
            # Calculate new retention score using SM-2 algorithm principles
            accuracy = correct_answers / attempts
            
            if is_correct:
                retention_score = min(2.5, retention_score + 0.1)
                # Adaptive difficulty based on performance
                if accuracy > 0.9 and attempts >= 3:
                    difficulty = min(5, difficulty + 1)
            else:
                retention_score = max(1.3, retention_score - 0.2)
                if accuracy < 0.5:
                    difficulty = max(1, difficulty - 1)
            
            # Calculate next review time (spaced repetition)
            if is_correct:
                interval_days = max(1, int(retention_score ** difficulty))
            else:
                interval_days = 1  # Review again soon if incorrect
            
            next_review = now + timedelta(days=interval_days)
            
            cursor.execute('''
                UPDATE flashcard_performance 
                SET attempts = ?, correct_answers = ?, difficulty_level = ?, 
                    retention_score = ?, last_reviewed = ?, next_review = ?
                WHERE performance_id = ?
            ''', (attempts, correct_answers, difficulty, retention_score, now, next_review, perf_id))
            
        else:
            # New flashcard
            perf_id = str(uuid.uuid4())
            attempts = 1
            correct_answers = 1 if is_correct else 0
            difficulty = 2  # Start with medium difficulty
            retention_score = 2.5 if is_correct else 1.8
            
            next_review = now + timedelta(days=1 if is_correct else 1)
            
            cursor.execute('''
                INSERT INTO flashcard_performance 
                (performance_id, session_id, term, difficulty_level, attempts, correct_answers, 
                 last_reviewed, next_review, retention_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (perf_id, session_id, term, difficulty, attempts, correct_answers, now, next_review, retention_score))
        
        conn.commit()
        conn.close()
        
        return {
            "term": term,
            "attempts": attempts,
            "accuracy": correct_answers / attempts,
            "difficulty_level": difficulty,
            "retention_score": round(retention_score, 2),
            "next_review": next_review.isoformat(),
            "response_time": response_time
        }
    
    def process_quiz_results(self, session_id: str, answers: List[Dict]) -> Dict:
        """Process quiz results and update performance tracking"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        results = {
            "total_questions": len(answers),
            "correct_answers": 0,
            "total_time": 0,
            "question_results": []
        }
        
        for answer in answers:
            question_text = answer.get("question_text", "")
            correct_answer = answer.get("correct_answer", "")
            user_answer = answer.get("user_answer", "")
            response_time = answer.get("response_time", 0)
            difficulty_level = answer.get("difficulty_level", 2)
            
            is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
            if is_correct:
                results["correct_answers"] += 1
            
            results["total_time"] += response_time
            
            # Log quiz performance
            performance_id = str(uuid.uuid4())
            cursor.execute('''
                INSERT INTO quiz_performance 
                (performance_id, session_id, question_text, correct_answer, user_answer, 
                 is_correct, response_time, difficulty_level, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (performance_id, session_id, question_text, correct_answer, user_answer,
                  is_correct, response_time, difficulty_level, datetime.now()))
            
            results["question_results"].append({
                "question": question_text,
                "is_correct": is_correct,
                "response_time": response_time,
                "difficulty": difficulty_level
            })
        
        conn.commit()
        conn.close()
        
        # Calculate performance metrics
        results["accuracy"] = results["correct_answers"] / max(results["total_questions"], 1)
        results["average_time"] = results["total_time"] / max(results["total_questions"], 1)
        
        return results
    
    def get_performance_summary(self, session_id: str) -> Dict:
        """Get comprehensive performance summary for a session"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get session info
        cursor.execute('SELECT created_at, last_activity FROM user_sessions WHERE session_id = ?', (session_id,))
        session_info = cursor.fetchone()
        
        if not session_info:
            return {"error": "Session not found"}
        
        created_at, last_activity = session_info
        
        # Get activity summary
        cursor.execute('''
            SELECT activity_type, COUNT(*) as count, 
                   AVG((julianday(completed_at) - julianday(started_at)) * 86400) as avg_duration
            FROM study_activities 
            WHERE session_id = ? 
            GROUP BY activity_type
        ''', (session_id,))
        
        activities = {}
        for activity_type, count, avg_duration in cursor.fetchall():
            activities[activity_type] = {
                "count": count,
                "avg_duration_seconds": round(avg_duration or 0, 2)
            }
        
        # Get flashcard performance
        cursor.execute('''
            SELECT COUNT(*) as total_cards, 
                   AVG(CAST(correct_answers AS FLOAT) / attempts) as avg_accuracy,
                   AVG(retention_score) as avg_retention
            FROM flashcard_performance 
            WHERE session_id = ?
        ''', (session_id,))
        
        flashcard_stats = cursor.fetchone()
        
        # Get quiz performance
        cursor.execute('''
            SELECT COUNT(*) as total_questions, 
                   AVG(CASE WHEN is_correct THEN 1.0 ELSE 0.0 END) as accuracy,
                   AVG(response_time) as avg_response_time
            FROM quiz_performance 
            WHERE session_id = ?
        ''', (session_id,))
        
        quiz_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            "session_info": {
                "created_at": created_at,
                "last_activity": last_activity,
                "duration_hours": (datetime.fromisoformat(last_activity) - datetime.fromisoformat(created_at)).total_seconds() / 3600
            },
            "activities": activities,
            "flashcard_performance": {
                "total_cards": flashcard_stats[0] or 0,
                "avg_accuracy": round(flashcard_stats[1] or 0, 3),
                "avg_retention_score": round(flashcard_stats[2] or 0, 2)
            },
            "quiz_performance": {
                "total_questions": quiz_stats[0] or 0,
                "accuracy": round(quiz_stats[1] or 0, 3),
                "avg_response_time": round(quiz_stats[2] or 0, 2)
            }
        }
    
    def get_comprehensive_analytics(self, session_id: str) -> Dict:
        """Get detailed analytics including trends and insights"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get learning progress over time (daily)
        cursor.execute('''
            SELECT DATE(timestamp) as day, 
                   AVG(CASE WHEN is_correct THEN 1.0 ELSE 0.0 END) as daily_accuracy,
                   COUNT(*) as questions_answered
            FROM quiz_performance 
            WHERE session_id = ? 
            GROUP BY DATE(timestamp)
            ORDER BY day
        ''', (session_id,))
        
        daily_progress = [
            {"date": row[0], "accuracy": round(row[1], 3), "questions": row[2]}
            for row in cursor.fetchall()
        ]
        
        # Get difficulty progression
        cursor.execute('''
            SELECT difficulty_level, 
                   AVG(CASE WHEN is_correct THEN 1.0 ELSE 0.0 END) as accuracy,
                   COUNT(*) as count,
                   AVG(response_time) as avg_time
            FROM quiz_performance 
            WHERE session_id = ? 
            GROUP BY difficulty_level
            ORDER BY difficulty_level
        ''', (session_id,))
        
        difficulty_analysis = [
            {
                "difficulty": row[0],
                "accuracy": round(row[1], 3),
                "questions_count": row[2],
                "avg_response_time": round(row[3], 2)
            }
            for row in cursor.fetchall()
        ]
        
        # Get weak areas (topics with low performance)
        cursor.execute('''
            SELECT fp.term, 
                   CAST(fp.correct_answers AS FLOAT) / fp.attempts as accuracy,
                   fp.attempts,
                   fp.difficulty_level,
                   fp.retention_score
            FROM flashcard_performance fp
            WHERE fp.session_id = ? 
            AND CAST(fp.correct_answers AS FLOAT) / fp.attempts < 0.7
            ORDER BY accuracy ASC
            LIMIT 10
        ''', (session_id,))
        
        weak_areas = [
            {
                "term": row[0],
                "accuracy": round(row[1], 3),
                "attempts": row[2],
                "difficulty": row[3],
                "retention_score": round(row[4], 2)
            }
            for row in cursor.fetchall()
        ]
        
        # Get strong areas
        cursor.execute('''
            SELECT fp.term, 
                   CAST(fp.correct_answers AS FLOAT) / fp.attempts as accuracy,
                   fp.attempts,
                   fp.retention_score
            FROM flashcard_performance fp
            WHERE fp.session_id = ? 
            AND CAST(fp.correct_answers AS FLOAT) / fp.attempts >= 0.9
            AND fp.attempts >= 3
            ORDER BY accuracy DESC, retention_score DESC
            LIMIT 10
        ''', (session_id,))
        
        strong_areas = [
            {
                "term": row[0],
                "accuracy": round(row[1], 3),
                "attempts": row[2],
                "retention_score": round(row[3], 2)
            }
            for row in cursor.fetchall()
        ]
        
        # Calculate learning velocity (improvement over time)
        if len(daily_progress) >= 2:
            recent_accuracy = statistics.mean([day["accuracy"] for day in daily_progress[-3:]])
            early_accuracy = statistics.mean([day["accuracy"] for day in daily_progress[:3]])
            learning_velocity = recent_accuracy - early_accuracy
        else:
            learning_velocity = 0
        
        conn.close()
        
        return {
            "daily_progress": daily_progress,
            "difficulty_analysis": difficulty_analysis,
            "weak_areas": weak_areas,
            "strong_areas": strong_areas,
            "learning_velocity": round(learning_velocity, 3),
            "insights": self._generate_insights(daily_progress, difficulty_analysis, weak_areas)
        }
    
    def _generate_insights(self, daily_progress: List[Dict], 
                          difficulty_analysis: List[Dict], 
                          weak_areas: List[Dict]) -> List[str]:
        """Generate actionable insights from performance data"""
        insights = []
        
        if daily_progress:
            recent_accuracy = daily_progress[-1]["accuracy"] if daily_progress else 0
            if recent_accuracy > 0.8:
                insights.append("Great job! Your recent performance shows strong understanding.")
            elif recent_accuracy < 0.6:
                insights.append("Consider reviewing the material more thoroughly before attempting quizzes.")
        
        if difficulty_analysis:
            easy_performance = next((d for d in difficulty_analysis if d["difficulty"] == 1), None)
            hard_performance = next((d for d in difficulty_analysis if d["difficulty"] >= 4), None)
            
            if easy_performance and easy_performance["accuracy"] < 0.7:
                insights.append("Focus on mastering basic concepts before advancing to harder material.")
            
            if hard_performance and hard_performance["accuracy"] > 0.7:
                insights.append("You're ready for more challenging content! Consider increasing difficulty.")
        
        if len(weak_areas) > 5:
            insights.append(f"You have {len(weak_areas)} topics that need more attention. Try spaced repetition.")
        
        if len(daily_progress) >= 3:
            recent_trend = [day["accuracy"] for day in daily_progress[-3:]]
            if all(recent_trend[i] >= recent_trend[i-1] for i in range(1, len(recent_trend))):
                insights.append("Your performance is consistently improving - keep up the momentum!")
        
        return insights