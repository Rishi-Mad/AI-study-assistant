import sqlite3
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math

class AdaptiveLearningEngine:
    
    def __init__(self, db_path: str = 'study_assistant.db'):
        self.db_path = db_path
        
        self.difficulty_levels = {
            1: {"name": "Beginner", "multiplier": 0.8, "time_bonus": 1.2},
            2: {"name": "Easy", "multiplier": 0.9, "time_bonus": 1.1},
            3: {"name": "Medium", "multiplier": 1.0, "time_bonus": 1.0},
            4: {"name": "Hard", "multiplier": 1.2, "time_bonus": 0.9},
            5: {"name": "Expert", "multiplier": 1.5, "time_bonus": 0.8}
        }
    
    def _get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def adjust_flashcard_difficulty(self, session_id: str, cards: List[Dict], 
                                   current_level: str = "medium") -> List[Dict]:
        """Adjust flashcard difficulty based on user performance"""
        if not cards:
            return cards
        
        # Get user's performance history
        performance_stats = self._get_user_performance_stats(session_id)
        
        # Determine optimal difficulty
        optimal_difficulty = self._calculate_optimal_difficulty(performance_stats)
        
        # Apply difficulty adjustments to cards
        adjusted_cards = []
        for card in cards:
            adjusted_card = card.copy()
            
            # Adjust based on user's historical performance with this term
            term_performance = self._get_term_performance(session_id, card.get("term", ""))
            
            if term_performance:
                if term_performance["accuracy"] > 0.9:
                    # User knows this well, make it harder or skip
                    if random.random() < 0.3:  # 30% chance to include for reinforcement
                        adjusted_card["difficulty_level"] = min(5, optimal_difficulty + 1)
                        adjusted_card["review_priority"] = "low"
                    else:
                        continue  # Skip this card
                elif term_performance["accuracy"] < 0.5:
                    # User struggles with this, make it easier and prioritize
                    adjusted_card["difficulty_level"] = max(1, optimal_difficulty - 1)
                    adjusted_card["review_priority"] = "high"
                else:
                    adjusted_card["difficulty_level"] = optimal_difficulty
                    adjusted_card["review_priority"] = "medium"
            else:
                # New term, use base difficulty
                adjusted_card["difficulty_level"] = optimal_difficulty
                adjusted_card["review_priority"] = "medium"
            
            # Add spaced repetition metadata
            adjusted_card["next_review"] = self._calculate_next_review_time(
                term_performance.get("retention_score", 2.0) if term_performance else 2.0,
                adjusted_card["difficulty_level"]
            ).isoformat()
            
            adjusted_cards.append(adjusted_card)
        
        # Sort by priority (high priority first)
        priority_order = {"high": 3, "medium": 2, "low": 1}
        adjusted_cards.sort(
            key=lambda x: priority_order.get(x.get("review_priority", "medium"), 2),
            reverse=True
        )
        
        return adjusted_cards
    
    def adjust_quiz_difficulty(self, session_id: str, questions: List[Dict], 
                              current_level: str = "medium") -> List[Dict]:
        """Adjust quiz difficulty based on user performance"""
        if not questions:
            return questions
        
        performance_stats = self._get_user_performance_stats(session_id)
        optimal_difficulty = self._calculate_optimal_difficulty(performance_stats)
        
        # Apply adaptive difficulty to questions
        adjusted_questions = []
        for i, question in enumerate(questions):
            adjusted_question = question.copy()
            
            # Gradually increase difficulty throughout the quiz
            question_difficulty = min(5, optimal_difficulty + (i // 3))
            adjusted_question["difficulty_level"] = question_difficulty
            
            # Adjust question complexity based on difficulty
            if question_difficulty <= 2:
                # Easier: More obvious distractors
                adjusted_question = self._simplify_question(adjusted_question)
            elif question_difficulty >= 4:
                # Harder: More subtle distractors, complex phrasing
                adjusted_question = self._complexify_question(adjusted_question)
            
            # Add timing expectations based on difficulty
            base_time = 30  # seconds
            adjusted_question["expected_time"] = int(
                base_time * self.difficulty_levels[question_difficulty]["multiplier"]
            )
            
            adjusted_questions.append(adjusted_question)
        
        return adjusted_questions
    
    def analyze_quiz_performance(self, session_id: str, results: Dict) -> Dict:
        """Analyze quiz performance and provide adaptive recommendations"""
        accuracy = results.get("accuracy", 0)
        avg_time = results.get("average_time", 30)
        question_results = results.get("question_results", [])
        
        recommendations = {
            "next_difficulty": self._recommend_next_difficulty(accuracy, avg_time),
            "focus_areas": self._identify_focus_areas(question_results),
            "study_plan": self._generate_study_plan(session_id, accuracy, question_results),
            "motivation_message": self._get_motivation_message(accuracy),
            "streak_info": self._calculate_streak_info(session_id)
        }
        
        return recommendations
    
    def get_next_review_recommendations(self, session_id: str) -> List[Dict]:
        """Get terms that are due for review (spaced repetition)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        now = datetime.now()
        
        # Get terms due for review
        cursor.execute('''
            SELECT term, difficulty_level, retention_score, attempts, correct_answers, next_review
            FROM flashcard_performance
            WHERE session_id = ? AND next_review <= ?
            ORDER BY next_review ASC, retention_score ASC
            LIMIT 10
        ''', (session_id, now))
        
        due_reviews = []
        for row in cursor.fetchall():
            term, difficulty, retention_score, attempts, correct, next_review = row
            accuracy = correct / max(attempts, 1)
            
            due_reviews.append({
                "term": term,
                "difficulty_level": difficulty,
                "retention_score": round(retention_score, 2),
                "accuracy": round(accuracy, 2),
                "urgency": self._calculate_review_urgency(next_review, retention_score),
                "estimated_time": int(30 * (difficulty / 3))  # Estimated time in seconds
            })
        
        conn.close()
        return due_reviews
    
    def get_learning_insights(self, session_id: str) -> Dict:
        """Generate learning insights similar to Duolingo's insights"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get recent activity (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        
        cursor.execute('''
            SELECT DATE(timestamp) as day, COUNT(*) as questions
            FROM quiz_performance
            WHERE session_id = ? AND timestamp > ?
            GROUP BY DATE(timestamp)
            ORDER BY day DESC
        ''', (session_id, week_ago))
        
        daily_activity = cursor.fetchall()
        
        # Calculate streak
        current_streak = self._calculate_current_streak(session_id)
        
        # Get learning velocity
        cursor.execute('''
            SELECT 
                AVG(CASE WHEN is_correct THEN 1.0 ELSE 0.0 END) as recent_accuracy,
                AVG(response_time) as avg_response_time,
                COUNT(*) as total_questions
            FROM quiz_performance
            WHERE session_id = ? AND timestamp > ?
        ''', (session_id, week_ago))
        
        recent_stats = cursor.fetchone()
        
        # Get mastery distribution
        cursor.execute('''
            SELECT 
                CASE 
                    WHEN CAST(correct_answers AS FLOAT) / attempts >= 0.9 THEN 'mastered'
                    WHEN CAST(correct_answers AS FLOAT) / attempts >= 0.7 THEN 'learning'
                    ELSE 'struggling'
                END as mastery_level,
                COUNT(*) as count
            FROM flashcard_performance
            WHERE session_id = ?
            GROUP BY mastery_level
        ''', (session_id,))
        
        mastery_distribution = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        # Generate insights
        insights = {
            "current_streak": current_streak,
            "weekly_activity": len(daily_activity),
            "consistency_score": self._calculate_consistency_score(daily_activity),
            "mastery_distribution": mastery_distribution,
            "learning_momentum": self._calculate_learning_momentum(session_id),
            "achievement_badges": self._check_achievements(session_id, current_streak, mastery_distribution)
        }
        
        if recent_stats and recent_stats[2] > 0:  # If there are recent questions
            insights.update({
                "recent_accuracy": round(recent_stats[0], 2),
                "avg_response_time": round(recent_stats[1], 1),
                "questions_this_week": recent_stats[2]
            })
        
        return insights
    
    def get_personalized_recommendations(self, session_id: str) -> List[Dict]:
        """Get personalized recommendations for the user"""
        performance_stats = self._get_user_performance_stats(session_id)
        insights = self.get_learning_insights(session_id)
        
        recommendations = []
        
        # Consistency recommendations
        if insights.get("consistency_score", 0) < 0.5:
            recommendations.append({
                "type": "consistency",
                "priority": "high",
                "title": "Build a Daily Habit",
                "message": "Try studying for just 10 minutes each day to build consistency.",
                "action": "Set a daily reminder"
            })
        
        # Difficulty recommendations
        if performance_stats.get("avg_accuracy", 0) > 0.85:
            recommendations.append({
                "type": "difficulty",
                "priority": "medium",
                "title": "Ready for a Challenge",
                "message": "You're doing great! Try increasing the difficulty level.",
                "action": "Increase difficulty"
            })
        elif performance_stats.get("avg_accuracy", 0) < 0.6:
            recommendations.append({
                "type": "difficulty",
                "priority": "high",
                "title": "Focus on Fundamentals",
                "message": "Consider reviewing basic concepts before advancing.",
                "action": "Review easier content"
            })
        
        # Review recommendations
        due_reviews = self.get_next_review_recommendations(session_id)
        if len(due_reviews) > 5:
            recommendations.append({
                "type": "review",
                "priority": "high",
                "title": "Review Time!",
                "message": f"You have {len(due_reviews)} terms ready for review.",
                "action": "Start review session"
            })
        
        # Motivation recommendations
        streak = insights.get("current_streak", 0)
        if streak >= 7:
            recommendations.append({
                "type": "motivation",
                "priority": "low",
                "title": "Streak Master!",
                "message": f"Amazing {streak}-day streak! Keep it up!",
                "action": "Continue streak"
            })
        
        return sorted(recommendations, key=lambda x: {"high": 3, "medium": 2, "low": 1}[x["priority"]], reverse=True)
    
    def _get_user_performance_stats(self, session_id: str) -> Dict:
        """Get comprehensive user performance statistics"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Quiz performance
        cursor.execute('''
            SELECT 
                AVG(CASE WHEN is_correct THEN 1.0 ELSE 0.0 END) as avg_accuracy,
                AVG(response_time) as avg_response_time,
                COUNT(*) as total_questions,
                AVG(difficulty_level) as avg_difficulty
            FROM quiz_performance
            WHERE session_id = ?
        ''', (session_id,))
        
        quiz_stats = cursor.fetchone()
        
        # Flashcard performance
        cursor.execute('''
            SELECT 
                AVG(CAST(correct_answers AS FLOAT) / attempts) as flashcard_accuracy,
                AVG(retention_score) as avg_retention,
                COUNT(*) as total_cards
            FROM flashcard_performance
            WHERE session_id = ?
        ''', (session_id,))
        
        flashcard_stats = cursor.fetchone()
        
        conn.close()
        
        return {
            "avg_accuracy": quiz_stats[0] or 0,
            "avg_response_time": quiz_stats[1] or 30,
            "total_questions": quiz_stats[2] or 0,
            "avg_difficulty": quiz_stats[3] or 3,
            "flashcard_accuracy": flashcard_stats[0] or 0,
            "avg_retention": flashcard_stats[1] or 2.0,
            "total_cards": flashcard_stats[2] or 0
        }
    
    def _get_term_performance(self, session_id: str, term: str) -> Optional[Dict]:
        """Get performance data for a specific term"""
        if not term:
            return None
            
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT attempts, correct_answers, retention_score, difficulty_level, last_reviewed
            FROM flashcard_performance
            WHERE session_id = ? AND term = ?
        ''', (session_id, term))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            attempts, correct, retention, difficulty, last_reviewed = result
            return {
                "attempts": attempts,
                "accuracy": correct / max(attempts, 1),
                "retention_score": retention,
                "difficulty_level": difficulty,
                "last_reviewed": last_reviewed
            }
        return None
    
    def _calculate_optimal_difficulty(self, performance_stats: Dict) -> int:
        """Calculate optimal difficulty level based on performance"""
        accuracy = performance_stats.get("avg_accuracy", 0.7)
        avg_time = performance_stats.get("avg_response_time", 30)
        total_questions = performance_stats.get("total_questions", 0)
        
        # Base difficulty on accuracy
        if accuracy >= 0.9:
            base_difficulty = 4
        elif accuracy >= 0.8:
            base_difficulty = 3
        elif accuracy >= 0.6:
            base_difficulty = 2
        else:
            base_difficulty = 1
        
        # Adjust for response time (quick responses suggest readiness for harder content)
        if avg_time < 15:
            base_difficulty = min(5, base_difficulty + 1)
        elif avg_time > 45:
            base_difficulty = max(1, base_difficulty - 1)
        
        # Consider experience (more questions = ready for more complexity)
        if total_questions > 100:
            base_difficulty = min(5, base_difficulty + 1)
        elif total_questions < 20:
            base_difficulty = max(1, base_difficulty - 1)
        
        return max(1, min(5, base_difficulty))
    
    def _calculate_next_review_time(self, retention_score: float, difficulty_level: int) -> datetime:
        """Calculate next review time using spaced repetition (SM-2 inspired algorithm)"""
        # Base interval in hours
        base_interval = 24  # 1 day
        
        # Calculate interval based on retention score and difficulty
        interval_hours = base_interval * (retention_score ** (difficulty_level * 0.5))
        
        # Cap the interval (max 30 days)
        interval_hours = min(interval_hours, 24 * 30)
        
        return datetime.now() + timedelta(hours=interval_hours)
    
    def _calculate_review_urgency(self, next_review_str: str, retention_score: float) -> str:
        """Calculate how urgent a review is"""
        next_review = datetime.fromisoformat(next_review_str)
        now = datetime.now()
        
        hours_overdue = (now - next_review).total_seconds() / 3600
        
        if hours_overdue > 48:  # More than 2 days overdue
            return "critical"
        elif hours_overdue > 24:  # More than 1 day overdue
            return "high"
        elif hours_overdue > 0:  # Overdue
            return "medium"
        else:
            return "low"
    
    def _calculate_current_streak(self, session_id: str) -> int:
        """Calculate current daily study streak"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get distinct study days ordered by date (most recent first)
        cursor.execute('''
            SELECT DISTINCT DATE(timestamp) as study_day
            FROM quiz_performance
            WHERE session_id = ?
            ORDER BY study_day DESC
        ''', (session_id,))
        
        study_days = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if not study_days:
            return 0
        
        streak = 0
        today = datetime.now().date()
        
        for i, day_str in enumerate(study_days):
            day = datetime.fromisoformat(day_str).date()
            expected_day = today - timedelta(days=i)
            
            if day == expected_day:
                streak += 1
            elif day == expected_day - timedelta(days=1) and i == 0:
                # Allow for yesterday if today hasn't been studied yet
                streak += 1
            else:
                break
        
        return streak
    
    def _simplify_question(self, question: Dict) -> Dict:
        """Simplify a question for lower difficulty"""
        # This is a placeholder - in a real implementation, you might:
        # - Make distractors more obviously wrong
        # - Use simpler vocabulary
        # - Provide more context
        question["hint"] = "Think about the basic definition"
        return question
    
    def _complexify_question(self, question: Dict) -> Dict:
        """Make a question more complex for higher difficulty"""
        # This is a placeholder - in a real implementation, you might:
        # - Make distractors more subtle
        # - Use more complex vocabulary
        # - Require deeper understanding
        question["requires_analysis"] = True
        return question
    
    def _recommend_next_difficulty(self, accuracy: float, avg_time: float) -> str:
        """Recommend next difficulty level based on performance"""
        if accuracy >= 0.9 and avg_time < 20:
            return "increase"
        elif accuracy < 0.6 or avg_time > 60:
            return "decrease"
        else:
            return "maintain"
    
    def _identify_focus_areas(self, question_results: List[Dict]) -> List[str]:
        """Identify areas that need more focus"""
        focus_areas = []
        
        # Group by difficulty and analyze performance
        difficulty_performance = {}
        for result in question_results:
            difficulty = result.get("difficulty", 3)
            if difficulty not in difficulty_performance:
                difficulty_performance[difficulty] = []
            difficulty_performance[difficulty].append(result["is_correct"])
        
        for difficulty, results in difficulty_performance.items():
            accuracy = sum(results) / len(results)
            if accuracy < 0.6:
                focus_areas.append(f"Difficulty level {difficulty}")
        
        return focus_areas
    
    def _generate_study_plan(self, session_id: str, accuracy: float, question_results: List[Dict]) -> Dict:
        """Generate a personalized study plan"""
        plan = {
            "recommended_daily_minutes": 15 if accuracy < 0.7 else 20,
            "focus": "review" if accuracy < 0.7 else "new_content",
            "suggested_activities": []
        }
        
        if accuracy < 0.6:
            plan["suggested_activities"] = [
                "Review flashcards for 10 minutes",
                "Take a practice quiz on easier difficulty",
                "Focus on one topic at a time"
            ]
        elif accuracy < 0.8:
            plan["suggested_activities"] = [
                "Mix review and new content",
                "Take regular quizzes to test understanding",
                "Practice spaced repetition"
            ]
        else:
            plan["suggested_activities"] = [
                "Challenge yourself with harder content",
                "Teach concepts to reinforce learning",
                "Explore advanced topics"
            ]
        
        return plan
    
    def _get_motivation_message(self, accuracy: float) -> str:
        """Get motivational message based on performance"""
        if accuracy >= 0.9:
            messages = [
                "Excellent work! You're mastering this material!",
                "Outstanding performance! Keep up the great work!",
                "You're on fire! Your hard work is paying off!"
            ]
        elif accuracy >= 0.7:
            messages = [
                "Good job! You're making solid progress!",
                "Nice work! Keep practicing to improve further!",
                "You're doing well! Stay consistent!"
            ]
        else:
            messages = [
                "Don't give up! Every expert was once a beginner!",
                "Keep practicing! You're building important skills!",
                "Progress takes time. You're on the right track!"
            ]
        
        return random.choice(messages)
    
    def _calculate_streak_info(self, session_id: str) -> Dict:
        """Calculate streak information"""
        current_streak = self._calculate_current_streak(session_id)
        
        # Get longest streak
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT DATE(timestamp) as study_day
            FROM quiz_performance
            WHERE session_id = ?
            ORDER BY study_day ASC
        ''', (session_id,))
        
        all_days = [datetime.fromisoformat(row[0]).date() for row in cursor.fetchall()]
        conn.close()
        
        longest_streak = 0
        current_count = 1
        
        for i in range(1, len(all_days)):
            if (all_days[i] - all_days[i-1]).days == 1:
                current_count += 1
                longest_streak = max(longest_streak, current_count)
            else:
                current_count = 1
        
        return {
            "current_streak": current_streak,
            "longest_streak": max(longest_streak, current_streak),
            "streak_target": max(current_streak + 1, 7)  # Next milestone
        }
    
    def _calculate_consistency_score(self, daily_activity: List[Tuple]) -> float:
        """Calculate consistency score (0-1) based on daily activity"""
        if not daily_activity:
            return 0.0
        
        # Look at last 7 days
        days_with_activity = len(daily_activity)
        return min(1.0, days_with_activity / 7.0)
    
    def _calculate_learning_momentum(self, session_id: str) -> str:
        """Calculate learning momentum trend"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get accuracy for last 3 sessions (groups of 10 questions)
        cursor.execute('''
            WITH numbered_questions AS (
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY timestamp) as row_num,
                    CASE WHEN is_correct THEN 1.0 ELSE 0.0 END as correct
                FROM quiz_performance
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT 30
            )
            SELECT 
                (row_num - 1) / 10 as session_group,
                AVG(correct) as accuracy
            FROM numbered_questions
            GROUP BY (row_num - 1) / 10
            ORDER BY session_group DESC
            LIMIT 3
        ''', (session_id,))
        
        session_accuracies = [row[1] for row in cursor.fetchall()]
        conn.close()
        
        if len(session_accuracies) < 2:
            return "insufficient_data"
        
        # Compare most recent to previous
        if len(session_accuracies) >= 2:
            recent_change = session_accuracies[0] - session_accuracies[1]
            
            if recent_change > 0.1:
                return "accelerating"
            elif recent_change > 0.05:
                return "improving"
            elif recent_change > -0.05:
                return "steady"
            elif recent_change > -0.1:
                return "declining"
            else:
                return "struggling"
        
        return "steady"
    
    def _check_achievements(self, session_id: str, streak: int, mastery_dist: Dict) -> List[Dict]:
        """Check for achievement badges"""
        badges = []
        
        # Streak achievements
        if streak >= 30:
            badges.append({"name": "Dedication Master", "description": "30-day study streak!", "type": "streak"})
        elif streak >= 14:
            badges.append({"name": "Committed Learner", "description": "2-week study streak!", "type": "streak"})
        elif streak >= 7:
            badges.append({"name": "Week Warrior", "description": "7-day study streak!", "type": "streak"})
        elif streak >= 3:
            badges.append({"name": "Getting Started", "description": "3-day study streak!", "type": "streak"})
        
        # Mastery achievements
        mastered_count = mastery_dist.get("mastered", 0)
        if mastered_count >= 50:
            badges.append({"name": "Knowledge Master", "description": "Mastered 50+ concepts!", "type": "mastery"})
        elif mastered_count >= 25:
            badges.append({"name": "Expert Learner", "description": "Mastered 25+ concepts!", "type": "mastery"})
        elif mastered_count >= 10:
            badges.append({"name": "Rising Star", "description": "Mastered 10+ concepts!", "type": "mastery"})
        
        # Get total questions answered
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM quiz_performance WHERE session_id = ?', (session_id,))
        total_questions = cursor.fetchone()[0]
        conn.close()
        
        # Volume achievements
        if total_questions >= 1000:
            badges.append({"name": "Quiz Champion", "description": "Answered 1000+ questions!", "type": "volume"})
        elif total_questions >= 500:
            badges.append({"name": "Question Master", "description": "Answered 500+ questions!", "type": "volume"})
        elif total_questions >= 100:
            badges.append({"name": "Active Learner", "description": "Answered 100+ questions!", "type": "volume"})
        
        return badges