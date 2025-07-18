#!/usr/bin/env python3
"""
Benchmark evaluation system for translation quality assessment.
"""

import json
import random
from typing import List, Dict, Any, Tuple
from pathlib import Path


class TranslationBenchmark:
    """Benchmark for evaluating translation quality judges."""
    
    def __init__(self, test_data_path: str = None):
        self.test_cases = []
        self.ground_truth = {}
        if test_data_path:
            self.load_test_data(test_data_path)
    
    def load_test_data(self, file_path: str):
        """Load test data from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.test_cases = data.get('test_cases', [])
                self.ground_truth = data.get('ground_truth', {})
        except FileNotFoundError:
            print(f"Test data file not found: {file_path}")
            self._generate_sample_data()
    
    def _generate_sample_data(self):
        """Generate sample test data for demonstration."""
        self.test_cases = [
            {
                "id": f"test_{i}",
                "source": f"Sample English text {i}",
                "translation": f"Sample Spanish translation {i}",
                "language_pair": "en-es",
                "error_type": random.choice(["none", "factual", "omission", "mistranslation"]),
                "has_error": random.choice([True, False])
            }
            for i in range(50)
        ]
        
        # Generate ground truth scores
        for case in self.test_cases:
            base_score = 4.5 if not case["has_error"] else random.uniform(1.5, 3.5)
            self.ground_truth[case["id"]] = {
                "expert_score": base_score,
                "error_present": case["has_error"],
                "error_type": case["error_type"]
            }
    
    def get_test_cases(self, language_pair: str = None, limit: int = None) -> List[Dict]:
        """Get test cases, optionally filtered by language pair."""
        cases = self.test_cases
        
        if language_pair:
            cases = [c for c in cases if c.get("language_pair") == language_pair]
        
        if limit:
            cases = cases[:limit]
        
        return cases
    
    def get_ground_truth(self, case_id: str) -> Dict:
        """Get ground truth for a specific test case."""
        return self.ground_truth.get(case_id, {})


class GroundTruthEvaluator:
    """Evaluates judge performance against ground truth."""
    
    def __init__(self, benchmark: TranslationBenchmark):
        self.benchmark = benchmark
    
    def evaluate_judge(self, judge_scores: Dict[str, float]) -> Dict[str, Any]:
        """Evaluate a judge's performance against ground truth."""
        accuracies = []
        error_detections = []
        correlations = []
        
        for case_id, judge_score in judge_scores.items():
            ground_truth = self.benchmark.get_ground_truth(case_id)
            
            if ground_truth:
                expert_score = ground_truth["expert_score"]
                
                # Calculate accuracy (within 0.5 points)
                accurate = abs(judge_score - expert_score) <= 0.5
                accuracies.append(accurate)
                
                # Check error detection
                judge_detected_error = judge_score < 3.0
                actual_error = ground_truth["error_present"]
                error_detection_correct = judge_detected_error == actual_error
                error_detections.append(error_detection_correct)
                
                correlations.append((judge_score, expert_score))
        
        # Calculate metrics
        accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0
        error_detection_rate = sum(error_detections) / len(error_detections) if error_detections else 0.0
        
        # Calculate correlation
        if correlations:
            judge_scores_list = [c[0] for c in correlations]
            expert_scores_list = [c[1] for c in correlations]
            
            # Simple correlation calculation
            n = len(correlations)
            if n > 1:
                mean_j = sum(judge_scores_list) / n
                mean_e = sum(expert_scores_list) / n
                
                numerator = sum((j - mean_j) * (e - mean_e) for j, e in zip(judge_scores_list, expert_scores_list))
                denom_j = sum((j - mean_j) ** 2 for j in judge_scores_list) ** 0.5
                denom_e = sum((e - mean_e) ** 2 for e in expert_scores_list) ** 0.5
                
                correlation = numerator / (denom_j * denom_e) if denom_j * denom_e > 0 else 0.0
            else:
                correlation = 0.0
        else:
            correlation = 0.0
        
        return {
            "accuracy": accuracy,
            "error_detection_rate": error_detection_rate,
            "correlation_with_expert": correlation,
            "total_evaluations": len(accuracies)
        }