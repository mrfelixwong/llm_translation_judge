"""
Back-Translation Judge: Technique 4 - Consistency validation through reverse translation.

This judge adds back-translation as a consistency check, translating
the target text back to the source language and comparing with the
original to catch subtle semantic errors and ensure faithfulness.
"""

from typing import Dict, Any, List
import json
from .multi_dimensional_judge import MultiDimensionalJudge


class BackTranslationJudge(MultiDimensionalJudge):
    """
    Back-translation LLM judge with consistency validation.
    
    Extends multi-dimensional evaluation by adding back-translation:
    1. Performs dimensional evaluation (inherited)
    2. Translates target text back to source language
    3. Compares back-translation with original for semantic consistency
    4. Adjusts scores based on consistency findings
    
    Expected Improvements over Multi-Dimensional Judge:
    - Catches subtle semantic drift not visible in forward evaluation
    - Validates meaning preservation through round-trip consistency
    - Identifies false positives where fluent text loses meaning
    - Provides additional confidence in high-stakes evaluations
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.judge_name = "Back-Translation Judge"
        self.technique = "Back-Translation Validation"
    
    def evaluate(
        self,
        source_text: str,
        translated_text: str,
        source_lang: str = "en",
        target_lang: str = "auto"
    ) -> Dict[str, Any]:
        """
        Evaluate translation with back-translation validation.
        
        Args:
            source_text: Original text
            translated_text: Translation to evaluate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Dictionary containing enhanced evaluation with consistency check
        """
        
        # Step 1: Get base multi-dimensional evaluation
        base_result = super().evaluate(source_text, translated_text, source_lang, target_lang)
        
        # Step 2: Perform back-translation
        back_translation = self._get_back_translation(translated_text, source_lang)
        
        # Step 3: Evaluate consistency
        consistency_analysis = self._evaluate_consistency(
            source_text, translated_text, back_translation
        )
        
        # Step 4: Integrate results
        enhanced_result = self._integrate_back_translation_results(
            base_result, back_translation, consistency_analysis
        )
        
        # Update metadata
        enhanced_result.update({
            "technique": self.technique,
            "judge_name": self.judge_name,
            "back_translation": back_translation,
            "consistency_analysis": consistency_analysis
        })
        
        return enhanced_result
    
    def _get_back_translation(self, translated_text: str, target_lang: str = "en") -> str:
        """
        Generate back-translation of the target text.
        
        Args:
            translated_text: Text to translate back
            target_lang: Target language for back-translation
            
        Returns:
            Back-translated text
        """
        
        prompt = f"""Translate the following text back to English. Focus on accuracy and preserve all meaning:

Text to translate: {translated_text}

Provide only the translation, no additional commentary."""
        
        messages = [
            {
                "role": "system", 
                "content": "You are a professional translator. Provide accurate, faithful translations that preserve all original meaning."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
        
        response = self._call_llm(messages, temperature=0.1)  # Lower temperature for consistency
        return response.strip()
    
    def _evaluate_consistency(
        self, 
        original: str, 
        translation: str, 
        back_translation: str
    ) -> Dict[str, Any]:
        """
        Evaluate consistency between original and back-translation.
        
        Args:
            original: Original source text
            translation: Forward translation
            back_translation: Back-translated text
            
        Returns:
            Consistency analysis results
        """
        
        prompt = f"""Compare the original text with its back-translation to assess semantic consistency. Identify any meaning changes, information loss, or distortions.

Original: {original}
Translation: {translation}
Back-Translation: {back_translation}

Analyze the following aspects:

1. **Semantic Preservation**: Does the back-translation preserve the core meaning?
2. **Information Retention**: Is any information lost or added during the round trip?
3. **Tone and Register**: Is the tone/formality level maintained?
4. **Factual Accuracy**: Are numbers, dates, names, and facts preserved?
5. **Confidence Assessment**: How confident are you in the translation quality based on this comparison?

Provide your analysis in the following JSON format:

{{
  "semantic_preservation": {{
    "score": [1-5],
    "analysis": "Detailed comparison of meaning preservation"
  }},
  "information_retention": {{
    "score": [1-5], 
    "analysis": "Assessment of information completeness"
  }},
  "tone_consistency": {{
    "score": [1-5],
    "analysis": "Evaluation of tone and register preservation"
  }},
  "factual_accuracy": {{
    "score": [1-5],
    "analysis": "Assessment of factual information preservation"
  }},
  "overall_consistency": {{
    "score": [1-5],
    "confidence": [1-5],
    "analysis": "Overall assessment of round-trip consistency"
  }},
  "key_discrepancies": ["List of significant differences found"],
  "consistency_verdict": "CONSISTENT|MINOR_ISSUES|MAJOR_ISSUES|INCONSISTENT"
}}"""
        
        messages = [
            {
                "role": "system", 
                "content": "You are an expert in translation consistency analysis. Compare texts systematically and identify subtle semantic differences."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
        
        response = self._call_llm(messages, max_tokens=1200)
        return self._parse_consistency_response(response)
    
    def _parse_consistency_response(self, response: str) -> Dict[str, Any]:
        """
        Parse consistency analysis response.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Structured consistency analysis
        """
        parsed_json = self._parse_json_response(response)
        
        if "parsing_error" in parsed_json:
            return self._fallback_consistency_parse(response)
        
        # Structure the consistency analysis
        consistency_result = {
            "semantic_preservation": parsed_json.get("semantic_preservation", {"score": 4, "analysis": ""}),
            "information_retention": parsed_json.get("information_retention", {"score": 4, "analysis": ""}),
            "tone_consistency": parsed_json.get("tone_consistency", {"score": 4, "analysis": ""}),
            "factual_accuracy": parsed_json.get("factual_accuracy", {"score": 4, "analysis": ""}),
            "overall_consistency": parsed_json.get("overall_consistency", {"score": 4, "confidence": 4, "analysis": ""}),
            "key_discrepancies": parsed_json.get("key_discrepancies", []),
            "consistency_verdict": parsed_json.get("consistency_verdict", "MINOR_ISSUES")
        }
        
        return consistency_result
    
    def _fallback_consistency_parse(self, response: str) -> Dict[str, Any]:
        """
        Fallback parser for consistency analysis.
        
        Args:
            response: Raw response text
            
        Returns:
            Basic consistency structure
        """
        import re
        
        # Extract overall assessment
        verdict = "MINOR_ISSUES"  # Default
        verdict_patterns = [
            r"(CONSISTENT|MINOR_ISSUES|MAJOR_ISSUES|INCONSISTENT)",
            r"verdict.*?:.*?(consistent|minor|major|inconsistent)"
        ]
        
        for pattern in verdict_patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                found_verdict = match.group(1).upper()
                if "CONSISTENT" in found_verdict:
                    verdict = "CONSISTENT"
                elif "MINOR" in found_verdict:
                    verdict = "MINOR_ISSUES"
                elif "MAJOR" in found_verdict:
                    verdict = "MAJOR_ISSUES"
                elif "INCONSISTENT" in found_verdict:
                    verdict = "INCONSISTENT"
                break
        
        # Extract any numerical scores
        scores = re.findall(r'\b([1-5])\b', response)
        avg_score = 4 if not scores else sum(int(s) for s in scores[:4]) / min(4, len(scores))
        
        return {
            "semantic_preservation": {"score": int(avg_score), "analysis": "Basic analysis"},
            "information_retention": {"score": int(avg_score), "analysis": "Basic analysis"},
            "tone_consistency": {"score": int(avg_score), "analysis": "Basic analysis"},
            "factual_accuracy": {"score": int(avg_score), "analysis": "Basic analysis"},
            "overall_consistency": {"score": int(avg_score), "confidence": int(avg_score), "analysis": response[:200]},
            "key_discrepancies": [],
            "consistency_verdict": verdict
        }
    
    def _integrate_back_translation_results(
        self,
        base_result: Dict[str, Any],
        back_translation: str,
        consistency_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Integrate back-translation findings with base evaluation.
        
        Args:
            base_result: Multi-dimensional evaluation result
            back_translation: Back-translated text
            consistency_analysis: Consistency evaluation
            
        Returns:
            Enhanced evaluation result
        """
        
        # Start with base result
        enhanced_result = base_result.copy()
        
        # Adjust scores based on consistency findings
        consistency_score = consistency_analysis["overall_consistency"]["score"]
        consistency_verdict = consistency_analysis["consistency_verdict"]
        
        # Apply consistency adjustments to dimensional scores
        if "dimensional_scores" in enhanced_result:
            for dim_name, dim_data in enhanced_result["dimensional_scores"].items():
                original_score = dim_data["score"]
                
                # Adjust based on consistency verdict
                if consistency_verdict == "INCONSISTENT":
                    adjusted_score = max(1, min(original_score, 2))  # Cap at 2 for major inconsistency
                elif consistency_verdict == "MAJOR_ISSUES":
                    adjusted_score = max(1, min(original_score, 3))  # Cap at 3 for major issues
                elif consistency_verdict == "MINOR_ISSUES":
                    adjusted_score = max(1, original_score - 0.5)  # Small penalty
                else:  # CONSISTENT
                    adjusted_score = min(5, original_score + 0.2)  # Small bonus for consistency
                
                # Special handling for accuracy dimension
                if dim_name == "accuracy":
                    semantic_score = consistency_analysis["semantic_preservation"]["score"]
                    factual_score = consistency_analysis["factual_accuracy"]["score"]
                    consistency_adjusted = (semantic_score + factual_score) / 2
                    adjusted_score = (original_score + consistency_adjusted) / 2
                
                enhanced_result["dimensional_scores"][dim_name] = {
                    "score": round(adjusted_score),
                    "original_score": original_score,
                    "consistency_adjustment": round(adjusted_score) - original_score,
                    "reasoning": dim_data["reasoning"] + f" [Consistency check: {consistency_verdict}]"
                }
        
        # Update overall score
        if enhanced_result["dimensional_scores"]:
            new_dim_scores = [d["score"] for d in enhanced_result["dimensional_scores"].values()]
            enhanced_result["overall_score"] = round(sum(new_dim_scores) / len(new_dim_scores))
        
        # Enhanced confidence based on consistency
        consistency_confidence = consistency_analysis["overall_consistency"]["confidence"]
        base_confidence_map = {"low": 0.4, "medium": 0.6, "high": 0.8}
        base_confidence_val = base_confidence_map.get(enhanced_result.get("confidence", "medium"), 0.6)
        
        # Combine confidences
        combined_confidence = (base_confidence_val + consistency_confidence / 5) / 2
        if combined_confidence >= 0.8:
            enhanced_result["confidence"] = "very_high"
        elif combined_confidence >= 0.7:
            enhanced_result["confidence"] = "high"
        elif combined_confidence >= 0.5:
            enhanced_result["confidence"] = "medium"
        else:
            enhanced_result["confidence"] = "low"
        
        # Add back-translation specific metrics
        enhanced_result.update({
            "methodology": "back_translation_validated_evaluation",
            "consistency_score": consistency_score,
            "consistency_verdict": consistency_verdict,
            "back_translation_analysis": consistency_analysis,
            "reliability_score": min(1.0, enhanced_result.get("reliability_score", 0.8) + 0.15)  # Boost reliability
        })
        
        # Update summary notes
        consistency_summary = f"Back-translation consistency: {consistency_verdict} (score: {consistency_score}/5)"
        if enhanced_result.get("notes"):
            enhanced_result["notes"] += f". {consistency_summary}"
        else:
            enhanced_result["notes"] = consistency_summary
        
        return enhanced_result


# Example usage and comprehensive testing
if __name__ == "__main__":
    from .basic_judge import BasicJudge
    from .few_shot_judge import FewShotJudge
    
    # Test all judge types for comparison
    judges = {
        "Basic": BasicJudge(),
        "Few-Shot": FewShotJudge(), 
        "Multi-Dimensional": MultiDimensionalJudge(),
        "Back-Translation": BackTranslationJudge()
    }
    
    test_cases = [
        {
            "name": "Perfect Translation",
            "source": "Please confirm your attendance by Friday.",
            "translation": "Veuillez confirmer votre présence avant vendredi."
        },
        {
            "name": "Date Error", 
            "source": "The deadline is Monday, March 15th.",
            "translation": "La fecha límite es martes, 15 de marzo."  # Wrong day
        },
        {
            "name": "Missing Information",
            "source": "Transfer $5,000 to account #12345 by 5 PM today.",
            "translation": "Transfiera dinero a la cuenta hoy."  # Missing amount, account, time
        }
    ]
    
    print("Comprehensive Judge Comparison")
    print("=" * 80)
    
    for case in test_cases:
        print(f"\n{case['name'].upper()}")
        print(f"Source: {case['source']}")
        print(f"Translation: {case['translation']}")
        print("-" * 60)
        
        for judge_name, judge in judges.items():
            result = judge.evaluate(case['source'], case['translation'])
            
            print(f"\n{judge_name} Judge:")
            print(f"  Score: {result['overall_score']}/5")
            print(f"  Confidence: {result.get('confidence', 'N/A')}")
            
            if judge_name == "Back-Translation" and "back_translation" in result:
                print(f"  Back-Translation: {result['back_translation']}")
                print(f"  Consistency: {result['consistency_verdict']}")
            
            # Show first 100 chars of notes
            notes = result.get('notes', 'No notes')
            print(f"  Notes: {notes[:100]}{'...' if len(notes) > 100 else ''}")
        
        print("\n" + "=" * 80)
    
    # Usage statistics comparison
    print("\nUsage Statistics Comparison:")
    print("-" * 40)
    for judge_name, judge in judges.items():
        stats = judge.get_usage_stats()
        print(f"{judge_name}: {stats['total_calls']} calls, {stats['total_tokens']} tokens, ${stats['estimated_cost']:.4f}")
    
    # Show token overhead progression
    basic_tokens = judges["Basic"].get_usage_stats()['total_tokens']
    print(f"\nToken Overhead vs Basic Judge:")
    for judge_name, judge in judges.items():
        if judge_name != "Basic":
            tokens = judge.get_usage_stats()['total_tokens']
            overhead = tokens - basic_tokens
            percentage = (overhead / basic_tokens) * 100 if basic_tokens > 0 else 0
            print(f"  {judge_name}: +{overhead} tokens (+{percentage:.1f}%)")