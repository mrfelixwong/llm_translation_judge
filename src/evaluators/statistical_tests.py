#!/usr/bin/env python3
"""
Statistical significance testing for LLM judge comparisons.
"""

import numpy as np
from scipy import stats
from typing import List, Dict, Tuple, Any
import statistics


class SignificanceTestRunner:
    """Run statistical significance tests for judge comparisons."""
    
    def __init__(self):
        pass
    
    def t_test(self, group1: List[float], group2: List[float]) -> Dict[str, Any]:
        """Perform independent t-test between two groups."""
        try:
            statistic, p_value = stats.ttest_ind(group1, group2)
            
            # Calculate effect size (Cohen's d)
            mean1, mean2 = statistics.mean(group1), statistics.mean(group2)
            std1, std2 = statistics.stdev(group1), statistics.stdev(group2)
            n1, n2 = len(group1), len(group2)
            
            pooled_std = ((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2)
            pooled_std = pooled_std**0.5
            
            cohens_d = (mean1 - mean2) / pooled_std if pooled_std > 0 else 0.0
            
            # Effect size interpretation
            if abs(cohens_d) < 0.2:
                effect_size = "negligible"
            elif abs(cohens_d) < 0.5:
                effect_size = "small"
            elif abs(cohens_d) < 0.8:
                effect_size = "medium"
            else:
                effect_size = "large"
            
        except Exception as e:
            statistic = p_value = cohens_d = 0.0
            effect_size = "unknown"
        
        return {
            "statistic": statistic,
            "p_value": p_value,
            "cohens_d": cohens_d,
            "effect_size": effect_size,
            "significant": p_value < 0.05
        }
    
    def chi_square_test(self, observed: List[List[int]]) -> Dict[str, Any]:
        """Perform chi-square test of independence."""
        try:
            chi2, p_value, dof, expected = stats.chi2_contingency(observed)
            
            # Calculate effect size (Cramer's V)
            n = sum(sum(row) for row in observed)
            min_dim = min(len(observed) - 1, len(observed[0]) - 1)
            cramers_v = (chi2 / (n * min_dim))**0.5 if min_dim > 0 else 0.0
            
        except Exception as e:
            chi2 = p_value = dof = cramers_v = 0.0
            expected = []
        
        return {
            "chi2": chi2,
            "p_value": p_value,
            "degrees_of_freedom": dof,
            "cramers_v": cramers_v,
            "significant": p_value < 0.05,
            "expected": expected
        }
    
    def compare_judges(self, judge_scores: Dict[str, List[float]]) -> Dict[str, Any]:
        """Compare multiple judges using various statistical tests."""
        judges = list(judge_scores.keys())
        results = {}
        
        # Pairwise t-tests
        for i, judge1 in enumerate(judges):
            for j, judge2 in enumerate(judges[i+1:], i+1):
                comparison = f"{judge1}_vs_{judge2}"
                results[comparison] = self.t_test(
                    judge_scores[judge1], 
                    judge_scores[judge2]
                )
        
        # ANOVA if more than 2 judges
        if len(judges) > 2:
            try:
                f_stat, anova_p = stats.f_oneway(*judge_scores.values())
                results["anova"] = {
                    "f_statistic": f_stat,
                    "p_value": anova_p,
                    "significant": anova_p < 0.05
                }
            except:
                results["anova"] = {
                    "f_statistic": 0.0,
                    "p_value": 1.0,
                    "significant": False
                }
        
        return results
    
    def power_analysis(self, effect_size: float, alpha: float = 0.05, 
                      power: float = 0.8) -> int:
        """Calculate required sample size for given effect size and power."""
        # Simplified power analysis for t-test
        # Using Cohen's conventions
        try:
            from scipy.stats import norm
            z_alpha = norm.ppf(1 - alpha/2)
            z_beta = norm.ppf(power)
            
            n = 2 * ((z_alpha + z_beta) / effect_size)**2
            return int(np.ceil(n))
        except:
            return 30  # Default minimum sample size