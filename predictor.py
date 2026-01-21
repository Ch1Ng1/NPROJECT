"""
🎯 Smart Predictor - Интелигентен модул за прогнози
Използва ELO рейтинг + форма + статистики
"""
import requests
from datetime import datetime
import logging
from typing import List, Dict, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

class SmartPredictor:
    """Интелигентен прогнозатор"""
    
    # ELO константи
    INITIAL_ELO = 1500
    K_FACTOR = 32
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            'x-apisports-key': api_key
        }
        self.elo_ratings = defaultdict(lambda: self.INITIAL_ELO)
        
    def _request(self, endpoint: str, params: dict) -> Optional[dict]:
        """API заявка"""
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('response'):
                    return data
            
            logger.warning(f"API грешка: {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"Request грешка: {e}")
            return None
    
    def _calculate_elo_probability(self, elo_home: float, elo_away: float) -> Dict[str, float]:
        """Изчислява вероятности от ELO рейтинг"""
        diff = elo_home - elo_away
        
        # Формула на ELO
        expected_home = 1 / (1 + 10 ** (-diff / 400))
        expected_away = 1 - expected_home
        
        # Добавяне на вероятност за равен
        draw_prob = max(0.15, 0.35 - abs(diff) / 1000)
        
        # Нормализация
        total = expected_home + expected_away + draw_prob
        
        return {
            'home_win': round(expected_home / total * 100, 1),
            'draw': round(draw_prob / total * 100, 1),
            'away_win': round(expected_away / total * 100, 1)
        }
    
    def _get_form_score(self, form: str) -> float:
        """Оценка на форма (W=3, D=1, L=0)"""
        if not form:
            return 1.5
        
        points = {'W': 3, 'D': 1, 'L': 0}
        total = sum(points.get(char, 0) for char in form[:5])
        return total / min(len(form), 5)
    
    def _analyze_match(self, fixture: dict, home_stats: dict, away_stats: dict) -> dict:
        """Анализира един мач"""
        home_team = fixture['teams']['home']['name']
        away_team = fixture['teams']['away']['name']
        home_id = fixture['teams']['home']['id']
        away_id = fixture['teams']['away']['id']
        
        # ELO рейтинги
        home_elo = self.elo_ratings[home_id]
        away_elo = self.elo_ratings[away_id]
        
        # ELO вероятности
        elo_probs = self._calculate_elo_probability(home_elo, away_elo)
        
        # Форма
        home_form = home_stats.get('form', '')
        away_form = away_stats.get('form', '')
        home_form_score = self._get_form_score(home_form)
        away_form_score = self._get_form_score(away_form)
        
        # Голове (последни 5 мача)
        home_goals_avg = home_stats.get('goals_avg', 1.5)
        away_goals_avg = away_stats.get('goals_avg', 1.5)
        
        # Прогноза за Over 2.5
        expected_goals = home_goals_avg + away_goals_avg
        over_25_prob = min(95, max(5, (expected_goals - 1.5) * 35 + 50))
        
        # Окончателна прогноза (комбинация ELO + форма)
        form_factor = (home_form_score - away_form_score) / 6 * 10  # -10 до +10
        
        final_home = min(95, max(5, elo_probs['home_win'] + form_factor))
        final_away = min(95, max(5, elo_probs['away_win'] - form_factor))
        final_draw = 100 - final_home - final_away
        
        # Препоръка
        probs = {'1': final_home, 'X': final_draw, '2': final_away}
        best_bet = max(probs, key=probs.get)
        confidence = max(probs.values())
        
        if confidence >= 60:
            confidence_level = "Висока"
        elif confidence >= 45:
            confidence_level = "Средна"
        else:
            confidence_level = "Ниска"
        
        return {
            'id': fixture['fixture']['id'],
            'time': datetime.fromtimestamp(fixture['fixture']['timestamp']).strftime('%H:%M'),
            'league': fixture['league']['name'],
            'country': fixture['league']['country'],
            'home_team': home_team,
            'away_team': away_team,
            'home_elo': round(home_elo),
            'away_elo': round(away_elo),
            'home_form': home_form,
            'away_form': away_form,
            'probabilities': {
                '1': round(final_home, 1),
                'X': round(final_draw, 1),
                '2': round(final_away, 1)
            },
            'over_25': round(over_25_prob, 1),
            'expected_goals': round(expected_goals, 2),
            'prediction': {
                'bet': best_bet,
                'confidence': round(confidence, 1),
                'level': confidence_level
            },
            'details': {
                'home_goals_avg': round(home_goals_avg, 2),
                'away_goals_avg': round(away_goals_avg, 2),
                'home_form_score': round(home_form_score, 2),
                'away_form_score': round(away_form_score, 2)
            }
        }
    
    def get_today_predictions(self) -> List[dict]:
        """Генерира прогнози за днес (максимум 20 мача)"""
        logger.info("📊 Започване на анализ...")
        
        # Вземи мачове за днес
        today = datetime.now().strftime('%Y-%m-%d')
        fixtures_data = self._request('fixtures', {
            'date': today,
            'timezone': 'Europe/Sofia'
        })
        
        if not fixtures_data or not fixtures_data.get('response'):
            logger.warning("Няма мачове за днес")
            return []
        
        # Ограничаване на 20 мача
        all_fixtures = fixtures_data['response']
        fixtures = all_fixtures[:20]
        
        logger.info(f"📋 Намерени {len(all_fixtures)} мача, анализиране на първите {len(fixtures)}")
        
        predictions = []
        
        for fixture in fixtures:
            try:
                home_id = fixture['teams']['home']['id']
                away_id = fixture['teams']['away']['id']
                league_id = fixture['league']['id']
                
                # Вземи статистики за отборите
                home_stats_data = self._request('teams/statistics', {
                    'team': home_id,
                    'season': 2024,
                    'league': league_id
                })
                
                away_stats_data = self._request('teams/statistics', {
                    'team': away_id,
                    'season': 2024,
                    'league': league_id
                })
                
                # Извличане на данни
                home_stats = {}
                away_stats = {}
                
                if home_stats_data and home_stats_data.get('response'):
                    resp = home_stats_data['response']
                    goals_avg = resp.get('goals', {}).get('for', {}).get('average', {}).get('total', 1.5)
                    home_stats = {
                        'form': resp.get('form', ''),
                        'goals_avg': float(goals_avg) if goals_avg else 1.5
                    }
                
                if away_stats_data and away_stats_data.get('response'):
                    resp = away_stats_data['response']
                    goals_avg = resp.get('goals', {}).get('for', {}).get('average', {}).get('total', 1.5)
                    away_stats = {
                        'form': resp.get('form', ''),
                        'goals_avg': float(goals_avg) if goals_avg else 1.5
                    }
                
                # Анализ
                prediction = self._analyze_match(fixture, home_stats, away_stats)
                predictions.append(prediction)
                
                logger.info(f"✅ {prediction['home_team']} vs {prediction['away_team']} - {prediction['prediction']['bet']} ({prediction['prediction']['confidence']}%)")
                
            except Exception as e:
                logger.error(f"Грешка при анализ на мач: {e}")
                continue
        
        # Сортиране по време
        predictions.sort(key=lambda x: x['time'])
        
        logger.info(f"🎯 Завършени {len(predictions)} прогнози")
        return predictions
    
    def get_stats(self) -> dict:
        """Статистики"""
        return {
            'total_teams': len(self.elo_ratings),
            'avg_elo': round(sum(self.elo_ratings.values()) / len(self.elo_ratings), 1) if self.elo_ratings else 1500,
            'api_key_configured': bool(self.api_key)
        }
