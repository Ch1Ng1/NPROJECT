"""
🎯 Smart Predictor - Интелигентен модул за прогнози
Използва ELO рейтинг + форма + статистики за генериране на прогнози за футболни мачове

Алгоритъм:
1. ELO рейтинг: Математически модел базиран на резултати
2. Форма: Последни 5 мача (W=3 точки, D=1 точка, L=0 точки)
3. Голове: Средни голове от/за отбора
4. Вероятности: Комбинация от горните фактори с нормализация
5. Увереност: Основава се на разликата между вероятностите

Примери:
    predictor = SmartPredictor(api_key="your_key")
    predictions = predictor.get_today_predictions()
"""
import requests
from datetime import datetime
import logging
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

class SmartPredictor:
    """
    Интелигентен прогнозатор за футболни мачове
    
    Атрибути:
        INITIAL_ELO: Начален ELO рейтинг (1500)
        K_FACTOR: Фактор за актуализация на ELO (32)
        MAX_FIXTURES: Максимален брой мачове за анализ (20)
        API_TIMEOUT: Таймаут за API заявки (10 сек)
    """
    
    # ELO константи
    INITIAL_ELO: int = 1500
    K_FACTOR: int = 32
    MAX_FIXTURES: int = 20
    API_TIMEOUT: int = 10
    MAX_RETRIES: int = 3
    
    def __init__(self, api_key: str) -> None:
        """
        Инициализация на прогнозатора
        
        Args:
            api_key: API ключ за api-sports.io
            
        Raises:
            ValueError: Ако api_key е празен
        """
        if not api_key:
            raise ValueError("API ключът е задължителен")
            
        self.api_key = api_key
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            'x-apisports-key': api_key,
            'User-Agent': 'SmartFootballPredictor/1.0'
        }
        self.elo_ratings: Dict[int, float] = defaultdict(lambda: self.INITIAL_ELO)
        
        # Конфигуриране на retry стратегия
        self.session = requests.Session()
        retry_strategy = Retry(
            total=self.MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
    def _request(self, endpoint: str, params: Dict[str, any]) -> Optional[Dict[str, any]]:
        """
        Прави API заявка със обработка на грешки и retry логика
        
        Args:
            endpoint: API endpoint (без домена)
            params: Параметри на заявката
            
        Returns:
            Декодиран JSON отговор или None ако грешка
        """
        try:
            url = f"{self.base_url}/{endpoint}"
            response = self.session.get(
                url,
                headers=self.headers,
                params=params,
                timeout=self.API_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('response'):
                    return data
            elif response.status_code == 429:
                logger.warning("⏳ API rate limit достигнат, чакане...")
                return None
            elif response.status_code == 401:
                logger.error("❌ Невалиден API ключ")
                raise ValueError("API ключът е невалиден")
            else:
                logger.warning(f"⚠️  API грешка: {response.status_code} - {response.text[:100]}")
                return None
            
        except requests.exceptions.Timeout:
            logger.error(f"⏱️  Request timeout при {endpoint}")
        except requests.exceptions.ConnectionError:
            logger.error(f"🌐 Connection error при {endpoint}")
        except ValueError as e:
            logger.error(f"❌ Валидационна грешка: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Request грешка: {e}")
            
        return None
    
    def _calculate_elo_probability(self, elo_home: float, elo_away: float) -> Dict[str, float]:
        """
        Изчислява вероятности на базата на ELO рейтинги
        
        Формула: E = 1 / (1 + 10^(-diff/400))
        
        Args:
            elo_home: ELO рейтинг на домакина
            elo_away: ELO рейтинг на гостите
            
        Returns:
            Dict с ключове 'home_win', 'draw', 'away_win' (проценти 0-100)
        """
        try:
            diff = elo_home - elo_away
            
            # Формула на ELO
            expected_home = 1 / (1 + 10 ** (-diff / 400))
            expected_away = 1 - expected_home
            
            # Добавяне на вероятност за равен
            # По-малката разлика, по-висока е вероятност за равен
            draw_prob = max(0.15, 0.35 - abs(diff) / 1000)
            
            # Нормализация
            total = expected_home + expected_away + draw_prob
            
            return {
                'home_win': round(expected_home / total * 100, 1),
                'draw': round(draw_prob / total * 100, 1),
                'away_win': round(expected_away / total * 100, 1)
            }
        except Exception as e:
            logger.error(f"❌ Грешка при изчисляване на ELO вероятности: {e}")
            return {
                'home_win': 33.3,
                'draw': 33.3,
                'away_win': 33.3
            }
    
    def _get_form_score(self, form: str) -> float:
        """
        Изчислява оценка на форма (W=3, D=1, L=0)
        
        Примери:
            "WWDWL" -> 3+3+1+3+0 = 10 / 5 = 2.0
            "LLLLL" -> 0 / 5 = 0.0
            
        Args:
            form: Строка с последни резултати (W/D/L)
            
        Returns:
            Средна оценка (0-3)
        """
        if not form:
            return 1.5
        
        try:
            points = {'W': 3, 'D': 1, 'L': 0}
            total = sum(points.get(char, 0) for char in form[:5])
            result = total / min(len(form), 5)
            return result
        except Exception as e:
            logger.error(f"❌ Грешка при изчисляване на форма: {e}")
            return 1.5
    
    def _analyze_match(self, fixture: Dict[str, any], home_stats: Dict[str, any], away_stats: Dict[str, any]) -> Dict[str, any]:
        """
        Анализира един мач и генерира прогноза
        
        Прави комплексен анализ на основата на:
        - ELO рейтинги и вероятности
        - Текуща форма на отборите
        - Средни голове за/против
        - Очаквани голове (xG)
        
        Args:
            fixture: Информация за мача (времеви печат, отбори, лига)
            home_stats: Статистики на домакина (форма, голове)
            away_stats: Статистики на гостите (форма, голове)
            
        Returns:
            Dict с детайлна прогноза
        """
        try:
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
            home_goals_avg = float(home_stats.get('goals_avg', 1.5))
            away_goals_avg = float(away_stats.get('goals_avg', 1.5))
            
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
        except Exception as e:
            logger.error(f"❌ Грешка при анализ на мач {home_team} vs {away_team}: {e}")
            return None
    
    def get_today_predictions(self) -> List[Dict[str, any]]:
        """
        Генерира прогнози за мачове днес (максимум 20 мача)
        
        Процес:
        1. Вземане на мачове за днешния ден
        2. Ограничаване на първите 20 мача
        3. За всеки мач: вземане на статистики и анализ
        4. Сортиране по време
        
        Returns:
            Список с прогнози (всяка прогноза е dict)
        """
        logger.info("📊 Започване на анализ...")
        
        # Вземи мачове за днес
        today = datetime.now().strftime('%Y-%m-%d')
        fixtures_data = self._request('fixtures', {
            'date': today,
            'timezone': 'Europe/Sofia'
        })
        
        if not fixtures_data or not fixtures_data.get('response'):
            logger.warning("⚠️  Няма мачове за днес")
            return []
        
        # Ограничаване на 20 мача
        all_fixtures = fixtures_data['response']
        fixtures = all_fixtures[:self.MAX_FIXTURES]
        
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
                if prediction:
                    predictions.append(prediction)
                    logger.info(f"✅ {prediction['home_team']} vs {prediction['away_team']} - {prediction['prediction']['bet']} ({prediction['prediction']['confidence']}%)")
                
            except Exception as e:
                logger.error(f"❌ Грешка при анализ на мач: {e}")
                continue
        
        # Сортиране по време
        predictions.sort(key=lambda x: x['time'])
        
        logger.info(f"🎯 Завършени {len(predictions)} прогнози")
        return predictions
    
    def get_stats(self) -> Dict[str, any]:
        """
        Връща статистики за системата
        
        Returns:
            Dict със статистики (брой отбори, средно ELO, конфигурация)
        """
        avg_elo = 1500
        if self.elo_ratings:
            avg_elo = round(sum(self.elo_ratings.values()) / len(self.elo_ratings), 1)
        
        return {
            'total_teams': len(self.elo_ratings),
            'avg_elo': avg_elo,
            'api_key_configured': bool(self.api_key),
            'system_status': 'operational'
        }
