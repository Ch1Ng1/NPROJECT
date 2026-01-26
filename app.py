"""
⚽ Smart Football Predictor - Интелигентни прогнози за футбол
Използва ELO рейтинг, форма, H2H и xG статистики

Методология:
- ELO рейтинг: Математически модел за сила на отборите
- Форма: Последни 5 резултата (W/D/L)
- Статистики: Средни голове, защита, xG
- Комбинация: Интегрирана прогноза с ниво на увереност
"""
import os
from flask import Flask, render_template, jsonify, Response
from datetime import datetime, timedelta
import logging
from functools import wraps
from typing import Dict, Any, List
from predictor import SmartPredictor
from utils import export_predictions_to_csv, get_high_confidence_predictions
from dotenv import load_dotenv

# Зареждане на .env
load_dotenv()

# Logging конфигурация
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Кеш за последните прогнози
_predictions_cache: Dict[str, Any] = {
    'data': None,
    'timestamp': None,
    'cache_duration': 3600  # 1 час
}

# Инициализация
API_KEY = os.getenv('API_FOOTBALL_KEY', '')
if not API_KEY:
    logger.warning("⚠️  API ключ не е конфигуриран. Продължаване без API функционалност.")
    
predictor = SmartPredictor(api_key=API_KEY)

def _is_cache_valid() -> bool:
    """Проверява дали кешът е все още валиден"""
    if _predictions_cache['data'] is None or _predictions_cache['timestamp'] is None:
        return False
    elapsed = (datetime.now() - _predictions_cache['timestamp']).total_seconds()
    return elapsed < _predictions_cache['cache_duration']

def _get_cached_predictions() -> List[Dict[str, Any]]:
    """Връща кеширани прогнози или праз списък"""
    if _is_cache_valid():
        logger.info("💾 Използвам кеширани прогнози")
        return _predictions_cache['data']
    return []

def _update_predictions_cache(predictions: List[Dict[str, Any]]) -> None:
    """Актуализира кеша на прогнозите"""
    _predictions_cache['data'] = predictions
    _predictions_cache['timestamp'] = datetime.now()
    logger.info(f"💾 Кеш актуализиран с {len(predictions)} прогнози")

@app.route('/')
def index() -> str:
    """Главна страница"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Грешка при зареждане на главна страница: {e}")
        return "Грешка при зареждане на страницата", 500

@app.route('/api/predictions')
def get_predictions() -> tuple[Response, int]:
    """
    Връща прогнози за днес с кеширане
    
    Returns:
        JSON response с прогнози или грешка
    """
    try:
        # Проверяване на API ключ
        if not API_KEY:
            return jsonify({
                'success': False,
                'error': 'API ключ не е конфигуриран. Настрой API_FOOTBALL_KEY в .env файла.'
            }), 400
        
        # Използвай кеширани прогнози ако са валидни
        cached = _get_cached_predictions()
        if cached:
            return jsonify({
                'success': True,
                'total': len(cached),
                'predictions': cached,
                'source': 'cache'
            }), 200
        
        # Генериране на нови прогнози
        logger.info("📊 Генериране на нови прогнози...")
        predictions = predictor.get_today_predictions()
        
        # Кеширане на резултата
        _update_predictions_cache(predictions)
        
        return jsonify({
            'success': True,
            'total': len(predictions),
            'predictions': predictions,
            'source': 'fresh'
        }), 200
        
    except ValueError as e:
        logger.error(f"Валидационна грешка: {e}")
        return jsonify({
            'success': False,
            'error': f'Валидационна грешка: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"Критична грешка при генериране на прогнози: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Грешка при генериране на прогнози. Опитай отново по-късно.'
        }), 503

@app.route('/api/stats')
def get_stats() -> tuple[Response, int]:
    """
    Връща статистики за системата
    
    Returns:
        JSON response със статистики
    """
    try:
        stats = predictor.get_stats()
        stats['cache_valid'] = _is_cache_valid()
        if _predictions_cache['timestamp']:
            stats['cache_age_seconds'] = (datetime.now() - _predictions_cache['timestamp']).total_seconds()
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Грешка при генериране на статистики: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/refresh')
def refresh_cache() -> tuple[Response, int]:
    """
    Принудително обновяване на кеша
    
    Returns:
        JSON response със статус
    """
    try:
        _predictions_cache['data'] = None
        _predictions_cache['timestamp'] = None
        logger.info("🔄 Кеш очищен, новите прогнози ще бъдат генерирани при следващата заявка")
        return jsonify({
            'success': True,
            'message': 'Кеш очищен успешно'
        }), 200
    except Exception as e:
        logger.error(f"Грешка при очищаване на кеша: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/csv')
def export_csv() -> tuple[Response, int]:
    """
    Експортира текущите прогнози като CSV
    
    Returns:
        CSV файл за сваляне
    """
    try:
        # Получи текущите прогнози (от кеша или генериране на нови)
        cached = _get_cached_predictions()
        if cached:
            predictions = cached
        else:
            if not API_KEY:
                return jsonify({'error': 'API ключ не е конфигуриран'}), 400
            predictions = predictor.get_today_predictions()
            _update_predictions_cache(predictions)
        
        # Експортиране в CSV
        csv_content = export_predictions_to_csv(predictions)
        
        if not csv_content:
            return jsonify({'error': 'Няма прогнози за експортиране'}), 400
        
        response = Response(csv_content, mimetype='text/csv')
        response.headers['Content-Disposition'] = f'attachment; filename=predictions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        
        logger.info(f"📥 Експортирани прогнози в CSV формат")
        return response, 200
        
    except Exception as e:
        logger.error(f"Грешка при експортиране: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/high-confidence')
def get_high_confidence() -> tuple[Response, int]:
    """
    Връща само прогнози със висока увереност (>=60%)
    
    Returns:
        JSON response с филтрирани прогнози
    """
    try:
        if not API_KEY:
            return jsonify({
                'success': False,
                'error': 'API ключ не е конфигуриран'
            }), 400
        
        cached = _get_cached_predictions()
        if cached:
            predictions = cached
        else:
            predictions = predictor.get_today_predictions()
            _update_predictions_cache(predictions)
        
        high_conf = get_high_confidence_predictions(predictions)
        
        return jsonify({
            'success': True,
            'total': len(high_conf),
            'predictions': high_conf
        }), 200
        
    except Exception as e:
        logger.error(f"Грешка при филтриране: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(500)
def internal_error(error: Any) -> tuple[Response, int]:
    """Обработка на 500 грешки"""
    logger.error(f"500 Вътрешна сърверна грешка: {error}")
    return jsonify({'error': 'Вътрешна сърверна грешка'}), 500

if __name__ == '__main__':
    # Създавање на logs директория
    os.makedirs('logs', exist_ok=True)
    
    logger.info("🚀 Стартиране на Smart Football Predictor")
    logger.info(f"📍 Сървър: http://0.0.0.0:5000")
    logger.info(f"🔑 API конфигурирано: {bool(API_KEY)}")
    
    app.run(
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', 5000))
    )
