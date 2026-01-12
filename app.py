"""
Flask приложение за прогнозиране на футболни мачове
"""

from flask import Flask, render_template, jsonify, request
from match_scraper import MatchScraper
from predictor import MatchPredictor
from datetime import datetime
import os

app = Flask(__name__)

# Инициализация на модулите
# API ключове
API_FOOTBALL_KEY = 'bbc0c6a638297557289b83aca01e2948'
FOOTBALL_DATA_KEY = os.environ.get('FOOTBALL_DATA_KEY', 'YOUR_API_KEY')  # Вземи от GET_API_KEY.md

scraper = MatchScraper(api_key=API_FOOTBALL_KEY, use_livescore=False)
predictor = MatchPredictor(api_key=FOOTBALL_DATA_KEY)


@app.route('/')
def index():
    """Главна страница"""
    return render_template('index.html')


@app.route('/api/matches')
def get_matches():
    """API endpoint за получаване на мачове"""
    try:
        # Получаване на мачове
        matches = scraper.get_today_matches()
        
        # Прогнозиране
        predictions = predictor.predict_all_matches(matches)
        
        return jsonify({
            'success': True,
            'count': len(predictions),
            'predictions': predictions
        })
    except Exception as e:
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
