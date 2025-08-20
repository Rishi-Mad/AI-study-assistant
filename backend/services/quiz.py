import random
import re
from typing import List, Dict, Set, Tuple
from services.flashcards import extract_flashcards
from utils.text import sentences, normalize_space
import hashlib

class EnhancedQuizService:
    """Enhanced quiz generation with adaptive difficulty and improved question types"""
    
    def __init__(self):
        self.question_templates = {
            "definition": [
                "What is {term}?",
                "How would you define {term}?",
                "{term} refers to:",
                "Which of the following best describes {term}?"
            ],
            "application": [
                "When would you use {term}?",
                "An example of {term} would be:",
                "{term} is commonly applied in:",
                "The main purpose of {term} is:"
            ],
            "comparison": [
                "How does {term} differ from other concepts?",
                "What makes {term} unique?",
                "Compared to similar concepts, {term} is:",
                "The key distinction of {term} is:"
            ],
            "cause_effect": [
                "What causes {term}?",
                "What is the result of {term}?",
                "If {term} occurs, what happens?",
                "{term} leads to:"
            ]
        }
        
        self.difficulty_modifiers = {
            1: {"name": "Beginner", "distractors": "obvious", "complexity": "simple"},
            2: {"name": "Easy", "distractors": "somewhat_obvious", "complexity": "simple"},
            3: {"name": "Medium", "distractors": "plausible", "complexity": "moderate"},
            4: {"name": "Hard", "distractors": "subtle", "complexity": "complex"},
            5: {"name": "Expert", "distractors": "very_subtle", "complexity": "very_complex"}
        }
    
    def build_quiz(self, text: str, max_qs: int = 5, difficulty_level: int = 3, 
                   question_types: List[str] = None) -> List[Dict]:
        """Enhanced quiz building with multiple question types and adaptive difficulty"""
        
        # Extract flashcards as base material
        cards = extract_flashcards(text, max_cards=max_qs * 3)  # Get more cards for variety
        if not cards:
            return []
        
        # Default question types
        if question_types is None:
            question_types = ["definition", "application", "comparison"]
        
        quiz_questions = []
        used_terms = set()
        
        # Generate different types of questions
        for i, card in enumerate(cards[:max_qs]):
            if card["term"].lower() in used_terms:
                continue
            
            used_terms.add(card["term"].lower())
            
            # Choose question type based on position and difficulty
            if i == 0:  # First question is always definition
                q_type = "definition"
            else:
                q_type = random.choice(question_types)
            
            question = self._generate_question_by_type(
                card, q_type, difficulty_level, cards, text
            )
            
            if question:
                quiz_questions.append(question)
        
        # Add variety questions if we have room
        if len(quiz_questions) < max_qs:
            variety_questions = self._generate_variety_questions(
                text, max_qs - len(quiz_questions), difficulty_level, used_terms
            )
            quiz_questions.extend(variety_questions)
        
        return quiz_questions[:max_qs]
    
    def _generate_question_by_type(self, card: Dict, question_type: str, 
                                   difficulty_level: int, all_cards: List[Dict], 
                                   full_text: str) -> Dict:
        """Generate a question of specific type"""
        
        term = card["term"]
        correct_answer = card["answer"]
        
        if question_type == "definition":
            return self._create_definition_question(card, difficulty_level, all_cards)
        
        elif question_type == "application":
            return self._create_application_question(card, difficulty_level, full_text, all_cards)
        
        elif question_type == "comparison":
            return self._create_comparison_question(card, difficulty_level, all_cards)
        
        elif question_type == "cause_effect":
            return self._create_cause_effect_question(card, difficulty_level, full_text)
        
        else:
            # Default to definition
            return self._create_definition_question(card, difficulty_level, all_cards)
    
    def _create_definition_question(self, card: Dict, difficulty_level: int, 
                                    all_cards: List[Dict]) -> Dict:
        """Create a definition-style question"""
        term = card["term"]
        correct_answer = card["answer"]
        
        # Choose question template
        template = random.choice(self.question_templates["definition"])
        question_text = template.format(term=term)
        
        # Generate distractors
        distractors = self._generate_smart_distractors(
            correct_answer, all_cards, difficulty_level, "definition"
        )
        
        return self._build_question_dict(
            question_text, correct_answer, distractors, difficulty_level, 
            "definition", term, card.get("quality_score", 0.5)
        )
    
    def _create_application_question(self, card: Dict, difficulty_level: int, 
                                     full_text: str, all_cards: List[Dict]) -> Dict:
        """Create an application-style question"""
        term = card["term"]
        
        # Extract context about when/how the term is used
        context_sentences = self._find_context_sentences(term, full_text)
        
        if not context_sentences:
            # Fall back to definition question
            return self._create_definition_question(card, difficulty_level, all_cards)
        
        # Create application-focused answer
        application_context = self._extract_application_context(context_sentences, term)
        
        template = random.choice(self.question_templates["application"])
        question_text = template.format(term=term)
        
        # Generate application-specific distractors
        distractors = self._generate_application_distractors(
            application_context, all_cards, difficulty_level
        )
        
        return self._build_question_dict(
            question_text, application_context, distractors, difficulty_level,
            "application", term, card.get("quality_score", 0.5)
        )
    
    def _create_comparison_question(self, card: Dict, difficulty_level: int, 
                                    all_cards: List[Dict]) -> Dict:
        """Create a comparison-style question"""
        term = card["term"]
        correct_answer = card["answer"]
        
        # Find similar terms for comparison
        similar_terms = self._find_similar_terms(card, all_cards)
        
        if not similar_terms:
            # Fall back to definition question
            return self._create_definition_question(card, difficulty_level, all_cards)
        
        # Create comparison-focused question and answer
        template = random.choice(self.question_templates["comparison"])
        question_text = template.format(term=term)
        
        # Modify answer to focus on distinguishing features
        comparison_answer = self._create_comparison_answer(correct_answer, similar_terms)
        
        # Generate comparison distractors
        distractors = self._generate_comparison_distractors(
            comparison_answer, similar_terms, difficulty_level
        )
        
        return self._build_question_dict(
            question_text, comparison_answer, distractors, difficulty_level,
            "comparison", term, card.get("quality_score", 0.5)
        )
    
    def _create_cause_effect_question(self, card: Dict, difficulty_level: int, 
                                      full_text: str) -> Dict:
        """Create a cause-and-effect style question"""
        term = card["term"]
        
        # Look for cause-effect relationships in the text
        cause_effect_context = self._find_cause_effect_context(term, full_text)
        
        if not cause_effect_context:
            # Fall back to definition question
            return self._create_definition_question(card, difficulty_level, [])
        
        template = random.choice(self.question_templates["cause_effect"])
        question_text = template.format(term=term)
        
        # Generate cause-effect distractors
        distractors = self._generate_cause_effect_distractors(
            cause_effect_context, difficulty_level
        )
        
        return self._build_question_dict(
            question_text, cause_effect_context, distractors, difficulty_level,
            "cause_effect", term, card.get("quality_score", 0.5)
        )
    
    def _generate_smart_distractors(self, correct_answer: str, all_cards: List[Dict], 
                                    difficulty_level: int, question_type: str) -> List[str]:
        """Generate intelligent distractors based on difficulty level"""
        
        distractors = []
        answers_pool = [c["answer"] for c in all_cards if c["answer"] != correct_answer]
        
        if difficulty_level <= 2:  # Easy - obvious distractors
            distractors = self._generate_obvious_distractors(correct_answer, answers_pool)
        
        elif difficulty_level == 3:  # Medium - plausible distractors
            distractors = self._generate_plausible_distractors(correct_answer, answers_pool)
        
        else:  # Hard - subtle distractors
            distractors = self._generate_subtle_distractors(correct_answer, answers_pool)
        
        # Ensure we have exactly 3 distractors
        while len(distractors) < 3 and answers_pool:
            candidate = random.choice(answers_pool)
            if candidate not in distractors and candidate != correct_answer:
                distractors.append(candidate)
                answers_pool.remove(candidate)
        
        # If we still don't have enough, generate generic ones
        while len(distractors) < 3:
            generic = self._generate_generic_distractor(correct_answer, len(distractors))
            distractors.append(generic)
        
        return distractors[:3]
    
    def _generate_obvious_distractors(self, correct_answer: str, answers_pool: List[str]) -> List[str]:
        """Generate obviously wrong distractors for easy questions"""
        distractors = []
        
        # Look for answers that are clearly different in key ways
        for answer in answers_pool:
            if len(distractors) >= 3:
                break
                
            # Different length categories
            if len(answer.split()) != len(correct_answer.split()):
                distractors.append(answer)
                continue
            
            # Different starting words
            correct_words = correct_answer.lower().split()
            answer_words = answer.lower().split()
            
            if (correct_words and answer_words and 
                correct_words[0] != answer_words[0]):
                distractors.append(answer)
        
        return distractors
    
    def _generate_plausible_distractors(self, correct_answer: str, answers_pool: List[str]) -> List[str]:
        """Generate plausible but incorrect distractors"""
        distractors = []
        correct_words = set(correct_answer.lower().split())
        
        # Score answers by similarity (we want moderate similarity)
        answer_scores = []
        for answer in answers_pool:
            answer_words = set(answer.lower().split())
            similarity = len(correct_words.intersection(answer_words)) / len(correct_words.union(answer_words))
            answer_scores.append((answer, similarity))
        
        # Sort by similarity and take middle range (0.1 to 0.4 similarity)
        answer_scores.sort(key=lambda x: x[1])
        
        for answer, similarity in answer_scores:
            if len(distractors) >= 3:
                break
            if 0.1 <= similarity <= 0.4:  # Moderate similarity
                distractors.append(answer)
        
        return distractors
    
    def _generate_subtle_distractors(self, correct_answer: str, answers_pool: List[str]) -> List[str]:
        """Generate subtle, hard-to-distinguish distractors"""
        distractors = []
        correct_words = set(correct_answer.lower().split())
        
        # Look for answers with high similarity but key differences
        for answer in answers_pool:
            if len(distractors) >= 3:
                break
                
            answer_words = set(answer.lower().split())
            similarity = len(correct_words.intersection(answer_words)) / len(correct_words.union(answer_words))
            
            # High similarity but not identical
            if 0.4 <= similarity <= 0.8:
                distractors.append(answer)
        
        return distractors
    
    def _generate_generic_distractor(self, correct_answer: str, index: int) -> str:
        """Generate a generic distractor when we can't find good ones"""
        generic_templates = [
            "A process that involves multiple steps",
            "A concept related to system organization",
            "A method used in various applications",
            "A principle that guides decision making",
            "A framework for understanding relationships"
        ]
        
        if index < len(generic_templates):
            return generic_templates[index]
        else:
            return f"An alternative explanation for the concept (option {index + 1})"
    
    def _find_context_sentences(self, term: str, text: str) -> List[str]:
        """Find sentences that provide context about how a term is used"""
        context_sentences = []
        text_sentences = sentences(text)
        
        for sentence in text_sentences:
            if term.lower() in sentence.lower():
                # Look for application indicators
                app_indicators = ['used', 'applied', 'implemented', 'utilized', 'employed', 
                                'helps', 'enables', 'allows', 'provides', 'supports']
                
                if any(indicator in sentence.lower() for indicator in app_indicators):
                    context_sentences.append(sentence)
        
        return context_sentences
    
    def _extract_application_context(self, context_sentences: List[str], term: str) -> str:
        """Extract application context from sentences"""
        # Simple extraction - look for phrases after application indicators
        for sentence in context_sentences:
            sentence_lower = sentence.lower()
            term_lower = term.lower()
            
            # Find where the term appears and what follows
            if f"{term_lower} is used" in sentence_lower:
                parts = sentence_lower.split(f"{term_lower} is used", 1)
                if len(parts) > 1:
                    return f"Used {parts[1].strip()[:100]}..."
            
            elif f"{term_lower} helps" in sentence_lower:
                parts = sentence_lower.split(f"{term_lower} helps", 1)
                if len(parts) > 1:
                    return f"Helps {parts[1].strip()[:100]}..."
        
        # Default to first context sentence
        return context_sentences[0][:150] + "..." if context_sentences else ""
    
    def _find_similar_terms(self, card: Dict, all_cards: List[Dict]) -> List[Dict]:
        """Find terms similar to the given card's term"""
        target_words = set(card["answer"].lower().split())
        similar_terms = []
        
        for other_card in all_cards:
            if other_card["term"] == card["term"]:
                continue
                
            other_words = set(other_card["answer"].lower().split())
            similarity = len(target_words.intersection(other_words)) / len(target_words.union(other_words))
            
            if similarity > 0.2:  # Some similarity but not identical
                similar_terms.append({
                    "card": other_card,
                    "similarity": similarity
                })
        
        # Sort by similarity and return top ones
        similar_terms.sort(key=lambda x: x["similarity"], reverse=True)
        return [item["card"] for item in similar_terms[:3]]
    
    def _create_comparison_answer(self, original_answer: str, similar_terms: List[Dict]) -> str:
        """Create an answer that emphasizes distinguishing features"""
        # Extract key distinguishing words
        original_words = set(original_answer.lower().split())
        
        # Find words that are unique to this answer
        unique_words = original_words.copy()
        for similar_card in similar_terms:
            similar_words = set(similar_card["answer"].lower().split())
            unique_words -= similar_words
        
        if unique_words:
            # Emphasize unique aspects
            unique_phrase = " ".join(list(unique_words)[:3])
            return f"{original_answer[:100]}... (Distinguished by: {unique_phrase})"
        
        return original_answer
    
    def _generate_comparison_distractors(self, correct_answer: str, similar_terms: List[Dict], 
                                        difficulty_level: int) -> List[str]:
        """Generate distractors for comparison questions"""
        distractors = []
        
        # Use similar terms as basis for distractors
        for similar_card in similar_terms[:3]:
            if len(distractors) >= 3:
                break
                
            # Modify the similar answer to make it a plausible but wrong comparison
            modified_answer = self._modify_for_comparison_distractor(
                similar_card["answer"], difficulty_level
            )
            distractors.append(modified_answer)
        
        return distractors
    
    def _modify_for_comparison_distractor(self, answer: str, difficulty_level: int) -> str:
        """Modify an answer to make it a comparison distractor"""
        if difficulty_level <= 2:
            # Easy: Obviously wrong comparison
            return f"{answer[:50]}... (This is clearly different)"
        else:
            # Hard: Subtle difference
            return f"{answer[:80]}... (Similar but distinct application)"
    
    def _find_cause_effect_context(self, term: str, text: str) -> str:
        """Find cause-effect relationships involving the term"""
        text_sentences = sentences(text)
        cause_effect_indicators = [
            'causes', 'results in', 'leads to', 'produces', 'creates',
            'due to', 'because of', 'results from', 'caused by'
        ]
        
        for sentence in text_sentences:
            if term.lower() in sentence.lower():
                for indicator in cause_effect_indicators:
                    if indicator in sentence.lower():
                        return sentence[:200] + "..."
        
        return ""
    
    def _generate_cause_effect_distractors(self, correct_context: str, difficulty_level: int) -> List[str]:
        """Generate distractors for cause-effect questions"""
        # This is a simplified implementation
        # In practice, you'd want more sophisticated cause-effect distractor generation
        generic_distractors = [
            "Has no significant impact on related processes",
            "Primarily affects unrelated systems",
            "Results in opposite effects from what might be expected"
        ]
        
        return generic_distractors
    
    def _generate_variety_questions(self, text: str, needed_count: int, 
                                   difficulty_level: int, used_terms: Set[str]) -> List[Dict]:
        """Generate additional variety questions from the text"""
        variety_questions = []
        
        # Extract additional concepts that weren't used
        additional_cards = extract_flashcards(text, max_cards=needed_count * 2)
        
        for card in additional_cards:
            if len(variety_questions) >= needed_count:
                break
                
            if card["term"].lower() not in used_terms:
                question = self._create_definition_question(card, difficulty_level, additional_cards)
                if question:
                    variety_questions.append(question)
                    used_terms.add(card["term"].lower())
        
        return variety_questions
    
    def _build_question_dict(self, question_text: str, correct_answer: str, 
                            distractors: List[str], difficulty_level: int,
                            question_type: str, term: str, quality_score: float) -> Dict:
        """Build the final question dictionary"""
        
        # Create choices and shuffle
        choices = distractors + [correct_answer]
        random.shuffle(choices)
        
        # Calculate estimated time based on difficulty and complexity
        base_time = 30  # seconds
        time_multiplier = {1: 0.7, 2: 0.8, 3: 1.0, 4: 1.3, 5: 1.6}
        estimated_time = int(base_time * time_multiplier.get(difficulty_level, 1.0))
        
        return {
            "id": hashlib.md5(f"{question_text}{correct_answer}".encode()).hexdigest()[:8],
            "question": question_text,
            "choices": choices,
            "answer": correct_answer,
            "term": term,
            "difficulty_level": difficulty_level,
            "question_type": question_type,
            "estimated_time": estimated_time,
            "quality_score": round(quality_score, 2),
            "metadata": {
                "difficulty_name": self.difficulty_modifiers[difficulty_level]["name"],
                "complexity": self.difficulty_modifiers[difficulty_level]["complexity"]
            }
        }

# Function to maintain backward compatibility with existing code
def build_quiz(text: str, max_qs: int = 5) -> List[Dict]:
    """Backward compatible quiz building function"""
    quiz_service = EnhancedQuizService()
    return quiz_service.build_quiz(text, max_qs)
