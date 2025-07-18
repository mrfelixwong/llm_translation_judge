"""
Base class for all LLM judges.

This provides the common interface and utilities shared across
all judge implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import json
import openai
from openai import OpenAI
import time


class BaseJudge(ABC):
    """
    Abstract base class for LLM judges.
    
    All judge implementations should inherit from this class
    and implement the evaluate method.
    """
    
    def __init__(
        self,
        model: str = "gpt-4",
        temperature: float = 0.2,
        max_retries: int = 3,
        api_key: Optional[str] = None
    ):
        """
        Initialize the base judge.
        
        Args:
            model: OpenAI model to use
            temperature: Sampling temperature
            max_retries: Number of API call retries
            api_key: OpenAI API key (if not in environment)
        """
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = OpenAI()  # Uses OPENAI_API_KEY from environment
        
        # Tracking for analysis
        self.total_calls = 0
        self.total_tokens = 0
        self.total_cost = 0.0
    
    @abstractmethod
    def evaluate(
        self,
        source_text: str,
        translated_text: str,
        source_lang: str = "en",
        target_lang: str = "auto"
    ) -> Dict[str, Any]:
        """
        Evaluate a translation.
        
        Args:
            source_text: Original text
            translated_text: Translation to evaluate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Dictionary containing evaluation results
        """
        pass
    
    def _call_llm(
        self,
        messages: list,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Make an API call to the LLM with retry logic.
        
        Args:
            messages: Chat messages for the API
            temperature: Override temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Response content string
        """
        if temperature is None:
            temperature = self.temperature
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                # Track usage
                self.total_calls += 1
                if hasattr(response, 'usage') and response.usage:
                    self.total_tokens += response.usage.total_tokens
                    # Rough cost calculation (adjust for actual pricing)
                    self.total_cost += response.usage.total_tokens * 0.00003
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise e
                time.sleep(2 ** attempt)  # Exponential backoff
        
        raise Exception("Failed to get response after all retries")
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON response from LLM, with fallback handling.
        
        Args:
            response: Raw response string
            
        Returns:
            Parsed JSON as dictionary
        """
        try:
            # Try to find JSON in the response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Fallback: create structured response from text
                return self._fallback_parse(response)
                
        except json.JSONDecodeError:
            return self._fallback_parse(response)
    
    def _fallback_parse(self, response: str) -> Dict[str, Any]:
        """
        Fallback parser when JSON parsing fails.
        
        Args:
            response: Raw response string
            
        Returns:
            Dictionary with basic structure
        """
        # Basic fallback - extract score if possible
        lines = response.strip().split('\n')
        
        result = {
            "overall_score": 3,  # Default middle score
            "notes": response,
            "parsing_error": True
        }
        
        # Try to extract any numbers that might be scores
        import re
        scores = re.findall(r'\b([1-5])\b', response)
        if scores:
            result["overall_score"] = int(scores[0])
        
        return result
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics for this judge.
        
        Returns:
            Dictionary with usage metrics
        """
        return {
            "total_calls": self.total_calls,
            "total_tokens": self.total_tokens,
            "estimated_cost": self.total_cost,
            "avg_tokens_per_call": self.total_tokens / max(1, self.total_calls)
        }
    
    def reset_stats(self):
        """Reset usage statistics."""
        self.total_calls = 0
        self.total_tokens = 0
        self.total_cost = 0.0