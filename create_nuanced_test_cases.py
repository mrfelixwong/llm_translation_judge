#!/usr/bin/env python3
"""
Create more nuanced test cases that differentiate judge capabilities.

The current test case ("immediately" → "later") is too obvious - all judges detect it.
We need subtle errors where multi-dimensional analysis shows its value.
"""

import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.judges import BasicJudge, FewShotJudge, MultiDimensionalJudge, MultiDimensionalJudgeOriginal

def create_nuanced_test_cases():
    """Create sophisticated test cases that should differentiate judge performance."""
    
    test_cases = [
        {
            "id": "nuanced_001",
            "source_text": "The confidential report should be shared with authorized personnel only.",
            "translated_text": "El informe confidencial debe ser compartido con todo el personal.",
            "source_lang": "en",
            "target_lang": "es",
            "error_type": "subtle_omission",
            "error_description": "Missing 'only' - critical meaning change but grammatically correct",
            "has_error": True,
            "human_score": 2.0,
            "error_severity": "high",
            "why_challenging": "Perfect grammar and fluency, only accuracy is compromised"
        },
        {
            "id": "nuanced_002", 
            "source_text": "Please increase the budget by approximately 15% for next quarter.",
            "translated_text": "Por favor, aumenta el presupuesto en aproximadamente 25% para el próximo trimestre.",
            "source_lang": "en",
            "target_lang": "es", 
            "error_type": "numerical_error",
            "error_description": "15% changed to 25% - subtle but critical financial error",
            "has_error": True,
            "human_score": 2.5,
            "error_severity": "high",
            "why_challenging": "Small numerical change, perfect fluency and completeness"
        },
        {
            "id": "nuanced_003",
            "source_text": "The meeting is scheduled for 2:30 PM on Tuesday.",
            "translated_text": "La reunión está programada para las 2:30 PM del martes.",
            "source_lang": "en", 
            "target_lang": "es",
            "error_type": "none",
            "error_description": "Perfect translation - control case",
            "has_error": False,
            "human_score": 5.0,
            "error_severity": "none",
            "why_challenging": "Should score high across all dimensions"
        },
        {
            "id": "nuanced_004",
            "source_text": "Due to regulatory compliance requirements, all data must be encrypted.",
            "translated_text": "Debido a los requisitos normativos, todos los datos deben estar encriptados.",
            "source_lang": "en",
            "target_lang": "es",
            "error_type": "subtle_omission", 
            "error_description": "Missing 'compliance' - changes legal meaning",
            "has_error": True,
            "human_score": 3.0,
            "error_severity": "medium",
            "why_challenging": "Technical term omission, otherwise perfect translation"
        },
        {
            "id": "nuanced_005",
            "source_text": "The system will be unavailable from 9 AM to 11 AM for maintenance.",
            "translated_text": "El sistema no estará disponible de 9 AM a 1 PM para mantenimiento.",
            "source_lang": "en",
            "target_lang": "es",
            "error_type": "time_error",
            "error_description": "11 AM changed to 1 PM - extends maintenance window",
            "has_error": True,
            "human_score": 2.8,
            "error_severity": "medium", 
            "why_challenging": "Small time difference but significant operational impact"
        }
    ]
    
    return test_cases

def test_judges_on_nuanced_cases():
    """Test all judges on nuanced cases to see performance differences."""
    
    # Initialize judges
    judges = {
        "basic": BasicJudge(),
        "few_shot": FewShotJudge(), 
        "multi_dimensional": MultiDimensionalJudge(),
        "multi_dimensional_original": MultiDimensionalJudgeOriginal()
    }
    
    test_cases = create_nuanced_test_cases()
    
    print("🔬 TESTING JUDGES ON NUANCED CASES")
    print("=" * 50)
    print()
    
    results = {}
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"TEST CASE {i}: {test_case['error_description']}")
        print(f"Source: {test_case['source_text']}")
        print(f"Translation: {test_case['translated_text']}")
        print(f"Expected: {'ERROR' if test_case['has_error'] else 'GOOD'} (Human: {test_case['human_score']}/5)")
        print()
        
        case_results = {}
        
        for judge_name, judge in judges.items():
            try:
                result = judge.evaluate(
                    test_case["source_text"],
                    test_case["translated_text"],
                    test_case["source_lang"],
                    test_case["target_lang"]
                )
                
                score = result["overall_score"]
                case_results[judge_name] = {
                    "score": score,
                    "detected_error": score <= 3 if test_case["has_error"] else score >= 4,
                    "reasoning": result.get("notes", "")[:100] + "..."
                }
                
                # Show results
                if test_case["has_error"]:
                    detection = "✅ DETECTED" if score <= 3 else "❌ MISSED"
                else:
                    detection = "✅ CORRECT" if score >= 4 else "❌ TOO LOW"
                    
                print(f"  {judge_name.replace('_', ' ').title()}: {score}/5 {detection}")
                
            except Exception as e:
                print(f"  {judge_name}: ERROR - {e}")
                case_results[judge_name] = {"score": 0, "detected_error": False, "error": str(e)}
        
        results[test_case["id"]] = case_results
        print()
        print("-" * 40)
        print()
    
    # Summary analysis
    print("📊 SUMMARY ANALYSIS")
    print("=" * 30)
    print()
    
    judge_performance = {}
    for judge_name in judges.keys():
        correct = 0
        total = 0
        
        for test_case in test_cases:
            case_id = test_case["id"]
            if case_id in results and judge_name in results[case_id]:
                if "error" not in results[case_id][judge_name]:
                    total += 1
                    if results[case_id][judge_name]["detected_error"]:
                        correct += 1
        
        accuracy = (correct / total * 100) if total > 0 else 0
        judge_performance[judge_name] = accuracy
        
        print(f"{judge_name.replace('_', ' ').title()}: {accuracy:.1f}% ({correct}/{total})")
    
    print()
    print("🎯 KEY INSIGHTS:")
    best_judge = max(judge_performance.items(), key=lambda x: x[1])
    worst_judge = min(judge_performance.items(), key=lambda x: x[1])
    
    print(f"Best: {best_judge[0].replace('_', ' ').title()} ({best_judge[1]:.1f}%)")
    print(f"Worst: {worst_judge[0].replace('_', ' ').title()} ({worst_judge[1]:.1f}%)")
    
    if judge_performance["multi_dimensional"] > judge_performance["basic"]:
        improvement = judge_performance["multi_dimensional"] - judge_performance["basic"]
        print(f"Multi-Dimensional advantage: +{improvement:.1f} percentage points")
    
    return results

if __name__ == "__main__":
    # Test the nuanced cases
    results = test_judges_on_nuanced_cases()
    
    # Save results 
    with open("nuanced_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to nuanced_test_results.json")