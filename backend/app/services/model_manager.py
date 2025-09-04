"""
Model management service for loading and managing AI models.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path

import torch
from transformers import (
    T5ForConditionalGeneration, T5Tokenizer,
    BlipProcessor, BlipForConditionalGeneration,
    pipeline
)
import spacy
import nltk

from app.core.config import settings

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages loading and caching of AI models."""
    
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.device = self._get_device()
        self.cache_dir = Path(settings.HUGGINGFACE_CACHE_DIR)
        self.cache_dir.mkdir(exist_ok=True)
        
    def _get_device(self) -> str:
        """Determine the best available device."""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
    
    async def load_models(self):
        """Load all required models asynchronously."""
        logger.info(f"Loading models on device: {self.device}")
        
        # Load models in parallel
        tasks = [
            self._load_summarization_model(),
            self._load_paraphrase_model(),
            self._load_visual_qa_model(),
            self._load_nlp_models()
        ]
        
        await asyncio.gather(*tasks)
        logger.info("All models loaded successfully")
    
    async def _load_summarization_model(self):
        """Load T5 summarization model."""
        try:
            logger.info("Loading T5 summarization model...")
            
            model_name = "t5-small"
            tokenizer = T5Tokenizer.from_pretrained(
                model_name, 
                cache_dir=self.cache_dir
            )
            model = T5ForConditionalGeneration.from_pretrained(
                model_name,
                cache_dir=self.cache_dir
            ).to(self.device)
            
            self.models["summarization"] = {
                "model": model,
                "tokenizer": tokenizer,
                "type": "t5"
            }
            
            logger.info("T5 summarization model loaded")
            
        except Exception as e:
            logger.error(f"Failed to load summarization model: {e}")
            raise
    
    async def _load_paraphrase_model(self):
        """Load T5 paraphrase model."""
        try:
            logger.info("Loading T5 paraphrase model...")
            
            model_name = "t5-small"
            tokenizer = T5Tokenizer.from_pretrained(
                model_name,
                cache_dir=self.cache_dir
            )
            model = T5ForConditionalGeneration.from_pretrained(
                model_name,
                cache_dir=self.cache_dir
            ).to(self.device)
            
            self.models["paraphrase"] = {
                "model": model,
                "tokenizer": tokenizer,
                "type": "t5"
            }
            
            logger.info("T5 paraphrase model loaded")
            
        except Exception as e:
            logger.error(f"Failed to load paraphrase model: {e}")
            raise
    
    async def _load_visual_qa_model(self):
        """Load BLIP visual QA model."""
        try:
            logger.info("Loading BLIP visual QA model...")
            
            model_name = "Salesforce/blip-image-captioning-base"
            processor = BlipProcessor.from_pretrained(
                model_name,
                cache_dir=self.cache_dir
            )
            model = BlipForConditionalGeneration.from_pretrained(
                model_name,
                cache_dir=self.cache_dir
            ).to(self.device)
            
            self.models["visual_qa"] = {
                "model": model,
                "processor": processor,
                "type": "blip"
            }
            
            logger.info("BLIP visual QA model loaded")
            
        except Exception as e:
            logger.error(f"Failed to load visual QA model: {e}")
            raise
    
    async def _load_nlp_models(self):
        """Load NLP models (spaCy, NLTK)."""
        try:
            logger.info("Loading NLP models...")
            
            # Load spaCy model
            try:
                nlp = spacy.load("en_core_web_sm")
                self.models["spacy"] = nlp
                logger.info("spaCy model loaded")
            except OSError:
                logger.warning("spaCy model not found, downloading...")
                spacy.cli.download("en_core_web_sm")
                nlp = spacy.load("en_core_web_sm")
                self.models["spacy"] = nlp
                logger.info("spaCy model downloaded and loaded")
            
            # Download NLTK data
            try:
                nltk.data.find('tokenizers/punkt')
                nltk.data.find('corpora/stopwords')
            except LookupError:
                logger.info("Downloading NLTK data...")
                nltk.download('punkt', quiet=True)
                nltk.download('stopwords', quiet=True)
                nltk.download('averaged_perceptron_tagger', quiet=True)
            
            logger.info("NLP models loaded")
            
        except Exception as e:
            logger.error(f"Failed to load NLP models: {e}")
            raise
    
    def get_model(self, model_type: str) -> Optional[Dict[str, Any]]:
        """Get a loaded model by type."""
        return self.models.get(model_type)
    
    async def cleanup(self):
        """Cleanup models and free memory."""
        logger.info("Cleaning up models...")
        
        for model_type, model_data in self.models.items():
            if isinstance(model_data, dict) and "model" in model_data:
                del model_data["model"]
            elif hasattr(model_data, "to"):
                del model_data
        
        self.models.clear()
        
        # Clear CUDA cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("Model cleanup complete")
