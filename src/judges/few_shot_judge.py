"""
Few-Shot Judge: Technique 2 - Learning from examples.

This judge uses few-shot learning to provide examples of good
and bad translations with their evaluations, teaching the LLM
what constitutes quality translation.
"""

from typing import Dict, Any, List
from .base_judge import BaseJudge


class FewShotJudge(BaseJudge):
    """
    Few-shot LLM judge with example-based learning.
    
    Provides 3-5 carefully selected examples that demonstrate:
    - What constitutes excellent, good, average, poor translations
    - Common error types and their severity
    - Consistent scoring criteria
    
    Expected Improvements over Basic Judge:
    - More consistent scoring across similar cases
    - Better calibration of score ranges
    - Reduced subjectivity through example guidance
    - Improved handling of common error patterns
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.judge_name = "Few-Shot Judge"
        self.technique = "Few-Shot Examples"
        
        # Curated examples for few-shot learning
        self.examples = self._get_few_shot_examples()
    
    def evaluate(
        self,
        source_text: str,
        translated_text: str,
        source_lang: str = "en",
        target_lang: str = "auto"
    ) -> Dict[str, Any]:
        """
        Evaluate translation using few-shot examples.
        
        Args:
            source_text: Original text
            translated_text: Translation to evaluate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Dictionary containing evaluation with improved consistency
        """
        
        # Build prompt with examples
        examples_text = self._format_examples()
        
        prompt = f"""{examples_text}

Now evaluate this translation following the same criteria and format:

Original: {source_text}
Translation: {translated_text}

Score (1-5): 
Explanation:"""

        messages = [
            {
                "role": "system", 
                "content": "You are an expert translation evaluator. Use the provided examples to guide your assessment and maintain consistent scoring standards."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
        
        response = self._call_llm(messages)
        parsed_result = self._parse_few_shot_response(response)
        
        # Add metadata
        parsed_result.update({
            "technique": self.technique,
            "judge_name": self.judge_name,
            "source_text": source_text,
            "translated_text": translated_text,
            "examples_used": len(self.examples),
            "raw_response": response
        })
        
        return parsed_result
    
    def _get_few_shot_examples(self) -> List[Dict[str, Any]]:
        """
        Get curated examples for few-shot learning.
        
        Returns:
            List of example cases with scores and explanations
        """
        return [
            {
                "source": "Please send the invoice by Friday.",
                "translation": "Veuillez envoyer la facture avant vendredi.",
                "score": 5,
                "explanation": "Perfect translation. All semantic content preserved, appropriate formality level, natural target language phrasing."
            },
            {
                "source": "The project deadline is next Monday.",
                "translation": "La fecha límite del proyecto es el próximo miércoles.",
                "score": 2,
                "explanation": "Major error: 'Monday' incorrectly translated as 'Wednesday'. This changes critical information and could cause serious misunderstandings."
            },
            {
                "source": "We need to increase our market share by 15%.",
                "translation": "Necesitamos aumentar nuestra participación en el mercado.",
                "score": 3,
                "explanation": "Good general meaning preserved, but specific figure '15%' is omitted. Partial information loss affects completeness."
            },
            {
                "source": "Thank you for your patience during this difficult time.",
                "translation": "Merci pour votre patience pendant cette période difficile.",
                "score": 5,
                "explanation": "Excellent translation. Tone, formality, and complete meaning preserved. Natural French expression."
            },
            {
                "source": "The software requires Windows 10 or higher.",
                "translation": "El software requiere Windows 10 o superior más rápido.",
                "score": 2,
                "explanation": "Mistranslation: 'or higher' becomes 'or faster superior', changing technical meaning. This could mislead users about system requirements."
            }
        ]
    
    def _format_examples(self) -> str:
        """
        Format examples for inclusion in prompt.
        
        Returns:
            Formatted examples string
        """
        formatted = "Here are examples of how to evaluate translations:\n\n"
        
        for i, example in enumerate(self.examples, 1):
            formatted += f"Example {i}:\n"
            formatted += f"Original: {example['source']}\n"
            formatted += f"Translation: {example['translation']}\n"
            formatted += f"Score (1-5): {example['score']}\n"
            formatted += f"Explanation: {example['explanation']}\n\n"
            formatted += "---\n\n"
        
        return formatted
    
    def _parse_few_shot_response(self, response: str) -> Dict[str, Any]:
        """
        Parse response from few-shot judge.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Structured result dictionary
        """
        import re
        
        lines = response.strip().split('\n')
        
        # Look for score
        score = 3  # Default
        explanation = ""
        
        score_patterns = [
            r'score.*?:?\s*([1-5])',
            r'rating.*?:?\s*([1-5])',
            r'\b([1-5])\s*\/\s*5',
            r'\b([1-5])\s*out of 5'
        ]
        
        explanation_started = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Try to extract score
            for pattern in score_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    try:
                        score = int(match.group(1))
                        break
                    except (ValueError, IndexError):
                        continue
            
            # Collect explanation
            if 'explanation:' in line.lower():
                explanation_started = True
                # Get text after "explanation:"
                explanation += line.split(':', 1)[1].strip() + " "
            elif explanation_started:
                explanation += line + " "
            elif not any(re.search(pattern, line, re.IGNORECASE) for pattern in score_patterns):
                # If we haven't found a score pattern, treat as explanation
                if not explanation_started:
                    explanation += line + " "
        
        explanation = explanation.strip()
        if not explanation:
            explanation = "Evaluation completed using few-shot examples."
        
        return {
            "overall_score": score,
            "notes": explanation,
            "confidence": "medium",  # Few-shot provides better confidence
            "methodology": "few_shot_guided_evaluation",
            "consistency_score": self._estimate_consistency(score, explanation)
        }
    
    def _estimate_consistency(self, score: int, explanation: str) -> float:
        """
        Estimate consistency based on explanation quality.
        
        Args:
            score: Assigned score
            explanation: Explanation text
            
        Returns:
            Consistency estimate (0.0-1.0)
        """
        consistency = 0.7  # Base consistency for few-shot
        
        # Higher consistency if explanation mentions specific criteria
        quality_indicators = [
            'semantic', 'meaning', 'accuracy', 'fluency', 'natural',
            'error', 'omission', 'addition', 'tone', 'formality'
        ]
        
        explanation_lower = explanation.lower()
        criteria_mentioned = sum(1 for indicator in quality_indicators 
                               if indicator in explanation_lower)
        
        # Increase consistency based on criteria mentioned
        consistency += min(0.2, criteria_mentioned * 0.05)
        
        # Decrease if explanation is very short (likely low effort)
        if len(explanation.split()) < 10:
            consistency -= 0.15
        
        return min(1.0, max(0.0, consistency))


# Example usage and comparison
if __name__ == "__main__":
    from .basic_judge import BasicJudge
    
    # Test both judges for comparison
    basic_judge = BasicJudge()
    few_shot_judge = FewShotJudge()
    
    test_cases = [
        {
            "source": "The meeting has been rescheduled to Thursday at 2 PM.",
            "translation": "La reunión ha sido reprogramada para el viernes a las 2 PM."  # Wrong day
        },
        {
            "source": "Please review the attached document.",
            "translation": "Veuillez examiner le document ci-joint."  # Perfect
        },
        {
            "source": "We achieved 95% customer satisfaction this quarter.",
            "translation": "Logramos satisfacción del cliente este trimestre."  # Missing percentage
        }
    ]
    
    print("Comparing Basic Judge vs Few-Shot Judge")
    print("=" * 60)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Source: {case['source']}")
        print(f"Translation: {case['translation']}")
        print()
        
        # Basic judge evaluation
        basic_result = basic_judge.evaluate(case['source'], case['translation'])
        print(f"Basic Judge: {basic_result['overall_score']}/5")
        print(f"Basic Notes: {basic_result['notes'][:100]}...")
        
        # Few-shot judge evaluation  
        few_shot_result = few_shot_judge.evaluate(case['source'], case['translation'])
        print(f"Few-Shot Judge: {few_shot_result['overall_score']}/5")
        print(f"Few-Shot Notes: {few_shot_result['notes'][:100]}...")
        print(f"Consistency Score: {few_shot_result['consistency_score']:.2f}")
        print("-" * 40)
    
    # Compare usage statistics
    print(f"\nUsage Comparison:")
    basic_stats = basic_judge.get_usage_stats()
    few_shot_stats = few_shot_judge.get_usage_stats()
    
    print(f"Basic Judge - Calls: {basic_stats['total_calls']}, Tokens: {basic_stats['total_tokens']}")
    print(f"Few-Shot Judge - Calls: {few_shot_stats['total_calls']}, Tokens: {few_shot_stats['total_tokens']}")
    print(f"Token Overhead: {few_shot_stats['total_tokens'] - basic_stats['total_tokens']} tokens")