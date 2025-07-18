"""
Multi-Dimensional Judge: Technique 3 - Structured reasoning with dimensions.

This judge evaluates translations across multiple specific dimensions
with explicit reasoning for each, providing structured and comprehensive
evaluation that reduces bias and improves consistency.
"""

from typing import Dict, Any, List
import json
from .base_judge import BaseJudge


class MultiDimensionalJudge(BaseJudge):
    """
    Multi-dimensional LLM judge with WEIGHTED structured reasoning.
    
    Evaluates translations across distinct dimensions with critical fixes:
    - Accuracy (60% weight): Semantic fidelity and correctness - PRIORITIZED
    - Completeness (25% weight): No omissions or unwanted additions
    - Fluency (10% weight): Natural expression in target language  
    - Appropriateness (5% weight): Register, tone, and style preservation
    
    Key Improvements:
    - WEIGHTED SCORING: Accuracy dominates to prevent dilution by style scores
    - HIERARCHICAL RULES: Critical errors (accuracy ≤2) cap overall scores
    - SIMPLIFIED PROMPTS: Removed JSON complexity, reduced cognitive load
    - ERROR-FOCUSED: Designed to correctly identify factual/semantic issues
    
    Fixes the original averaging problem where high fluency/style scores
    masked critical accuracy failures.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.judge_name = "Multi-Dimensional Judge"
        self.technique = "Multi-Dimensional Reasoning"
        
        # Define evaluation dimensions
        self.dimensions = self._get_evaluation_dimensions()
    
    def evaluate(
        self,
        source_text: str,
        translated_text: str,
        source_lang: str = "en",
        target_lang: str = "auto"
    ) -> Dict[str, Any]:
        """
        Evaluate translation across multiple dimensions.
        
        Args:
            source_text: Original text
            translated_text: Translation to evaluate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Dictionary containing dimensional scores and reasoning
        """
        
        prompt = self._build_dimensional_prompt(source_text, translated_text)
        
        messages = [
            {
                "role": "system", 
                "content": "You are an expert translation evaluator. Analyze translations systematically across multiple dimensions. Provide structured, detailed assessments with clear reasoning."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
        
        response = self._call_llm(messages, max_tokens=1000)
        parsed_result = self._parse_dimensional_response(response)
        
        # Add metadata
        parsed_result.update({
            "technique": self.technique,
            "judge_name": self.judge_name,
            "source_text": source_text,
            "translated_text": translated_text,
            "dimensions_evaluated": len(self.dimensions),
            "raw_response": response
        })
        
        return parsed_result
    
    def _get_evaluation_dimensions(self) -> List[Dict[str, str]]:
        """
        Define the evaluation dimensions and their criteria.
        
        Returns:
            List of dimension specifications
        """
        return [
            {
                "name": "accuracy",
                "description": "Semantic fidelity and factual correctness",
                "criteria": [
                    "All key information is preserved",
                    "No factual errors or distortions", 
                    "Numerical values and dates are correct",
                    "Names and technical terms are accurate"
                ]
            },
            {
                "name": "fluency", 
                "description": "Natural expression in target language",
                "criteria": [
                    "Grammatically correct in target language",
                    "Natural word order and phrasing",
                    "Appropriate idioms and expressions",
                    "Sounds like native speaker output"
                ]
            },
            {
                "name": "completeness",
                "description": "No omissions or unwanted additions",
                "criteria": [
                    "All source content is translated",
                    "No information is omitted",
                    "No extra information is added",
                    "Maintains same level of detail"
                ]
            },
            {
                "name": "appropriateness",
                "description": "Register, tone, and style preservation", 
                "criteria": [
                    "Maintains original formality level",
                    "Preserves emotional tone",
                    "Appropriate for target audience",
                    "Consistent style throughout"
                ]
            }
        ]
    
    def _build_dimensional_prompt(self, source_text: str, translated_text: str) -> str:
        """
        Build prompt with dimensional evaluation structure.
        
        Args:
            source_text: Original text
            translated_text: Translation to evaluate
            
        Returns:
            Formatted prompt string
        """
        
        # Build dimension descriptions
        dimensions_desc = ""
        for dim in self.dimensions:
            dimensions_desc += f"\n**{dim['name'].title()}** ({dim['description']}):\n"
            for criterion in dim['criteria']:
                dimensions_desc += f"  - {criterion}\n"
        
        prompt = f"""Evaluate this translation systematically across these key dimensions:

**ACCURACY** (Most Important): Are facts, numbers, and meaning preserved?
**COMPLETENESS**: Is all information included without omissions?  
**FLUENCY**: Is the language natural and grammatically correct?
**APPROPRIATENESS**: Is the tone and style suitable?

**Translation to Evaluate:**
Original: {source_text}
Translation: {translated_text}

**Provide your evaluation in this format:**

Accuracy (1-5): [score]
Reasoning: [Why this score? Focus on factual correctness]

Completeness (1-5): [score] 
Reasoning: [Any missing or added information?]

Fluency (1-5): [score]
Reasoning: [Grammar, naturalness, readability]

Appropriateness (1-5): [score]
Reasoning: [Tone, formality, style match]

Overall Assessment: [Brief summary of main issues and strengths]"""
        
        return prompt
    
    def _parse_dimensional_response(self, response: str) -> Dict[str, Any]:
        """
        Parse structured dimensional response.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Structured result dictionary
        """
        # Parse the simplified natural language response format
        return self._parse_simplified_response(response)
    
    def _parse_simplified_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the simplified natural language response format.
        
        Args:
            response: Raw LLM response in simplified format
            
        Returns:
            Structured result dictionary
        """
        import re
        
        result = {
            "dimensional_scores": {},
            "overall_score": 3,
            "overall_reasoning": "",
            "key_issues": [],
            "strengths": [],
            "confidence": "high",
            "methodology": "multi_dimensional_weighted_evaluation"
        }
        
        # Extract dimensional scores using regex patterns
        dimensions = ["accuracy", "completeness", "fluency", "appropriateness"]
        
        for dim in dimensions:
            # Look for pattern: "Dimension (1-5): score"
            score_pattern = rf"{dim}.*?\(1-5\):\s*(\d)"
            score_match = re.search(score_pattern, response, re.IGNORECASE)
            
            if score_match:
                score = int(score_match.group(1))
            else:
                # Fallback: look for "Dimension: score"
                fallback_pattern = rf"{dim}.*?:\s*(\d)"
                fallback_match = re.search(fallback_pattern, response, re.IGNORECASE)
                score = int(fallback_match.group(1)) if fallback_match else 3
            
            # Extract reasoning for this dimension
            reasoning_pattern = rf"{dim}.*?reasoning:\s*(.+?)(?=\n[A-Z]|\nOverall|$)"
            reasoning_match = re.search(reasoning_pattern, response, re.IGNORECASE | re.DOTALL)
            reasoning = reasoning_match.group(1).strip() if reasoning_match else f"Score: {score}"
            
            result["dimensional_scores"][dim] = {
                "score": max(1, min(5, score)),
                "reasoning": reasoning[:200] + "..." if len(reasoning) > 200 else reasoning
            }
        
        # Extract overall assessment
        overall_pattern = r"overall assessment:\s*(.+?)$"
        overall_match = re.search(overall_pattern, response, re.IGNORECASE | re.DOTALL)
        if overall_match:
            result["overall_reasoning"] = overall_match.group(1).strip()
        
        # Calculate weighted overall score (this is the key fix!)
        result["overall_score"] = self._calculate_weighted_score(result["dimensional_scores"])
        
        # Extract key issues and strengths from reasoning
        all_reasoning = " ".join([d["reasoning"] for d in result["dimensional_scores"].values()])
        
        # Simple extraction of issues and strengths
        if any(word in all_reasoning.lower() for word in ["error", "incorrect", "wrong", "missing", "problem"]):
            result["key_issues"] = ["Issues identified in dimensional analysis"]
        
        if any(word in all_reasoning.lower() for word in ["good", "correct", "natural", "appropriate", "accurate"]):
            result["strengths"] = ["Strengths noted in dimensional analysis"]
        
        # Calculate reliability and notes
        result["reliability_score"] = self._calculate_reliability(result)
        result["notes"] = self._summarize_evaluation(result)
        
        return result
    
    def _fallback_dimensional_parse(self, response: str) -> Dict[str, Any]:
        """
        Fallback parser for non-JSON dimensional responses.
        
        Args:
            response: Raw response text
            
        Returns:
            Structured result with extracted information
        """
        import re
        
        result = {
            "dimensional_scores": {},
            "overall_score": 3,
            "overall_reasoning": "",
            "key_issues": [],
            "strengths": [],
            "confidence": "medium",
            "methodology": "fallback_dimensional_parsing"
        }
        
        # Try to extract scores for each dimension
        for dim in self.dimensions:
            dim_name = dim["name"]
            # Look for patterns like "Accuracy: 4" or "Accuracy score: 4"
            patterns = [
                f"{dim_name}.*?:.*?([1-5])",
                f"{dim_name}.*?score.*?([1-5])",
                f"{dim_name}.*?([1-5])/5"
            ]
            
            score = 3  # Default
            for pattern in patterns:
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    try:
                        score = int(match.group(1))
                        break
                    except (ValueError, IndexError):
                        continue
            
            # Extract reasoning (text following dimension name)
            reasoning_pattern = f"{dim_name}.*?:(.+?)(?={self.dimensions[self.dimensions.index(dim)+1]['name'] if self.dimensions.index(dim)+1 < len(self.dimensions) else 'overall|summary'}|$)"
            reasoning_match = re.search(reasoning_pattern, response, re.IGNORECASE | re.DOTALL)
            reasoning = reasoning_match.group(1).strip() if reasoning_match else "No reasoning extracted"
            
            result["dimensional_scores"][dim_name] = {
                "score": score,
                "reasoning": reasoning[:200] + "..." if len(reasoning) > 200 else reasoning
            }
        
        # Calculate overall score using weighted methodology
        if result["dimensional_scores"]:
            result["overall_score"] = self._calculate_weighted_score(result["dimensional_scores"])
        
        result["overall_reasoning"] = response[:300] + "..." if len(response) > 300 else response
        result["notes"] = self._summarize_evaluation(result)
        
        return result
    
    def _calculate_reliability(self, result: Dict[str, Any]) -> float:
        """
        Calculate reliability score based on evaluation completeness.
        
        Args:
            result: Evaluation result
            
        Returns:
            Reliability score (0.0-1.0)
        """
        reliability = 0.8  # Base reliability for structured evaluation
        
        # Check completeness of dimensional evaluation
        expected_dims = len(self.dimensions)
        actual_dims = len(result["dimensional_scores"])
        completeness = actual_dims / expected_dims
        
        # Check reasoning quality
        reasoning_quality = 0.0
        if result["dimensional_scores"]:
            reasoning_lengths = [len(d["reasoning"]) for d in result["dimensional_scores"].values()]
            avg_reasoning_length = sum(reasoning_lengths) / len(reasoning_lengths)
            reasoning_quality = min(1.0, avg_reasoning_length / 100)  # Normalize to 100 chars
        
        # Check for specific evidence
        evidence_bonus = 0.0
        if result["key_issues"] or result["strengths"]:
            evidence_bonus = 0.1
        
        reliability = reliability * completeness + reasoning_quality * 0.15 + evidence_bonus
        return min(1.0, max(0.0, reliability))
    
    def _summarize_evaluation(self, result: Dict[str, Any]) -> str:
        """
        Create a summary of the dimensional evaluation.
        
        Args:
            result: Evaluation result
            
        Returns:
            Summary string
        """
        summary_parts = []
        
        # Dimensional scores summary
        if result["dimensional_scores"]:
            scores_text = ", ".join([
                f"{dim}: {data['score']}/5" 
                for dim, data in result["dimensional_scores"].items()
            ])
            summary_parts.append(f"Dimensional scores: {scores_text}")
        
        # Key issues
        if result["key_issues"]:
            issues_text = "; ".join(result["key_issues"][:3])  # Top 3 issues
            summary_parts.append(f"Key issues: {issues_text}")
        
        # Strengths
        if result["strengths"]:
            strengths_text = "; ".join(result["strengths"][:2])  # Top 2 strengths
            summary_parts.append(f"Strengths: {strengths_text}")
        
        return ". ".join(summary_parts) if summary_parts else "Structured evaluation completed."
    
    def _calculate_weighted_score(self, dimensional_scores: Dict[str, Dict]) -> int:
        """
        Calculate weighted overall score to prioritize accuracy and fix averaging problem.
        
        Args:
            dimensional_scores: Dictionary of dimensional evaluations
            
        Returns:
            Weighted overall score (1-5)
        """
        # Weighted scoring system - accuracy is DOMINANT
        weights = {
            "accuracy": 0.80,        # DOMINANT - factual correctness must dominate
            "completeness": 0.15,    # Important - information preservation  
            "fluency": 0.03,         # Minimal - grammar/naturalness
            "appropriateness": 0.02  # Minimal - style considerations
        }
        
        total_weight = 0.0
        weighted_sum = 0.0
        
        for dim_name, dim_data in dimensional_scores.items():
            if dim_name in weights:
                score = dim_data.get("score", 3)
                weight = weights[dim_name]
                weighted_sum += score * weight
                total_weight += weight
        
        if total_weight == 0:
            return 3  # Default fallback
            
        weighted_average = weighted_sum / total_weight
        
        # Apply hierarchical rules - critical errors override high scores
        accuracy_score = dimensional_scores.get("accuracy", {}).get("score", 3)
        
        # Rule 1: Severe accuracy problems (≤2) cap the overall score MORE AGGRESSIVELY
        if accuracy_score <= 2:
            # Major accuracy issues cannot score above 2, regardless of other dimensions
            weighted_average = min(weighted_average, 2.0)
            
        # Rule 2: Critical accuracy failures (score 1) get maximum penalty
        if accuracy_score == 1:
            # Critical factual errors cannot score above 1 (matches Basic judge severity)
            weighted_average = min(weighted_average, 1.0)
        
        return round(max(1, min(5, weighted_average)))


# Example usage and testing
if __name__ == "__main__":
    judge = MultiDimensionalJudge()
    
    test_cases = [
        {
            "source": "Due to unforeseen circumstances, we must postpone the quarterly review meeting until next Friday at 3:00 PM.",
            "translation": "En raison de circonstances imprévues, nous devons reporter la réunion d'examen trimestrielle jusqu'à vendredi prochain à 15h00."
        },
        {
            "source": "The project budget has increased by 25% due to additional requirements.",
            "translation": "El presupuesto del proyecto ha aumentado debido a requisitos adicionales."  # Missing percentage
        }
    ]
    
    print(f"Testing {judge.judge_name}")
    print("=" * 60)
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"Source: {case['source']}")
        print(f"Translation: {case['translation']}")
        print()
        
        result = judge.evaluate(case['source'], case['translation'])
        
        print(f"Overall Score: {result['overall_score']}/5")
        print(f"Reliability: {result['reliability_score']:.2f}")
        print()
        
        print("Dimensional Breakdown:")
        for dim, data in result["dimensional_scores"].items():
            print(f"  {dim.title()}: {data['score']}/5")
            print(f"    Reasoning: {data['reasoning'][:80]}...")
        
        if result["key_issues"]:
            print(f"\nKey Issues: {'; '.join(result['key_issues'])}")
        
        if result["strengths"]:
            print(f"Strengths: {'; '.join(result['strengths'])}")
        
        print("-" * 50)
    
    # Show usage statistics
    stats = judge.get_usage_stats()
    print(f"\nUsage Statistics:")
    print(f"Total API calls: {stats['total_calls']}")
    print(f"Total tokens: {stats['total_tokens']}")
    print(f"Avg tokens per call: {stats['avg_tokens_per_call']:.1f}")