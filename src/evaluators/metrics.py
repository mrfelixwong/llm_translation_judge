#!/usr/bin/env python3
"""
Reliability metrics for evaluating LLM judge performance.
"""

import numpy as np
from sklearn.metrics import mean_absolute_error, cohen_kappa_score
from scipy.stats import pearsonr, spearmanr
from typing import List, Dict, Tuple, Any
import statistics


class ReliabilityMetrics:
    """Calculate reliability metrics for LLM judge evaluation."""
    
    def __init__(self):
        self.metrics = {}
    
    def calculate_accuracy(self, predictions: List[float], ground_truth: List[float], 
                          threshold: float = 0.5) -> float:
        """Calculate accuracy based on score agreement within threshold."""
        if len(predictions) != len(ground_truth):
            raise ValueError("Predictions and ground truth must have same length")
        
        correct = sum(1 for p, g in zip(predictions, ground_truth) 
                     if abs(p - g) <= threshold)
        return correct / len(predictions)
    
    def calculate_consistency(self, scores_list: List[List[float]]) -> Dict[str, float]:
        """Calculate consistency metrics across multiple evaluations."""
        if not scores_list or len(scores_list) < 2:
            return {"overall": 0.0, "inter_repetition_agreement": 0.0, "score_stability": 0.0}
        
        # Calculate variance across repetitions
        variances = []
        for i in range(len(scores_list[0])):
            scores_for_item = [scores[i] for scores in scores_list if i < len(scores)]
            if len(scores_for_item) > 1:
                variances.append(statistics.variance(scores_for_item))
        
        avg_variance = statistics.mean(variances) if variances else 0
        consistency = max(0, 1 - avg_variance)  # Lower variance = higher consistency
        
        # Inter-repetition agreement (simplified Cohen's kappa approximation)
        if len(scores_list) >= 2:
            flat_scores1 = scores_list[0]
            flat_scores2 = scores_list[1] if len(scores_list) > 1 else scores_list[0]
            
            # Convert to categorical for kappa
            cat1 = [1 if s >= 3.5 else 0 for s in flat_scores1]
            cat2 = [1 if s >= 3.5 else 0 for s in flat_scores2]
            
            try:
                kappa = cohen_kappa_score(cat1, cat2)
            except:
                kappa = 0.0
        else:
            kappa = 0.0
        
        return {
            "overall": consistency,
            "inter_repetition_agreement": kappa,
            "score_stability": 1 - (avg_variance / 5.0) if avg_variance < 5.0 else 0.0
        }
    
    def calculate_error_detection(self, predictions: List[float], 
                                error_labels: List[bool]) -> Dict[str, Any]:
        """Calculate error detection metrics."""
        if len(predictions) != len(error_labels):
            raise ValueError("Predictions and error labels must have same length")
        
        # Use threshold to determine if error was detected
        threshold = 3.0  # Scores below 3.0 indicate detected error
        detected = [p < threshold for p in predictions]
        
        true_positives = sum(1 for d, e in zip(detected, error_labels) if d and e)
        false_positives = sum(1 for d, e in zip(detected, error_labels) if d and not e)
        false_negatives = sum(1 for d, e in zip(detected, error_labels) if not d and e)
        true_negatives = sum(1 for d, e in zip(detected, error_labels) if not d and not e)
        
        total_errors = sum(error_labels)
        detection_rate = true_positives / total_errors if total_errors > 0 else 0.0
        
        return {
            "detection_rate": detection_rate,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "true_negatives": true_negatives,
            "total_errors": total_errors
        }
    
    def calculate_correlation(self, predictions: List[float], 
                            ground_truth: List[float]) -> Dict[str, float]:
        """Calculate correlation metrics with ground truth."""
        if len(predictions) != len(ground_truth):
            raise ValueError("Predictions and ground truth must have same length")
        
        try:
            pearson_r, pearson_p = pearsonr(predictions, ground_truth)
            spearman_r, spearman_p = spearmanr(predictions, ground_truth)
            mae = mean_absolute_error(ground_truth, predictions)
        except:
            pearson_r = pearson_p = spearman_r = spearman_p = mae = 0.0
        
        return {
            "pearson_correlation": pearson_r,
            "pearson_p_value": pearson_p,
            "spearman_correlation": spearman_r,
            "spearman_p_value": spearman_p,
            "mean_absolute_error": mae
        }


class ConsistencyAnalyzer:
    """Analyze consistency patterns in LLM judge evaluations."""
    
    def __init__(self):
        pass
    
    def analyze_score_variance(self, scores: List[List[float]]) -> Dict[str, float]:
        """Analyze variance patterns in scores."""
        if not scores:
            return {"mean_variance": 0.0, "max_variance": 0.0, "stability_index": 0.0}
        
        variances = []
        for score_set in scores:
            if len(score_set) > 1:
                variances.append(statistics.variance(score_set))
        
        if not variances:
            return {"mean_variance": 0.0, "max_variance": 0.0, "stability_index": 1.0}
        
        return {
            "mean_variance": statistics.mean(variances),
            "max_variance": max(variances),
            "stability_index": max(0, 1 - (statistics.mean(variances) / 2.0))
        }
    
    def calculate_inter_judge_agreement(self, judge_scores: Dict[str, List[float]]) -> float:
        """Calculate agreement between different judges."""
        judges = list(judge_scores.keys())
        if len(judges) < 2:
            return 0.0
        
        agreements = []
        for i in range(len(judges)):
            for j in range(i + 1, len(judges)):
                scores1 = judge_scores[judges[i]]
                scores2 = judge_scores[judges[j]]
                
                min_len = min(len(scores1), len(scores2))
                if min_len > 0:
                    # Calculate agreement as inverse of mean absolute difference
                    differences = [abs(scores1[k] - scores2[k]) for k in range(min_len)]
                    agreement = max(0, 1 - (statistics.mean(differences) / 5.0))
                    agreements.append(agreement)
        
        return statistics.mean(agreements) if agreements else 0.0