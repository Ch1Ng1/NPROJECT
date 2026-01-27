"""
Полезни функции за экспортиране и валидация на данни
"""
import csv
from datetime import datetime
from typing import List, Dict, Any
import logging
from io import StringIO

logger = logging.getLogger(__name__)


def export_predictions_to_csv(predictions: List[Dict[str, Any]]) -> str:
    """
    Експортира прогнози в CSV формат
    
    Args:
        predictions: Список с прогнози
        
    Returns:
        CSV строка
        
    Пример:
        csv_content = export_predictions_to_csv(predictions)
        with open('predictions.csv', 'w') as f:
            f.write(csv_content)
    """
    if not predictions:
        logger.warning("Няма прогнози за експортиране")
        return ""
    
    try:
        output = StringIO()
        fieldnames = [
            'Време', 'Лига', 'Домакин', 'Гост',
            'Домакин ELO', 'Гост ELO',
            'Вероятност 1', 'Вероятност X', 'Вероятност 2',
            'Препоръка', 'Увереност',
            'Over 2.5', 'Очаквани голове',
            'Очаквани картони', 'Очаквани корнери',
            'Домакин форма', 'Гост форма'
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for pred in predictions:
            writer.writerow({
                'Време': pred['time'],
                'Лига': pred['league'],
                'Домакин': pred['home_team'],
                'Гост': pred['away_team'],
                'Домакин ELO': pred['home_elo'],
                'Гост ELO': pred['away_elo'],
                'Вероятност 1': pred['probabilities']['1'],
                'Вероятност X': pred['probabilities']['X'],
                'Вероятност 2': pred['probabilities']['2'],
                'Препоръка': pred['prediction']['bet'],
                'Увереност': f"{pred['prediction']['confidence']}%",
                'Over 2.5': f"{pred['over_25']}%",
                'Очаквани голове': pred['expected_goals'],
                'Очаквани картони': pred.get('expected_yellow_cards', 0),
                'Очаквани корнери': pred.get('expected_corners', 0),
                'Домакин форма': pred['home_form'],
                'Гост форма': pred['away_form']
            })
        
        csv_content = output.getvalue()
        logger.info(f"✅ Експортирани {len(predictions)} прогнози в CSV")
        return csv_content
        
    except Exception as e:
        logger.error(f"❌ Грешка при експортиране на CSV: {e}")
        return ""


def filter_predictions(
    predictions: List[Dict[str, Any]],
    min_confidence: float = 0,
    max_confidence: float = 100,
    bet_type: str = None
) -> List[Dict[str, Any]]:
    """
    Филтрира прогнози по критерии
    
    Args:
        predictions: Список с прогнози
        min_confidence: Минимална увереност (0-100)
        max_confidence: Максимална увереност (0-100)
        bet_type: Тип прогноза ('1', 'X', '2' или None за всички)
        
    Returns:
        Филтрирани прогнози
    """
    filtered = []
    
    for pred in predictions:
        confidence = pred['prediction']['confidence']
        
        # Проверка на увереност
        if not (min_confidence <= confidence <= max_confidence):
            continue
        
        # Проверка на тип прогноза
        if bet_type and pred['prediction']['bet'] != bet_type:
            continue
        
        filtered.append(pred)
    
    logger.info(f"Филтрирани: {len(filtered)} от {len(predictions)} прогнози")
    return filtered


def get_high_confidence_predictions(predictions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Връща прогнози със висока увереност (>=60%)
    
    Args:
        predictions: Список с прогнози
        
    Returns:
        Прогнози със висока увереност
    """
    return filter_predictions(predictions, min_confidence=60)


def validate_prediction(prediction: Dict[str, Any]) -> bool:
    """
    Валидира структурата на прогноза
    
    Args:
        prediction: Прогноза за проверка
        
    Returns:
        True ако валидна, False иначе
    """
    required_keys = {
        'home_team', 'away_team', 'league', 'time',
        'probabilities', 'prediction', 'expected_goals'
    }
    
    if not isinstance(prediction, dict):
        return False
    
    if not all(key in prediction for key in required_keys):
        return False
    
    # Проверка на вероятности
    probs = prediction.get('probabilities', {})
    if not all(p in probs for p in ['1', 'X', '2']):
        return False
    
    # Сума на вероятностите трябва да е ~100
    prob_sum = sum(probs.values())
    if not (95 <= prob_sum <= 105):
        return False
    
    return True
