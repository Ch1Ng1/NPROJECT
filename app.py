"""
⚽ Smart Football Predictor - Интелигентни прогнози за футбол
Използва ELO рейтинг, форма, H2H и xG статистики
"""
import os
from flask import Flask, render_template, jsonify
from datetime import datetime
import logging
from predictor import SmartPredictor

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# Инициализация
API_KEY = os.getenv('API_FOOTBALL_KEY', '')
predictor = SmartPredictor(api_key=API_KEY)

@app.route('/')
def index():
    """Главна страница"""
    return render_template('index.html')

@app.route('/api/predictions')
def get_predictions():
    """Връща прогнози за днес"""
    try:
        predictions = predictor.get_today_predictions()
        return jsonify({
            'success': True,
            'total': len(predictions),
            'predictions': predictions
        })
    except Exception as e:
        logger.error(f"Грешка: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats')
def get_stats():
    """Статистики"""
    try:
        stats = predictor.get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Грешка: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("🚀 Стартиране на Smart Football Predictor")
    app.run(debug=True, host='0.0.0.0', port=5000)
