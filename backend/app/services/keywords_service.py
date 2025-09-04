"""
Keywords extraction service using NLP and AI models.
"""

import logging
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import Counter

import spacy
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from app.services.model_manager import ModelManager
from app.core.config import settings

logger = logging.getLogger(__name__)


class KeywordsService:
    """Service for extracting keywords from text."""
    
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.nlp = model_manager.get_model("spacy")
        self.stop_words = set(stopwords.words('english'))
    
    async def extract_keywords(
        self, 
        text: str, 
        top_k: int = 10,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract keywords from input text.
        
        Args:
            text: Input text to extract keywords from
            top_k: Number of top keywords to extract
            session_id: Optional session ID for tracking
            
        Returns:
            Dictionary containing keywords and metadata
        """
        try:
            start_time = datetime.now()
            
            # Validate input
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")
            
            if len(text) > settings.MAX_TEXT_LENGTH:
                raise ValueError(f"Text too long. Maximum {settings.MAX_TEXT_LENGTH} characters allowed")
            
            if not (1 <= top_k <= 50):
                raise ValueError("top_k must be between 1 and 50")
            
            # Process text with spaCy
            doc = self.nlp(text)
            
            # Extract keywords using multiple methods
            keywords = await self._extract_keywords_multiple_methods(doc, top_k)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Prepare response
            result = {
                "count": len(keywords),
                "keywords": keywords,
                "metadata": {
                    "session_id": session_id,
                    "extraction_method": "combined",
                    "processing_time": processing_time
                }
            }
            
            logger.info(f"Extracted {len(keywords)} keywords in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            raise
    
    async def _extract_keywords_multiple_methods(
        self, 
        doc, 
        top_k: int
    ) -> List[str]:
        """Extract keywords using multiple methods and combine results."""
        
        # Method 1: Named Entity Recognition
        entity_keywords = self._extract_entity_keywords(doc)
        
        # Method 2: TF-IDF based extraction
        tfidf_keywords = self._extract_tfidf_keywords(doc, top_k)
        
        # Method 3: POS-based extraction
        pos_keywords = self._extract_pos_keywords(doc)
        
        # Method 4: Noun phrase extraction
        noun_phrase_keywords = self._extract_noun_phrase_keywords(doc)
        
        # Combine and rank all keywords
        all_keywords = entity_keywords + tfidf_keywords + pos_keywords + noun_phrase_keywords
        
        # Count frequency and rank
        keyword_counts = Counter(all_keywords)
        
        # Filter and sort
        filtered_keywords = self._filter_and_rank_keywords(keyword_counts, top_k)
        
        return filtered_keywords
    
    def _extract_entity_keywords(self, doc) -> List[str]:
        """Extract keywords from named entities."""
        keywords = []
        
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG", "GPE", "EVENT", "WORK_OF_ART", "LAW", "LANGUAGE", "PRODUCT"]:
                # Clean and validate entity
                entity_text = ent.text.strip()
                if len(entity_text) > 2 and not entity_text.lower() in self.stop_words:
                    keywords.append(entity_text)
        
        return keywords
    
    def _extract_tfidf_keywords(self, doc, top_k: int) -> List[str]:
        """Extract keywords using TF-IDF."""
        if not SKLEARN_AVAILABLE:
            return []
        
        try:
            # Split text into sentences
            sentences = [sent.text for sent in doc.sents if len(sent.text.strip()) > 10]
            
            if len(sentences) < 2:
                return []
            
            # Create TF-IDF vectorizer
            vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.8
            )
            
            # Fit and transform
            tfidf_matrix = vectorizer.fit_transform(sentences)
            feature_names = vectorizer.get_feature_names_out()
            
            # Get mean TF-IDF scores
            mean_scores = np.mean(tfidf_matrix.toarray(), axis=0)
            
            # Get top keywords
            top_indices = np.argsort(mean_scores)[-top_k*2:][::-1]  # Get more than needed for filtering
            keywords = [feature_names[i] for i in top_indices if mean_scores[i] > 0]
            
            return keywords
            
        except Exception as e:
            logger.warning(f"TF-IDF extraction failed: {e}")
            return []
    
    def _extract_pos_keywords(self, doc) -> List[str]:
        """Extract keywords based on part-of-speech tags."""
        keywords = []
        
        for token in doc:
            # Focus on nouns, proper nouns, and adjectives
            if (token.pos_ in ["NOUN", "PROPN", "ADJ"] and 
                not token.is_stop and 
                not token.is_punct and 
                not token.is_space and
                len(token.text) > 2 and
                token.text.isalpha()):
                
                keywords.append(token.text)
        
        return keywords
    
    def _extract_noun_phrase_keywords(self, doc) -> List[str]:
        """Extract keywords from noun phrases."""
        keywords = []
        
        for chunk in doc.noun_chunks:
            # Filter noun phrases
            if (len(chunk.text.split()) <= 3 and  # Not too long
                len(chunk.text) > 2 and  # Not too short
                not any(token.is_stop for token in chunk) and  # No stop words
                chunk.text.isalpha()):  # Only alphabetic
                
                keywords.append(chunk.text)
        
        return keywords
    
    def _filter_and_rank_keywords(self, keyword_counts: Counter, top_k: int) -> List[str]:
        """Filter and rank keywords by frequency and quality."""
        
        # Filter keywords
        filtered_keywords = []
        
        for keyword, count in keyword_counts.most_common():
            # Skip if too common or too rare
            if count < 1:
                continue
            
            # Skip very short or very long keywords
            if len(keyword) < 2 or len(keyword) > 50:
                continue
            
            # Skip if mostly numbers or special characters
            if not re.search(r'[a-zA-Z]', keyword):
                continue
            
            # Skip common words that might have slipped through
            if keyword.lower() in ['text', 'content', 'information', 'data', 'study', 'research']:
                continue
            
            filtered_keywords.append(keyword)
        
        # Return top k keywords
        return filtered_keywords[:top_k]
