"""
Text paraphrasing service using T5 model.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import torch

from app.services.model_manager import ModelManager
from app.core.config import settings

logger = logging.getLogger(__name__)


class ParaphraseService:
    """Service for text paraphrasing using T5 model."""
    
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
    
    async def paraphrase_text(
        self, 
        text: str, 
        max_length: int = 128,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Paraphrase input text using T5 model.
        
        Args:
            text: Input text to paraphrase
            max_length: Maximum length of paraphrased text
            session_id: Optional session ID for tracking
            
        Returns:
            Dictionary containing paraphrased text and metadata
        """
        try:
            start_time = datetime.now()
            
            # Validate input
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")
            
            if len(text) > 1000:  # Limit for paraphrasing
                raise ValueError("Text too long for paraphrasing. Maximum 1000 characters allowed")
            
            if not (16 <= max_length <= 512):
                raise ValueError("max_length must be between 16 and 512")
            
            # Get model
            model_data = self.model_manager.get_model("paraphrase")
            if not model_data:
                raise RuntimeError("Paraphrase model not loaded")
            
            model = model_data["model"]
            tokenizer = model_data["tokenizer"]
            
            # Prepare input
            input_text = f"paraphrase: {text}"
            inputs = tokenizer(
                input_text,
                max_length=512,
                truncation=True,
                padding=True,
                return_tensors="pt"
            ).to(model.device)
            
            # Generate paraphrase
            with torch.no_grad():
                outputs = model.generate(
                    inputs.input_ids,
                    max_length=max_length,
                    min_length=16,
                    num_beams=4,
                    early_stopping=True,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9
                )
            
            # Decode output
            paraphrase = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Clean up the paraphrase
            paraphrase = self._clean_paraphrase(paraphrase, text)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Calculate length change
            length_change = len(paraphrase) - len(text)
            
            # Prepare response
            result = {
                "paraphrase": paraphrase,
                "metadata": {
                    "model": "t5-small",
                    "length_change": length_change,
                    "processing_time": processing_time,
                    "session_id": session_id
                }
            }
            
            logger.info(f"Paraphrasing completed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Paraphrasing failed: {e}")
            raise
    
    def _clean_paraphrase(self, paraphrase: str, original_text: str) -> str:
        """Clean and improve the generated paraphrase."""
        
        # Remove common prefixes that T5 might add
        prefixes_to_remove = [
            "paraphrase:",
            "paraphrased:",
            "rewritten:",
            "rephrased:",
            "alternative:"
        ]
        
        for prefix in prefixes_to_remove:
            if paraphrase.lower().startswith(prefix):
                paraphrase = paraphrase[len(prefix):].strip()
        
        # Ensure the paraphrase is different from original
        if paraphrase.lower().strip() == original_text.lower().strip():
            # If identical, try to make it slightly different
            paraphrase = f"An alternative way to express this: {paraphrase}"
        
        # Ensure proper capitalization
        if paraphrase and not paraphrase[0].isupper():
            paraphrase = paraphrase[0].upper() + paraphrase[1:]
        
        # Ensure it ends with proper punctuation
        if paraphrase and not paraphrase.endswith(('.', '!', '?')):
            paraphrase += '.'
        
        return paraphrase.strip()
