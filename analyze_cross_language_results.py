#!/usr/bin/env python3
"""
Analyze cross-language error detection results from the LLM judge study.
"""

import json
import pandas as pd
from typing import Dict, List, Any

def analyze_results(results_file: str):
    """Analyze cross-language error detection performance."""
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    # Initialize data structure
    analysis = {
        'error_detection_by_language_and_judge': {},
        'score_distribution': {},
        'error_type_detection': {}
    }
    
    # Process each language
    for lang_pair, lang_data in results['results_by_language'].items():
        print(f"\n🌍 {lang_pair.upper()} Results:")
        print("=" * 50)
        
        # Get test cases for this language
        test_cases = lang_data['test_data']
        error_cases = [case for case in test_cases if case['has_error']]
        total_cases = len(test_cases)
        error_count = len(error_cases)
        
        print(f"Total test cases: {total_cases}")
        print(f"Error cases: {error_count}")
        print(f"Good cases: {total_cases - error_count}")
        
        # Analyze each judge's performance
        for judge_name, judge_results in lang_data['judge_evaluations'].items():
            print(f"\n📊 {judge_name.upper()} Judge Performance:")
            
            # Calculate error detection
            correct_detections = 0
            false_positives = 0
            false_negatives = 0
            true_negatives = 0
            
            scores = []
            error_type_performance = {}
            
            for result in judge_results:
                test_case_id = result['test_case_id']
                judge_score = result['overall_score']
                scores.append(judge_score)
                
                # Find corresponding test case
                test_case = next((case for case in test_cases if case['id'] == test_case_id), None)
                if not test_case:
                    continue
                
                has_error = test_case['has_error']
                error_type = test_case['error_type']
                
                # Judge considers score <= 3 as error detection
                judge_detected_error = judge_score <= 3
                
                if has_error and judge_detected_error:
                    correct_detections += 1
                    if error_type not in error_type_performance:
                        error_type_performance[error_type] = {'detected': 0, 'total': 0}
                    error_type_performance[error_type]['detected'] += 1
                elif has_error and not judge_detected_error:
                    false_negatives += 1
                elif not has_error and judge_detected_error:
                    false_positives += 1
                elif not has_error and not judge_detected_error:
                    true_negatives += 1
                
                # Count total by error type
                if error_type != 'none':
                    if error_type not in error_type_performance:
                        error_type_performance[error_type] = {'detected': 0, 'total': 0}
                    error_type_performance[error_type]['total'] += 1
            
            # Calculate metrics
            error_detection_rate = (correct_detections / error_count) * 100 if error_count > 0 else 0
            precision = (correct_detections / (correct_detections + false_positives)) * 100 if (correct_detections + false_positives) > 0 else 0
            recall = (correct_detections / (correct_detections + false_negatives)) * 100 if (correct_detections + false_negatives) > 0 else 0
            
            print(f"   Error Detection Rate: {error_detection_rate:.1f}%")
            print(f"   Precision: {precision:.1f}%")
            print(f"   Recall: {recall:.1f}%")
            print(f"   Score Range: {min(scores)}-{max(scores)}")
            print(f"   Average Score: {sum(scores)/len(scores):.1f}")
            
            # Error type breakdown
            print(f"   Error Type Detection:")
            for error_type, perf in error_type_performance.items():
                if perf['total'] > 0:
                    detection_rate = (perf['detected'] / perf['total']) * 100
                    print(f"     {error_type}: {detection_rate:.1f}% ({perf['detected']}/{perf['total']})")
            
            # Store for cross-language comparison
            if lang_pair not in analysis['error_detection_by_language_and_judge']:
                analysis['error_detection_by_language_and_judge'][lang_pair] = {}
            
            analysis['error_detection_by_language_and_judge'][lang_pair][judge_name] = {
                'error_detection_rate': error_detection_rate,
                'precision': precision,
                'recall': recall,
                'score_range': (min(scores), max(scores)),
                'average_score': sum(scores)/len(scores),
                'error_type_performance': error_type_performance
            }
    
    # Create cross-language comparison table
    print(f"\n🔍 CROSS-LANGUAGE ERROR DETECTION COMPARISON:")
    print("=" * 70)
    
    # Create comparison table
    df_data = []
    for lang_pair in analysis['error_detection_by_language_and_judge']:
        for judge_name in analysis['error_detection_by_language_and_judge'][lang_pair]:
            data = analysis['error_detection_by_language_and_judge'][lang_pair][judge_name]
            df_data.append({
                'Language': lang_pair.upper(),
                'Judge': judge_name.replace('_', ' ').title(),
                'Error Detection %': f"{data['error_detection_rate']:.1f}%",
                'Precision %': f"{data['precision']:.1f}%",
                'Recall %': f"{data['recall']:.1f}%",
                'Avg Score': f"{data['average_score']:.1f}",
                'Score Range': f"{data['score_range'][0]}-{data['score_range'][1]}"
            })
    
    df = pd.DataFrame(df_data)
    print(df.to_string(index=False))
    
    # Summary by judge across languages
    print(f"\n📈 JUDGE PERFORMANCE ACROSS LANGUAGES:")
    print("=" * 50)
    
    for judge_name in ['basic', 'few_shot', 'multi_dimensional', 'back_translation']:
        print(f"\n🔸 {judge_name.replace('_', ' ').title()} Judge:")
        detection_rates = []
        for lang_pair in analysis['error_detection_by_language_and_judge']:
            if judge_name in analysis['error_detection_by_language_and_judge'][lang_pair]:
                rate = analysis['error_detection_by_language_and_judge'][lang_pair][judge_name]['error_detection_rate']
                detection_rates.append(rate)
                print(f"   {lang_pair.upper()}: {rate:.1f}%")
        
        if detection_rates:
            avg_rate = sum(detection_rates) / len(detection_rates)
            variance = sum((r - avg_rate)**2 for r in detection_rates) / len(detection_rates)
            print(f"   Average: {avg_rate:.1f}%")
            print(f"   Variance: {variance:.1f}")
            print(f"   Consistency: {'High' if variance < 25 else 'Medium' if variance < 100 else 'Low'}")
    
    return analysis

if __name__ == "__main__":
    # Run analysis on latest results
    results_file = "results/reliability_study_results_20250718_093219.json"
    analysis = analyze_results(results_file)