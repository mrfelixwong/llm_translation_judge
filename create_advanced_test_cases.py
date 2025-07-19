#!/usr/bin/env python3
"""
Create advanced test cases that should show multi-dimensional judge's advantages.

These cases target specific scenarios where dimensional analysis provides value:
1. Multi-faceted errors (good in some dimensions, bad in others)
2. Context-dependent accuracy issues  
3. Subtle tone/register mismatches
4. Complex technical translations
"""

import json
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.judges import BasicJudge, FewShotJudge, MultiDimensionalJudge, MultiDimensionalJudgeOriginal

def create_advanced_test_cases():
    """Create test cases designed to showcase multi-dimensional analysis."""
    
    test_cases = [
        {
            "id": "advanced_001",
            "source_text": "Please submit your quarterly financial reports by the deadline to avoid penalties.",
            "translated_text": "Por favor presenta tus reportes financieros trimestrales antes de la fecha límite para evitar multas.",
            "source_lang": "en",
            "target_lang": "es",
            "error_type": "register_mismatch", 
            "error_description": "Formal → informal tone (submit→presenta, your→tus)",
            "has_error": True,
            "human_score": 3.5,
            "error_severity": "medium",
            "expected_dimensions": {
                "accuracy": 5, "completeness": 5, "fluency": 5, "appropriateness": 2
            },
            "why_challenging": "Perfect accuracy/fluency, but inappropriate register for business context"
        },
        {
            "id": "advanced_002",
            "source_text": "The API rate limit is 1000 requests per minute with burst capacity of 1500.",
            "translated_text": "El límite de velocidad de la API es de 1000 solicitudes por minuto con capacidad de ráfaga de 1500.",
            "source_lang": "en", 
            "target_lang": "es",
            "error_type": "none",
            "error_description": "Perfect technical translation",
            "has_error": False,
            "human_score": 5.0,
            "error_severity": "none",
            "expected_dimensions": {
                "accuracy": 5, "completeness": 5, "fluency": 5, "appropriateness": 5  
            },
            "why_challenging": "Technical terminology correctly preserved"
        },
        {
            "id": "advanced_003",
            "source_text": "The database backup failed due to insufficient disk space on the primary server.",
            "translated_text": "La copia de seguridad de la base de datos falló debido a espacio insuficiente en el servidor principal.",
            "source_lang": "en",
            "target_lang": "es", 
            "error_type": "subtle_omission",
            "error_description": "Missing 'disk' - changes technical meaning",
            "has_error": True,
            "human_score": 3.8,
            "error_severity": "medium",
            "expected_dimensions": {
                "accuracy": 3, "completeness": 4, "fluency": 5, "appropriateness": 5
            },
            "why_challenging": "Subtle technical omission, otherwise perfect"
        },
        {
            "id": "advanced_004", 
            "source_text": "Could you please review the draft proposal and provide feedback by Friday?",
            "translated_text": "¿Puedes revisar la propuesta preliminar y dar comentarios antes del viernes?",
            "source_lang": "en",
            "target_lang": "es",
            "error_type": "register_shift",
            "error_description": "Formal polite → casual (Could you please → Puedes)",
            "has_error": True, 
            "human_score": 4.0,
            "error_severity": "low",
            "expected_dimensions": {
                "accuracy": 5, "completeness": 5, "fluency": 5, "appropriateness": 3
            },
            "why_challenging": "Perfect meaning preservation but inappropriate casualness"
        },
        {
            "id": "advanced_005",
            "source_text": "The emergency evacuation procedure must be followed precisely during fire drills.",
            "translated_text": "El procedimiento de evacuación de emergencia debe seguirse aproximadamente durante los simulacros de incendio.",
            "source_lang": "en",
            "target_lang": "es",
            "error_type": "critical_accuracy",
            "error_description": "precisely → approximately (opposite meaning for safety)",
            "has_error": True,
            "human_score": 1.5,
            "error_severity": "critical",
            "expected_dimensions": {
                "accuracy": 1, "completeness": 5, "fluency": 5, "appropriateness": 5
            },
            "why_challenging": "Critical safety error but perfect grammar/completeness"
        }
    ]
    
    return test_cases

def test_dimensional_analysis():
    """Test to see if multi-dimensional judge shows its analytical value."""
    
    judges = {
        "basic": BasicJudge(),
        "few_shot": FewShotJudge(),
        "multi_dimensional": MultiDimensionalJudge(),
        "multi_dimensional_original": MultiDimensionalJudgeOriginal()
    }
    
    test_cases = create_advanced_test_cases()
    
    print("🔬 ADVANCED TEST: MULTI-DIMENSIONAL ANALYSIS VALUE")
    print("=" * 60)
    print()
    
    all_results = {}
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"TEST CASE {i}: {test_case['error_description']}")
        print(f"Source: {test_case['source_text']}")
        print(f"Translation: {test_case['translated_text']}")
        print(f"Expected Impact: {test_case['error_severity']}")
        
        if 'expected_dimensions' in test_case:
            exp_dims = test_case['expected_dimensions']
            print(f"Expected Dimensions: Acc:{exp_dims['accuracy']} Com:{exp_dims['completeness']} Flu:{exp_dims['fluency']} App:{exp_dims['appropriateness']}")
        
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
                
                # Check error detection
                if test_case["has_error"]:
                    detection = "✅ DETECTED" if score <= 3 else "❌ MISSED"
                else:
                    detection = "✅ CORRECT" if score >= 4 else "❌ TOO LOW"
                
                # Show dimensional breakdown for multi-dimensional judges
                dim_info = ""
                if "dimensional_scores" in result:
                    dims = result["dimensional_scores"]
                    dim_scores = []
                    for dim in ["accuracy", "completeness", "fluency", "appropriateness"]:
                        if dim in dims:
                            dim_scores.append(f"{dim[:3].title()}:{dims[dim]['score']}")
                    if dim_scores:
                        dim_info = f" ({', '.join(dim_scores)})"
                
                print(f"  {judge_name.replace('_', ' ').title()}: {score}/5 {detection}{dim_info}")
                
                case_results[judge_name] = {
                    "score": score,
                    "detected_correctly": (score <= 3) == test_case["has_error"],
                    "dimensional_scores": result.get("dimensional_scores", {}),
                    "reasoning": result.get("notes", "")[:150]
                }
                
            except Exception as e:
                print(f"  {judge_name}: ERROR - {e}")
                case_results[judge_name] = {"error": str(e)}
        
        all_results[test_case["id"]] = case_results
        print()
        print("-" * 50)
        print()
    
    # Performance analysis
    print("📊 ADVANCED PERFORMANCE ANALYSIS")
    print("=" * 40)
    print()
    
    judge_performance = {}
    for judge_name in judges.keys():
        correct = 0
        total = 0
        
        for test_case in test_cases:
            case_id = test_case["id"]
            if case_id in all_results and judge_name in all_results[case_id]:
                if "error" not in all_results[case_id][judge_name]:
                    total += 1
                    if all_results[case_id][judge_name]["detected_correctly"]:
                        correct += 1
        
        accuracy = (correct / total * 100) if total > 0 else 0
        judge_performance[judge_name] = accuracy
        
        print(f"{judge_name.replace('_', ' ').title()}: {accuracy:.1f}% ({correct}/{total})")
    
    # Specific analysis for multi-dimensional strengths
    print()
    print("🎯 MULTI-DIMENSIONAL ANALYSIS:")
    print()
    
    # Check if multi-dimensional judge provides better insights
    md_cases = []
    for test_case in test_cases:
        case_id = test_case["id"]
        if case_id in all_results and "multi_dimensional" in all_results[case_id]:
            md_result = all_results[case_id]["multi_dimensional"]
            if "dimensional_scores" in md_result:
                md_cases.append((test_case, md_result))
    
    if md_cases:
        print("Dimensional Analysis Examples:")
        for test_case, result in md_cases[:3]:  # Show first 3
            print(f"  {test_case['error_description']}:")
            dims = result["dimensional_scores"]
            for dim, data in dims.items():
                print(f"    {dim.title()}: {data['score']}/5 - {data['reasoning'][:60]}...")
            print()
    
    return all_results

if __name__ == "__main__":
    results = test_dimensional_analysis()
    
    # Save detailed results
    with open("advanced_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("Detailed results saved to advanced_test_results.json")