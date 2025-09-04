"""
Flashcard generation service using NLP and AI models.
"""

import logging
import re
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

import spacy
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.tag import pos_tag

from app.services.model_manager import ModelManager
from app.core.config import settings

logger = logging.getLogger(__name__)


class FlashcardService:
    """Service for generating flashcards from text."""
    
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.nlp = model_manager.get_model("spacy")
        self.stop_words = set(stopwords.words('english'))
    
    async def generate_flashcards(
        self, 
        text: str, 
        max_cards: int = 10,
        difficulty_level: str = "medium",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate flashcards from input text.
        
        Args:
            text: Input text to generate flashcards from
            max_cards: Maximum number of flashcards to generate
            difficulty_level: Difficulty level (easy, medium, hard)
            session_id: Optional session ID for tracking
            
        Returns:
            Dictionary containing flashcards and metadata
        """
        try:
            start_time = datetime.now()
            
            # Validate input
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")
            
            if len(text) > settings.MAX_TEXT_LENGTH:
                raise ValueError(f"Text too long. Maximum {settings.MAX_TEXT_LENGTH} characters allowed")
            
            if not (1 <= max_cards <= 50):
                raise ValueError("max_cards must be between 1 and 50")
            
            # Process text with spaCy
            doc = self.nlp(text)
            
            # Extract key concepts and definitions
            flashcards = await self._extract_flashcards(doc, max_cards, difficulty_level)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Calculate quality scores
            for card in flashcards:
                card["quality_score"] = self._calculate_quality_score(card)
            
            # Sort by quality score
            flashcards.sort(key=lambda x: x["quality_score"], reverse=True)
            
            # Prepare response
            result = {
                "count": len(flashcards),
                "cards": flashcards,
                "metadata": {
                    "difficulty_level": difficulty_level,
                    "avg_quality_score": round(
                        sum(card["quality_score"] for card in flashcards) / max(len(flashcards), 1), 2
                    ),
                    "processing_time": processing_time,
                    "session_id": session_id
                }
            }
            
            logger.info(f"Generated {len(flashcards)} flashcards in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Flashcard generation failed: {e}")
            raise
    
    async def _extract_flashcards(
        self, 
        doc, 
        max_cards: int, 
        difficulty_level: str
    ) -> List[Dict[str, Any]]:
        """Extract flashcards from spaCy document."""
        flashcards = []
        
        # Extract named entities
        entities = self._extract_entities(doc)
        
        # Extract key terms and definitions
        terms_definitions = self._extract_terms_definitions(doc)
        
        # Extract concept relationships
        concepts = self._extract_concepts(doc)
        
        # Combine and process
        all_candidates = entities + terms_definitions + concepts
        
        # Filter and rank candidates
        filtered_cards = self._filter_and_rank_cards(all_candidates, difficulty_level)
        
        # Take top candidates
        flashcards = filtered_cards[:max_cards]
        
        return flashcards
    
    def _extract_entities(self, doc) -> List[Dict[str, Any]]:
        """Extract named entities as flashcard candidates."""
        entities = []
        
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE", "EVENT", "WORK_OF_ART", "LAW", "LANGUAGE"]:
                # Find context around the entity
                context = self._get_entity_context(doc, ent)
                
                entities.append({
                    "term": ent.text,
                    "definition": context,
                    "type": "entity",
                    "difficulty": self._assess_difficulty(ent.text, context)
                })
        
        return entities
    
    def _extract_terms_definitions(self, doc) -> List[Dict[str, Any]]:
        """Extract terms and their definitions from text."""
        terms_definitions = []
        
        # Look for definition patterns
        definition_patterns = [
            r"(\w+(?:\s+\w+)*)\s+is\s+(?:a|an|the)?\s*([^.]*)",
            r"(\w+(?:\s+\w+)*)\s+refers\s+to\s+([^.]*)",
            r"(\w+(?:\s+\w+)*)\s+means\s+([^.]*)",
            r"(\w+(?:\s+\w+)*)\s+can\s+be\s+defined\s+as\s+([^.]*)"
        ]
        
        text = doc.text
        for pattern in definition_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                term = match.group(1).strip()
                definition = match.group(2).strip()
                
                if len(term) > 2 and len(definition) > 10:
                    terms_definitions.append({
                        "term": term,
                        "definition": definition,
                        "type": "definition",
                        "difficulty": self._assess_difficulty(term, definition)
                    })
        
        return terms_definitions
    
    def _extract_concepts(self, doc) -> List[Dict[str, Any]]:
        """Extract key concepts from text."""
        concepts = []
        
        # Extract noun phrases
        noun_phrases = [chunk.text for chunk in doc.noun_chunks if len(chunk.text.split()) <= 4]
        
        # Extract important terms (nouns, proper nouns)
        important_terms = []
        for token in doc:
            if (token.pos_ in ["NOUN", "PROPN"] and 
                not token.is_stop and 
                not token.is_punct and 
                len(token.text) > 2):
                important_terms.append(token.text)
        
        # Create concept cards
        for term in set(important_terms + noun_phrases):
            if len(term) > 2:
                context = self._get_term_context(doc, term)
                if context:
                    concepts.append({
                        "term": term,
                        "definition": context,
                        "type": "concept",
                        "difficulty": self._assess_difficulty(term, context)
                    })
        
        return concepts
    
    def _get_entity_context(self, doc, entity) -> str:
        """Get context around an entity."""
        start = max(0, entity.start - 20)
        end = min(len(doc), entity.end + 20)
        context = doc[start:end].text
        return context.strip()
    
    def _get_term_context(self, doc, term) -> str:
        """Get context around a term."""
        sentences = sent_tokenize(doc.text)
        for sentence in sentences:
            if term.lower() in sentence.lower():
                return sentence.strip()
        return ""
    
    def _assess_difficulty(self, term: str, definition: str) -> int:
        """Assess difficulty level of a flashcard (1-5 scale)."""
        score = 1
        
        # Term length
        if len(term.split()) > 2:
            score += 1
        
        # Definition complexity
        if len(definition.split()) > 20:
            score += 1
        
        # Technical terms
        technical_indicators = ["system", "process", "method", "technique", "algorithm", "function"]
        if any(indicator in definition.lower() for indicator in technical_indicators):
            score += 1
        
        # Special characters or numbers
        if re.search(r'[^\w\s]', term) or re.search(r'\d', term):
            score += 1
        
        return min(score, 5)
    
    def _filter_and_rank_cards(
        self, 
        candidates: List[Dict[str, Any]], 
        difficulty_level: str
    ) -> List[Dict[str, Any]]:
        """Filter and rank flashcard candidates."""
        # Remove duplicates
        seen_terms = set()
        unique_cards = []
        
        for card in candidates:
            term_lower = card["term"].lower()
            if term_lower not in seen_terms:
                seen_terms.add(term_lower)
                unique_cards.append(card)
        
        # Filter by difficulty
        difficulty_map = {"easy": (1, 2), "medium": (2, 4), "hard": (3, 5)}
        min_diff, max_diff = difficulty_map.get(difficulty_level, (1, 5))
        
        filtered_cards = [
            card for card in unique_cards 
            if min_diff <= card["difficulty"] <= max_diff
        ]
        
        # Sort by quality (term length, definition quality, etc.)
        filtered_cards.sort(key=lambda x: (
            len(x["definition"]),
            len(x["term"]),
            x["difficulty"]
        ), reverse=True)
        
        return filtered_cards
    
    def _calculate_quality_score(self, card: Dict[str, Any]) -> float:
        """Calculate quality score for a flashcard (0.0-1.0)."""
        score = 0.0
        
        # Term quality
        term = card["term"]
        if 2 <= len(term.split()) <= 4:
            score += 0.3
        
        # Definition quality
        definition = card["definition"]
        if 10 <= len(definition.split()) <= 50:
            score += 0.4
        
        # Clarity indicators
        clarity_words = ["is", "are", "refers", "means", "defined", "example"]
        if any(word in definition.lower() for word in clarity_words):
            score += 0.2
        
        # Completeness
        if len(definition) > len(term) * 2:
            score += 0.1
        
        return min(score, 1.0)
