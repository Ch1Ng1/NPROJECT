"""
Flask приложение за прогнозиране на футболни мачове
"""

from flask import Flask, render_template, jsonify, request
from match_scraper import MatchScraper
from predictor import MatchPredictor
from config import Config
from datetime import datetime
import os
import logging

# Настройка на логване
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)

# Инициализация на модулите
scraper = MatchScraper(api_key=Config.API_FOOTBALL_KEY, use_livescore=False)
predictor = MatchPredictor(api_key=Config.FOOTBALL_DATA_KEY)


@app.route('/')
def index():
    """Главна страница"""
    return render_template('index.html')


@app.route('/api/matches')
def get_matches():
    """API endpoint за получаване на мачове"""
    try:
        logger.info("Fetching today's matches...")
        # Получаване на мачове
        matches = scraper.get_today_matches()
        
        # Вземане на коефициенти за първите 30 мача
        if matches and len(matches) <= 50:
            matches = scraper.fetch_odds_for_selected_matches(matches, max_matches=30)
        
        # Прогнозиране
        predictions = predictor.predict_all_matches(matches)
        logger.info(f"Successfully generated {len(predictions)} predictions")
        
        return jsonify({
            'success': True,
            'count': len(predictions),
            'predictions': predictions
        })
    except Exception as e:
        logger.error(f"Error in /api/matches: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/top-predictions')
def get_top_predictions():
    """API endpoint за топ прогнози"""
    try:
        # Параметри от заявката
        min_probability = float(request.args.get('min_probability', 60))
        limit = int(request.args.get('limit', 10))
        
        # Получаване на мачове
        matches = scraper.get_today_matches()
        
        # Вземане на коефициенти за всички мачове (оптимизирано до 30)
        if matches and len(matches) <= 50:
            print(f"[API] Fetching odds for {min(len(matches), 30)} matches...")
            matches = scraper.fetch_odds_for_selected_matches(matches, max_matches=30)
        
        # Прогнозиране
        all_predictions = predictor.predict_all_matches(matches)
        
        # Филтриране на топ прогнози
        top_predictions = predictor.get_top_predictions(
            all_predictions, 
            min_probability=min_probability,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'count': len(top_predictions),
            'min_probability': min_probability,
            'predictions': top_predictions
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/refresh')
def refresh_data():
    """Обновява данните за мачове"""
    try:
        matches = scraper.get_today_matches()
        predictions = predictor.predict_all_matches(matches)
        
        return jsonify({
            'success': True,
            'message': f'Обновени {len(predictions)} мача',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    # Създаване на templates директория ако не съществува
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    print("\n" + "="*70)
    print("СТАРТИРАНЕ НА ПРИЛОЖЕНИЕ ЗА ПРОГНОЗИРАНЕ НА ФУТБОЛНИ МАЧОВЕ")
    print("="*70)
    print("\nПриложението ще бъде достъпно на: http://localhost:5000")
    print("\nAPI endpoints:")
    print("  - GET /api/matches - Всички мачове с прогнози")
    print("  - GET /api/top-predictions - Топ прогнози")
    print("  - GET /api/refresh - Обновяване на данни")
    print("\n" + "="*70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
