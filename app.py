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
import json
from functools import wraps
from typing import Dict, Any, List, Optional
from predictor import SmartPredictor
from utils import export_predictions_to_csv, get_high_confidence_predictions
from database import get_database, DatabaseManager
from dotenv import load_dotenv

# Зареждане на .env
load_dotenv()

# Валидация на API ключ
API_KEY = os.getenv('API_FOOTBALL_KEY')
if not API_KEY:
    print("⚠️  ВНИМАНИЕ: API_FOOTBALL_KEY не е задан в .env файла")
    print("Някои функции няма да работят. Настрой го в .env файла.")

# Logging конфигурация (безопасно за Windows конзола)
class _StripNonAsciiFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        try:
            msg = record.getMessage()
            # Премахва символи извън ASCII за избягване на UnicodeEncodeError в конзолата
            safe = msg.encode('ascii', 'ignore').decode('ascii')
            # Запазва оригиналния текст за файловия лог
            record.msg = safe if record.args == () else safe % record.args
        except Exception:
            pass
        return True

file_handler = logging.FileHandler('logs/app.log', encoding='utf-8')
stream_handler = logging.StreamHandler()
stream_handler.addFilter(_StripNonAsciiFilter())

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[file_handler, stream_handler]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['JSON_AS_ASCII'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Кеш за последните прогнози
_predictions_cache: Dict[str, Any] = {
    'data': None,
    'timestamp': None,
    'cache_duration': 86400  # 24 часа
}

CACHE_FILE = 'cache/predictions_cache.json'

# Инициализация
if not API_KEY:
    logger.warning("⚠️  API ключ не е конфигуриран. Продължаване без API функционалност.")
    
try:
    predictor = SmartPredictor(api_key=API_KEY) if API_KEY else None
except Exception as e:
    logger.error(f"❌ Грешка при инициализация на predictor: {e}")
    predictor = None

# Инициализиране на базата данни
db: Optional[DatabaseManager] = None

def init_database() -> bool:
    """Инициализира връзката към базата данни"""
    global db
    try:
        db = get_database()
        if db and db.connection and db.connection.is_connected():
            logger.info("✅ Базата данни инициализирана успешно")
            return True
        else:
            logger.warning("⚠️  Не може да се свърже към базата данни")
            db = None
            return False
    except Exception as e:
        logger.error(f"❌ Грешка при инициализиране на базата: {e}")
        db = None
        return False

# Зареждане на кеш от файл
def _load_cache_from_file():
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                timestamp_str = cache_data.get('timestamp')
                if timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    # Проверка дали е от днес
                    if timestamp.date() == datetime.now().date():
                        _predictions_cache['data'] = cache_data.get('data', [])
                        _predictions_cache['timestamp'] = timestamp
                        logger.info("💾 Зареден кеш от файл")
                    else:
                        logger.info("🗑️  Кешът е от стар ден, изтриване")
    except Exception as e:
        logger.error(f"❌ Грешка при зареждане на кеш: {e}")

_load_cache_from_file()

def _is_cache_valid() -> bool:
    """Проверява дали кешът е все още валиден"""
    if _predictions_cache['data'] is None or _predictions_cache['timestamp'] is None:
        return False
    elapsed = (datetime.now() - _predictions_cache['timestamp']).total_seconds()
    return elapsed < _predictions_cache['cache_duration']

def _get_cached_predictions() -> List[Dict[str, Any]]:
    """Връща кеширани прогнози от базата или праз списък"""
    today = datetime.now().strftime('%Y-%m-%d')
    if db:
        try:
            cursor = db.connection.cursor()
            cursor.execute("SELECT predictions FROM predictions_cache WHERE date = %s", (today,))
            result = cursor.fetchone()
            cursor.close()
            if result:
                predictions = json.loads(result[0])
                logger.info(f"💾 Заредени {len(predictions)} прогнози от базата за {today}")
                # Зареди в in-memory cache
                _predictions_cache['data'] = predictions
                _predictions_cache['timestamp'] = datetime.now()
                return predictions
        except Exception as e:
            logger.error(f"❌ Грешка при четене от кеша: {e}")
    
    # Fallback to in-memory cache
    if _is_cache_valid():
        logger.info("💾 Използвам in-memory кеширани прогнози")
        return _predictions_cache['data']
    return []

def _save_predictions_to_db(predictions: List[Dict[str, Any]]) -> int:
    """Запазва прогнозите в базата данни"""
    saved_count = 0
    if not db:
        return 0
    
    try:
        for pred in predictions:
            try:
                # Добавяне на отбори ако не съществуват
                home_team_id = db.add_team(
                    api_id=pred.get('home_team_id', 0),
                    name=pred.get('home_team', 'Unknown'),
                    league=pred.get('league', 'Unknown')
                )
                away_team_id = db.add_team(
                    api_id=pred.get('away_team_id', 0),
                    name=pred.get('away_team', 'Unknown'),
                    league=pred.get('league', 'Unknown')
                )
                
                if not home_team_id or not away_team_id:
                    continue
                
                # Добавяне на мач
                try:
                    match_time = datetime.fromisoformat(pred.get('time', datetime.now().isoformat()))
                except:
                    match_time = datetime.now()
                
                match_id = db.add_match(
                    api_id=pred.get('match_id', 0),
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                    match_date=match_time,
                    league=pred.get('league', 'Unknown'),
                    status='pending'
                )
                
                if not match_id:
                    continue
                
                # Запазване на прогноза
                probs = pred.get('probabilities', {})
                pred_data = pred.get('prediction', {})
                
                # Валидация на данни преди запис
                home_form = str(pred.get('home_form', ''))[:50]  # Лимит 50 символа
                away_form = str(pred.get('away_form', ''))[:50]
                
                prediction_id = db.save_prediction(
                    match_id=match_id,
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                    home_elo=float(pred.get('home_elo', 1500)),
                    away_elo=float(pred.get('away_elo', 1500)),
                    probability_home=float(probs.get('1', 0)),
                    probability_draw=float(probs.get('X', 0)),
                    probability_away=float(probs.get('2', 0)),
                    prediction_bet=str(pred_data.get('bet', ''))[:10],
                    confidence=int(pred_data.get('confidence', 0)),
                    expected_goals=float(pred.get('expected_goals', 0)),
                    over_25_probability=float(pred.get('over_25', 0)),
                    expected_yellow_cards=float(pred.get('expected_yellow_cards', 3.6)),
                    expected_corners=float(pred.get('expected_corners', 8.4)),
                    home_form=home_form,
                    away_form=away_form,
                    home_avg_goals_for=float(pred.get('home_avg_goals_for', 0)),
                    home_avg_goals_against=float(pred.get('home_avg_goals_against', 0)),
                    away_avg_goals_for=float(pred.get('away_avg_goals_for', 0)),
                    away_avg_goals_against=float(pred.get('away_avg_goals_against', 0)),
                    match_date=match_time
                )
                
                if prediction_id:
                    saved_count += 1
                    logger.debug(f"✅ Прогноза съхранена: {pred.get('home_team')} vs {pred.get('away_team')}")
            except Exception as e:
                logger.warning(f"⚠️  Грешка при запис на прогноза: {e}")
                continue
        
        if saved_count > 0:
            logger.info(f"✅ Запазени {saved_count} прогнози в базата данни")
    except Exception as e:
        logger.error(f"❌ Грешка при запис на прогнози: {e}")
    
    return saved_count

def _update_predictions_cache(predictions: List[Dict[str, Any]]) -> None:
    """Актуализира кеша на прогнозите"""
    _predictions_cache['data'] = predictions
    _predictions_cache['timestamp'] = datetime.now()
    logger.info(f"💾 Кеш актуализиран с {len(predictions)} прогнози")
    
    # Запис в базата данни за деня
    if db and predictions:
        today = datetime.now().strftime('%Y-%m-%d')
        try:
            cursor = db.connection.cursor()
            cursor.execute(
                "INSERT INTO predictions_cache (date, predictions) VALUES (%s, %s) ON DUPLICATE KEY UPDATE predictions = %s",
                (today, json.dumps(predictions), json.dumps(predictions))
            )
            db.connection.commit()
            cursor.close()
            logger.info(f"💾 Прогнози записани в базата за {today}")
        except Exception as e:
            logger.error(f"❌ Грешка при запис в predictions_cache: {e}")
    
    # Запис в файл
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        cache_data = {
            'data': predictions,
            'timestamp': _predictions_cache['timestamp'].isoformat()
        }
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        logger.info("💾 Кеш записан във файл")
    except Exception as e:
        logger.error(f"❌ Грешка при запис на кеш във файл: {e}")
    
    # Запис на прогнозите в базата данни
    if db and predictions:
        _save_predictions_to_db(predictions)

@app.route('/')
def index() -> str:
    """Главна страница"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"❌ Грешка при зареждане на главна страница: {e}")
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
        
        # Проверяване на predictor
        if not predictor:
            return jsonify({
                'success': False,
                'error': 'Прогнозаторът не е инициализиран. Проверете логовете.'
            }), 500
        
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
        
        if not predictions:
            logger.warning("⚠️  Няма прогнози за днес")
            return jsonify({
                'success': False,
                'error': 'Няма достъпни мачове за прогноза днес',
                'total': 0
            }), 200
        
        # Кеширане на резултата
        _update_predictions_cache(predictions)
        
        return jsonify({
            'success': True,
            'total': len(predictions),
            'predictions': predictions,
            'source': 'fresh'
        }), 200
        
    except ValueError as e:
        logger.error(f"❌ Валидационна грешка: {e}")
        return jsonify({
            'success': False,
            'error': f'Валидационна грешка: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"❌ Критична грешка при генериране на прогнози: {e}", exc_info=True)
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

@app.route('/api/accuracy')
def get_accuracy() -> tuple[Response, int]:
    """
    Връща точност на прогнозите за последния период
    
    Returns:
        JSON response със статистики за точност
    """
    try:
        if not db:
            return jsonify({
                'success': False,
                'error': 'База данни не е инициализирана'
            }), 503
        
        # Точност за последния месец
        accuracy_30 = db.get_prediction_accuracy(days=30)
        # Точност за последната седмица
        accuracy_7 = db.get_prediction_accuracy(days=7)
        # Точност за последния ден
        accuracy_1 = db.get_prediction_accuracy(days=1)
        
        return jsonify({
            'success': True,
            'accuracy': {
                'last_30_days': accuracy_30,
                'last_7_days': accuracy_7,
                'last_24_hours': accuracy_1
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Грешка при получаване на точност: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/database/stats')
def get_database_stats() -> tuple[Response, int]:
    """
    Връща статистики за базата данни
    
    Returns:
        JSON response със статистики за съхранено
    """
    try:
        if not db or not db.connection or not db.connection.is_connected():
            return jsonify({
                'success': False,
                'error': 'База данни не е свързана',
                'status': 'disconnected'
            }), 503
        
        # Получи броя на записите в各и таблица
        cursor = db.connection.cursor()
        
        stats = {}
        for table in ['teams', 'matches', 'predictions', 'team_statistics']:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            stats[table] = count
        
        return jsonify({
            'success': True,
            'status': 'connected',
            'database': 'football_predictor',
            'statistics': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Грешка при получаване на статистики за базата: {e}")
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
    
    # Инициализирање на базата данни
    if init_database():
        logger.info("✅ База данни инициализирана")
    else:
        logger.warning("⚠️  База данни не е инициализирана - някои функции няма да работят")
    
    try:
        app.run(
            debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
            host=os.getenv('HOST', '0.0.0.0'),
            port=int(os.getenv('PORT', 5000)),
            use_reloader=False
        )
    except KeyboardInterrupt:
        logger.info("\n🛑 Спиране на приложението по инструкция...")
        if db and db.connection:
            db.close()
    except Exception as e:
        logger.error(f"❌ Критична грешка: {e}")
        if db and db.connection:
            db.close()
