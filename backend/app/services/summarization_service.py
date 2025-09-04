"""
Text summarization service using T5 model.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import torch

from app.services.model_manager import ModelManager
from app.core.config import settings

logger = logging.getLogger(__name__)


class SummarizationService:
    """Service for text summarization using T5 model."""
    
    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
    
    async def summarize_text(
        self, 
        text: str, 
        min_length: int = 40, 
        max_length: int = 140,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Summarize input text using T5 model.
        
        Args:
            text: Input text to summarize
            min_length: Minimum length of summary
            max_length: Maximum length of summary
            session_id: Optional session ID for tracking
            
        Returns:
            Dictionary containing summary and metadata
        """
        try:
            start_time = datetime.now()
            
            # Validate input
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")
            
            if len(text) > settings.MAX_TEXT_LENGTH:
                raise ValueError(f"Text too long. Maximum {settings.MAX_TEXT_LENGTH} characters allowed")
            
            if max_length <= min_length:
                raise ValueError("max_length must be greater than min_length")
            
            # Get model
            model_data = self.model_manager.get_model("summarization")
            if not model_data:
                raise RuntimeError("Summarization model not loaded")
            
            model = model_data["model"]
            tokenizer = model_data["tokenizer"]
            
            # Prepare input
            input_text = f"summarize: {text}"
            inputs = tokenizer(
                input_text,
                max_length=512,
                truncation=True,
                padding=True,
                return_tensors="pt"
            ).to(model.device)
            
            # Generate summary
            with torch.no_grad():
                outputs = model.generate(
                    inputs.input_ids,
                    max_length=max_length,
                    min_length=min_length,
                    num_beams=4,
                    early_stopping=True,
                    do_sample=False
                )
            
            # Decode output
            summary = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Prepare response
            result = {
                "summary": summary,
                "metadata": {
                    "model": "t5-small",
                    "input_length": len(text),
                    "summary_length": len(summary),
                    "compression_ratio": round(len(summary) / len(text), 2),
                    "processing_time": processing_time,
                    "session_id": session_id
                }
            }
            
            logger.info(f"Summarization completed in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            raise
    
    async def batch_summarize(
        self, 
        texts: list[str], 
        min_length: int = 40, 
        max_length: int = 140
    ) -> list[Dict[str, Any]]:
        """
        Summarize multiple texts in batch.
        
        Args:
            texts: List of texts to summarize
            min_length: Minimum length of summaries
            max_length: Maximum length of summaries
            
        Returns:
            List of summarization results
        """
        results = []
        
        for text in texts:
            try:
                result = await self.summarize_text(text, min_length, max_length)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to summarize text: {e}")
                results.append({
                    "summary": "",
                    "error": str(e),
                    "metadata": {"input_length": len(text)}
                })
        
        return results
