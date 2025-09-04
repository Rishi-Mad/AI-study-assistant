"""
Quiz generation service using NLP and AI models.
"""

import logging
import re
import random
from typing import Dict, Any, List, Optional
from datetime import datetime

import spacy
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

from app.services.model_manager import ModelManager
from app.core.config import settings

logger = logging.getLogger(__name__)


class QuizService:
    """Service for generating quiz questions from text."""
    
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.nlp = model_manager.get_model("spacy")
        self.stop_words = set(stopwords.words('english'))
    
    async def generate_quiz(
        self, 
        text: str, 
        max_questions: int = 5,
        difficulty_level: str = "medium",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate quiz questions from input text.
        
        Args:
            text: Input text to generate quiz from
            max_questions: Maximum number of questions to generate
            difficulty_level: Difficulty level (easy, medium, hard)
            session_id: Optional session ID for tracking
            
        Returns:
            Dictionary containing quiz questions and metadata
        """
        try:
            start_time = datetime.now()
            
            # Validate input
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")
            
            if len(text) > settings.MAX_TEXT_LENGTH:
                raise ValueError(f"Text too long. Maximum {settings.MAX_TEXT_LENGTH} characters allowed")
            
            if not (1 <= max_questions <= 20):
                raise ValueError("max_questions must be between 1 and 20")
            
            # Process text with spaCy
            doc = self.nlp(text)
            
            # Extract key information for questions
            questions = await self._generate_questions(doc, max_questions, difficulty_level)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Prepare response
            result = {
                "count": len(questions),
                "questions": questions,
                "metadata": {
                    "difficulty_level": difficulty_level,
                    "processing_time": processing_time,
                    "session_id": session_id
                }
            }
            
            logger.info(f"Generated {len(questions)} quiz questions in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Quiz generation failed: {e}")
            raise
    
    async def _generate_questions(
        self, 
        doc, 
        max_questions: int, 
        difficulty_level: str
    ) -> List[Dict[str, Any]]:
        """Generate quiz questions from spaCy document."""
        questions = []
        
        # Extract sentences for question generation
        sentences = sent_tokenize(doc.text)
        
        # Extract key entities and concepts
        entities = [ent.text for ent in doc.ents if ent.label_ in ["PERSON", "ORG", "GPE", "EVENT"]]
        important_terms = [token.text for token in doc if token.pos_ in ["NOUN", "PROPN"] and not token.is_stop]
        
        # Generate different types of questions
        question_types = ["definition", "factual", "conceptual", "application"]
        
        for i in range(max_questions):
            if i < len(sentences):
                sentence = sentences[i]
                question_type = question_types[i % len(question_types)]
                
                question = self._create_question(sentence, question_type, entities, important_terms, difficulty_level)
                if question:
                    questions.append(question)
        
        return questions
    
    def _create_question(
        self, 
        sentence: str, 
        question_type: str, 
        entities: List[str], 
        terms: List[str], 
        difficulty_level: str
    ) -> Optional[Dict[str, Any]]:
        """Create a specific type of question from a sentence."""
        
        if question_type == "definition":
            return self._create_definition_question(sentence, terms, difficulty_level)
        elif question_type == "factual":
            return self._create_factual_question(sentence, entities, difficulty_level)
        elif question_type == "conceptual":
            return self._create_conceptual_question(sentence, terms, difficulty_level)
        elif question_type == "application":
            return self._create_application_question(sentence, difficulty_level)
        
        return None
    
    def _create_definition_question(self, sentence: str, terms: List[str], difficulty_level: str) -> Optional[Dict[str, Any]]:
        """Create a definition-based question."""
        # Find terms that might need definition
        important_terms = [term for term in terms if len(term) > 3 and term.lower() not in self.stop_words]
        
        if not important_terms:
            return None
        
        term = random.choice(important_terms)
        
        # Create question
        question = f"What is {term}?"
        
        # Generate options
        correct_answer = self._extract_definition_for_term(sentence, term)
        if not correct_answer:
            correct_answer = f"{term} is mentioned in the context of: {sentence[:100]}..."
        
        # Generate distractors
        distractors = self._generate_distractors(terms, term)
        options = [correct_answer] + distractors[:3]
        random.shuffle(options)
        
        return {
            "question": question,
            "options": options,
            "correct_answer": correct_answer,
            "explanation": f"According to the text, {correct_answer}",
            "difficulty": self._assess_question_difficulty(question, correct_answer, difficulty_level)
        }
    
    def _create_factual_question(self, sentence: str, entities: List[str], difficulty_level: str) -> Optional[Dict[str, Any]]:
        """Create a factual question."""
        if not entities:
            return None
        
        entity = random.choice(entities)
        
        # Create question
        question = f"Which of the following is mentioned in relation to {entity}?"
        
        # Extract context around entity
        context = self._extract_context_for_entity(sentence, entity)
        correct_answer = context if context else f"{entity} is discussed in the text"
        
        # Generate distractors
        other_entities = [e for e in entities if e != entity]
        distractors = [f"{entity} is not related to {e}" for e in other_entities[:3]]
        
        options = [correct_answer] + distractors
        random.shuffle(options)
        
        return {
            "question": question,
            "options": options,
            "correct_answer": correct_answer,
            "explanation": f"The text states: {correct_answer}",
            "difficulty": self._assess_question_difficulty(question, correct_answer, difficulty_level)
        }
    
    def _create_conceptual_question(self, sentence: str, terms: List[str], difficulty_level: str) -> Optional[Dict[str, Any]]:
        """Create a conceptual question."""
        # Find key concepts
        concepts = [term for term in terms if len(term.split()) <= 2 and term.lower() not in self.stop_words]
        
        if not concepts:
            return None
        
        concept = random.choice(concepts)
        
        # Create question
        question = f"What is the main concept discussed regarding {concept}?"
        
        # Extract main idea
        correct_answer = self._extract_main_idea(sentence)
        if not correct_answer:
            correct_answer = f"The text discusses {concept} in the context of: {sentence[:80]}..."
        
        # Generate distractors
        distractors = [
            f"{concept} is not important",
            f"{concept} is unrelated to the topic",
            f"{concept} is only mentioned briefly"
        ]
        
        options = [correct_answer] + distractors
        random.shuffle(options)
        
        return {
            "question": question,
            "options": options,
            "correct_answer": correct_answer,
            "explanation": f"The main concept is: {correct_answer}",
            "difficulty": self._assess_question_difficulty(question, correct_answer, difficulty_level)
        }
    
    def _create_application_question(self, sentence: str, difficulty_level: str) -> Optional[Dict[str, Any]]:
        """Create an application-based question."""
        # Create a "what would happen if" or "how would you apply" question
        question = "Based on the information provided, what would be the most likely outcome?"
        
        # Extract key information
        correct_answer = self._extract_key_information(sentence)
        if not correct_answer:
            correct_answer = "The information suggests a specific outcome based on the context"
        
        # Generate distractors
        distractors = [
            "The outcome would be completely different",
            "No clear outcome can be determined",
            "The outcome would be unpredictable"
        ]
        
        options = [correct_answer] + distractors
        random.shuffle(options)
        
        return {
            "question": question,
            "options": options,
            "correct_answer": correct_answer,
            "explanation": f"Based on the text: {correct_answer}",
            "difficulty": self._assess_question_difficulty(question, correct_answer, difficulty_level)
        }
    
    def _extract_definition_for_term(self, sentence: str, term: str) -> str:
        """Extract definition for a term from sentence."""
        # Look for definition patterns
        patterns = [
            rf"{re.escape(term)}\s+is\s+(?:a|an|the)?\s*([^.]*)",
            rf"{re.escape(term)}\s+refers\s+to\s+([^.]*)",
            rf"{re.escape(term)}\s+means\s+([^.]*)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _extract_context_for_entity(self, sentence: str, entity: str) -> str:
        """Extract context around an entity."""
        if entity.lower() in sentence.lower():
            # Return the sentence with some context
            return sentence.strip()
        return ""
    
    def _extract_main_idea(self, sentence: str) -> str:
        """Extract main idea from sentence."""
        # Simple extraction - take the first part of the sentence
        words = sentence.split()
        if len(words) > 10:
            return " ".join(words[:10]) + "..."
        return sentence
    
    def _extract_key_information(self, sentence: str) -> str:
        """Extract key information from sentence."""
        # Remove common words and return meaningful content
        words = [word for word in sentence.split() if word.lower() not in self.stop_words]
        if len(words) > 8:
            return " ".join(words[:8]) + "..."
        return sentence
    
    def _generate_distractors(self, terms: List[str], correct_term: str) -> List[str]:
        """Generate plausible distractors for multiple choice questions."""
        other_terms = [term for term in terms if term != correct_term]
        distractors = []
        
        for term in other_terms[:3]:
            distractors.append(f"{term} is a different concept")
        
        return distractors
    
    def _assess_question_difficulty(self, question: str, answer: str, target_difficulty: str) -> int:
        """Assess difficulty level of a question (1-5 scale)."""
        score = 1
        
        # Question complexity
        if len(question.split()) > 10:
            score += 1
        
        # Answer complexity
        if len(answer.split()) > 15:
            score += 1
        
        # Technical terms
        technical_indicators = ["system", "process", "method", "technique", "algorithm", "function", "analysis"]
        if any(indicator in question.lower() or indicator in answer.lower() for indicator in technical_indicators):
            score += 1
        
        # Abstract concepts
        abstract_indicators = ["concept", "theory", "principle", "framework", "model", "approach"]
        if any(indicator in question.lower() or indicator in answer.lower() for indicator in abstract_indicators):
            score += 1
        
        return min(score, 5)
