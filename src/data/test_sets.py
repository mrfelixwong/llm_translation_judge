#!/usr/bin/env python3
"""
Test data sets for LLM judge evaluation.

This module provides standardized test sets for evaluating judge reliability
across different language pairs and error types.
"""

import json
import random
from typing import List, Dict, Any, Optional
from pathlib import Path


def load_test_set(language_pair: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Load test set for a specific language pair.
    
    Args:
        language_pair: Language pair code (e.g., 'en-es', 'en-fr')
        limit: Maximum number of test cases to return
        
    Returns:
        List of test case dictionaries
    """
    
    # Check if test data file exists
    data_dir = Path(__file__).parent / "test_sets"
    test_file = data_dir / f"{language_pair}_test_set.json"
    
    if test_file.exists():
        with open(test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            test_cases = data.get('test_cases', [])
    else:
        # Generate synthetic test data
        test_cases = generate_synthetic_test_set(language_pair, limit or 50)
    
    if limit:
        test_cases = test_cases[:limit]
    
    return test_cases


def generate_synthetic_test_set(language_pair: str, size: int = 50) -> List[Dict[str, Any]]:
    """
    Generate synthetic test data for evaluation.
    
    Args:
        language_pair: Language pair code
        size: Number of test cases to generate
        
    Returns:
        List of synthetic test cases
    """
    
    source_lang, target_lang = language_pair.split('-')
    
    # Base templates for different error types
    templates = {
        "en-es": {
            "good": [
                ("Hello, how are you today?", "Hola, ¿cómo estás hoy?"),
                ("Please send the report by Friday.", "Por favor, envía el informe antes del viernes."),
                ("The meeting is scheduled for next week.", "La reunión está programada para la próxima semana."),
                ("Thank you for your assistance.", "Gracias por tu ayuda."),
                ("We need to review the proposal.", "Necesitamos revisar la propuesta.")
            ],
            "factual_error": [
                ("The meeting is on Monday.", "La reunión es el miércoles."),  # Wrong day
                ("Send it by 3 PM.", "Envíalo a las 5 PM."),  # Wrong time
                ("Call me at 555-1234.", "Llámame al 555-5678."),  # Wrong number
                ("The price is $50.", "El precio es $30."),  # Wrong amount
                ("Meet in room 302.", "Nos vemos en la sala 205.")  # Wrong room
            ],
            "omission": [
                ("Please send the urgent report by Friday.", "Por favor, envía el informe el viernes."),  # Missing "urgent"
                ("Call me tomorrow at 2 PM.", "Llámame mañana."),  # Missing time
                ("The blue car in the parking lot.", "El coche en el estacionamiento."),  # Missing "blue"
                ("Bring your ID and passport.", "Trae tu pasaporte."),  # Missing "ID"
                ("The meeting starts at 9 AM sharp.", "La reunión comienza a las 9 AM.")  # Missing "sharp"
            ],
            "mistranslation": [
                ("Please turn off the lights.", "Por favor, enciende las luces."),  # Turn off -> turn on
                ("The report is confidential.", "El informe es público."),  # Confidential -> public
                ("Send the email immediately.", "Envía el email más tarde."),  # Immediately -> later
                ("The software is free.", "El software es caro."),  # Free -> expensive
                ("Close the door gently.", "Abre la puerta con fuerza.")  # Close gently -> open forcefully
            ]
        },
        "en-fr": {
            "good": [
                ("Good morning, everyone.", "Bonjour tout le monde."),
                ("Please review the attached document.", "Veuillez examiner le document ci-joint."),
                ("We appreciate your feedback.", "Nous apprécions vos commentaires."),
                ("The deadline is next Tuesday.", "La date limite est mardi prochain."),
                ("Thank you for your patience.", "Merci pour votre patience.")
            ],
            "factual_error": [
                ("The appointment is at 10 AM.", "Le rendez-vous est à 14h."),  # Wrong time
                ("The building is on 5th Street.", "Le bâtiment est sur la 8ème rue."),  # Wrong street
                ("The cost is 100 euros.", "Le coût est de 200 euros."),  # Wrong amount
                ("Room number 15.", "Chambre numéro 25."),  # Wrong number
                ("Due on January 15th.", "À rendre le 20 janvier.")  # Wrong date
            ],
            "omission": [
                ("Please send the final version.", "Veuillez envoyer la version."),  # Missing "final"
                ("Call me after 6 PM today.", "Appelez-moi aujourd'hui."),  # Missing time
                ("The red folder on my desk.", "Le dossier sur mon bureau."),  # Missing "red"
                ("Urgent: Review immediately.", "Réviser immédiatement."),  # Missing "Urgent"
                ("Confidential and sensitive information.", "Informations confidentielles.")  # Missing "sensitive"
            ],
            "mistranslation": [
                ("The door is open.", "La porte est fermée."),  # Open -> closed
                ("Accept the invitation.", "Refuser l'invitation."),  # Accept -> refuse
                ("Save the changes.", "Supprimer les modifications."),  # Save -> delete
                ("Enable notifications.", "Désactiver les notifications."),  # Enable -> disable
                ("Increase the volume.", "Diminuer le volume.")  # Increase -> decrease
            ]
        }
    }
    
    # Get templates for this language pair, fallback to English-Spanish
    lang_templates = templates.get(language_pair, templates["en-es"])
    
    test_cases = []
    
    # Calculate distribution of error types
    good_count = int(size * 0.4)  # 40% good translations
    error_count = size - good_count
    error_per_type = error_count // 3
    
    case_id = 1
    
    # Generate good translations
    for _ in range(good_count):
        source, translation = random.choice(lang_templates["good"])
        test_cases.append({
            "id": f"test_{case_id:03d}",
            "source_text": source,
            "translated_text": translation,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "error_type": "none",
            "has_error": False,
            "human_score": round(random.uniform(4.0, 5.0), 1),  # High scores for good translations
            "error_severity": "none"
        })
        case_id += 1
    
    # Generate error cases
    error_types = ["factual_error", "omission", "mistranslation"]
    
    for error_type in error_types:
        for _ in range(error_per_type):
            source, translation = random.choice(lang_templates[error_type])
            
            # Assign human scores based on error severity
            if error_type == "factual_error":
                human_score = round(random.uniform(1.5, 2.5), 1)  # Severe errors
                severity = "high"
            elif error_type == "omission":
                human_score = round(random.uniform(2.5, 3.5), 1)  # Moderate errors
                severity = "medium"
            else:  # mistranslation
                human_score = round(random.uniform(1.5, 3.0), 1)  # Variable severity
                severity = random.choice(["medium", "high"])
            
            test_cases.append({
                "id": f"test_{case_id:03d}",
                "source_text": source,
                "translated_text": translation,
                "source_lang": source_lang,
                "target_lang": target_lang,
                "error_type": error_type,
                "has_error": True,
                "human_score": human_score,
                "error_severity": severity
            })
            case_id += 1
    
    # Fill remaining cases with random selections
    while len(test_cases) < size:
        error_type = random.choice(["none"] + error_types)
        
        if error_type == "none":
            source, translation = random.choice(lang_templates["good"])
            has_error = False
            human_score = round(random.uniform(4.0, 5.0), 1)
            severity = "none"
        else:
            source, translation = random.choice(lang_templates[error_type])
            has_error = True
            if error_type == "factual_error":
                human_score = round(random.uniform(1.5, 2.5), 1)
                severity = "high"
            elif error_type == "omission":
                human_score = round(random.uniform(2.5, 3.5), 1)
                severity = "medium"
            else:
                human_score = round(random.uniform(1.5, 3.0), 1)
                severity = random.choice(["medium", "high"])
        
        test_cases.append({
            "id": f"test_{case_id:03d}",
            "source_text": source,
            "translated_text": translation,
            "source_lang": source_lang,
            "target_lang": target_lang,
            "error_type": error_type,
            "has_error": has_error,
            "human_score": human_score,
            "error_severity": severity
        })
        case_id += 1
    
    # Shuffle to randomize order
    random.shuffle(test_cases)
    
    return test_cases[:size]


def get_available_language_pairs() -> List[str]:
    """
    Get list of available language pairs.
    
    Returns:
        List of language pair codes
    """
    return ["en-es", "en-fr", "en-de", "en-it", "en-pt"]


# Generate and save test sets if run directly
if __name__ == "__main__":
    print("Generating test sets...")
    
    for lang_pair in ["en-es", "en-fr"]:
        print(f"Generating {lang_pair} test set...")
        test_cases = generate_synthetic_test_set(lang_pair, 50)
        
        print(f"  Generated {len(test_cases)} test cases")
        error_dist = {}
        for case in test_cases:
            error_type = case.get("error_type", "unknown")
            error_dist[error_type] = error_dist.get(error_type, 0) + 1
        
        for error_type, count in error_dist.items():
            print(f"    {error_type}: {count}")
    
    print("Test sets generated successfully!")