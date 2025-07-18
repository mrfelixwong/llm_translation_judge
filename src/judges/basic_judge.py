"""
Basic Judge: Technique 1 - Simple prompt baseline.

This represents the most basic approach to using an LLM as a judge,
with minimal prompting and no structured guidance.
"""

from typing import Dict, Any
from .base_judge import BaseJudge


class BasicJudge(BaseJudge):
    """
    Basic LLM judge with minimal prompting.
    
    This serves as the baseline for comparison. It uses a simple,
    unstructured prompt that asks for a translation quality score
    without providing examples or detailed criteria.
    
    Expected Performance:
    - High variance in scoring
    - Inconsistent criteria application
    - Difficulty with edge cases
    - Subjective, non-reproducible judgments
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.judge_name = "Basic Judge"
        self.technique = "Basic Prompt"
    
    def evaluate(
        self,
        source_text: str,
        translated_text: str,
        source_lang: str = "en",
        target_lang: str = "auto"
    ) -> Dict[str, Any]:
        """
        Evaluate translation using basic prompting.
        
        Args:
            source_text: Original text
            translated_text: Translation to evaluate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Dictionary containing:
            - overall_score: 1-5 rating
            - notes: Brief explanation
            - technique: Method used
        """
        
        # Basic prompt - minimal guidance
        prompt = f"""Rate the quality of this translation on a scale from 1 to 5, where:
1 = Very Poor
2 = Poor  
3 = Average
4 = Good
5 = Excellent

Original text: {source_text}
Translation: {translated_text}

Provide your rating and a brief explanation."""

        messages = [
            {
                "role": "system", 
                "content": "You are a translation quality evaluator. Provide honest, objective assessments."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
        
        response = self._call_llm(messages)
        
        # Parse the response - basic judge doesn't enforce structure
        parsed_result = self._parse_basic_response(response)
        
        # Add metadata
        parsed_result.update({
            "technique": self.technique,
            "judge_name": self.judge_name,
            "source_text": source_text,
            "translated_text": translated_text,
            "raw_response": response
        })
        
        return parsed_result
    
    def _parse_basic_response(self, response: str) -> Dict[str, Any]:
        """
        Parse unstructured response from basic judge.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Structured result dictionary
        """
        import re
        
        # Try to extract numerical score
        score_patterns = [
            r'rating?:?\s*([1-5])',
            r'score:?\s*([1-5])',
            r'\b([1-5])\s*\/\s*5',
            r'\b([1-5])\s*out of 5',
            r'^([1-5])',  # Score at beginning
        ]
        
        score = 3  # Default to middle score
        for pattern in score_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                try:
                    score = int(match.group(1))
                    break
                except (ValueError, IndexError):
                    continue
        
        # Extract explanation (everything after the score)
        explanation = response
        
        # Try to separate score line from explanation
        lines = response.strip().split('\n')
        if len(lines) > 1:
            # Find line with score and use subsequent lines as explanation
            for i, line in enumerate(lines):
                if any(re.search(pattern, line, re.IGNORECASE) for pattern in score_patterns):
                    if i + 1 < len(lines):
                        explanation = '\n'.join(lines[i+1:]).strip()
                    break
        
        if not explanation or explanation == response:
            explanation = "No detailed explanation provided."
        
        return {
            "overall_score": score,
            "notes": explanation,
            "confidence": "low",  # Basic judge provides no confidence measure
            "methodology": "unstructured_evaluation"
        }


# Example usage and testing
if __name__ == "__main__":
    # Test the basic judge
    judge = BasicJudge()
    
    test_cases = [
        {
            "source": "Hello, how are you today?",
            "translation": "Bonjour, comment allez-vous aujourd'hui?"
        },
        {
            "source": "The meeting is scheduled for next Tuesday.",
            "translation": "La reunión está programada para el próximo domingo."  # Wrong day
        },
        {
            "source": "Please send the report by end of day.",
            "translation": "Veuillez envoyer le rapport avant la fin de la journée."
        }
    ]
    
    print(f"Testing {judge.judge_name}")
    print("=" * 50)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Source: {case['source']}")
        print(f"Translation: {case['translation']}")
        
        result = judge.evaluate(case['source'], case['translation'])
        
        print(f"Score: {result['overall_score']}/5")
        print(f"Notes: {result['notes']}")
        print("-" * 30)
    
    # Show usage statistics
    stats = judge.get_usage_stats()
    print(f"\nUsage Statistics:")
    print(f"Total API calls: {stats['total_calls']}")
    print(f"Total tokens: {stats['total_tokens']}")
    print(f"Estimated cost: ${stats['estimated_cost']:.4f}")