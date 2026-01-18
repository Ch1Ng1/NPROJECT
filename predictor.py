"""
Модул за прогнозиране на победители в футболни мачове
Използва реална статистика от API-Football за последните мачове
"""

import random
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MatchPredictor:
    """Клас за прогнозиране на резултати от футболни мачове"""
    
    def __init__(self, api_key: str = None):
        """
        Инициализация на предиктора
        
        Args:
            api_key: API-Football ключ за извличане на статистика
        """
        self.api_key = api_key
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            'x-apisports-key': api_key if api_key else 'YOUR_API_KEY'
        }
        self.team_cache = {}  # Кеш за статистики на отбори
        
    def get_team_last_matches(self, team_id: int, last: int = 5) -> Optional[List[Dict]]:
        """
        Извлича последните мачове на отбор от API-Football
        
        Args:
            team_id: ID на отбора
            last: Брой мачове
            
        Returns:
            List[Dict]: Списък с последните мачове или None
        """
        if not self.api_key or self.api_key == '':
            logger.warning(f"No API key - cannot fetch stats for team {team_id}")
            return None
            
        cache_key = f"team_{team_id}_last_{last}"
        
        # Проверка в кеша
        if cache_key in self.team_cache:
            logger.info(f"Using cached stats for team {team_id}")
            return self.team_cache[cache_key]
        
        try:
            url = f"{self.base_url}/fixtures"
            params = {
                'team': team_id,
                'last': last,
                'status': 'FT'  # Само завършени мачове
            }
            
            logger.info(f"Fetching last {last} matches for team {team_id}...")
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                matches = data.get('response', [])
                self.team_cache[cache_key] = matches
                logger.info(f"Found {len(matches)} matches for team {team_id}")
                return matches
            else:
                logger.error(f"API returned status {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error fetching team stats: {e}")
            return None
    
    def analyze_team_form(self, matches: List[Dict], team_id: int) -> Dict:
        """
        Анализира формата на отбора от последните мачове
        
        Args:
            matches: Списък с мачове
            team_id: ID на отбора
            
        Returns:
            Dict: Статистики за формата
        """
        stats = {
            'wins': 0,
            'draws': 0,
            'losses': 0,
            'goals_scored': 0,
            'goals_conceded': 0,
            'clean_sheets': 0,
            'form': [],  # W/D/L
            'points': 0,  # 3 за победа, 1 за равен
            'home_performance': {'wins': 0, 'draws': 0, 'losses': 0, 'goals_for': 0, 'goals_against': 0},
            'away_performance': {'wins': 0, 'draws': 0, 'losses': 0, 'goals_for': 0, 'goals_against': 0}
        }
        
        for match in matches:
            teams = match.get('teams', {})
            goals = match.get('goals', {})
            
            home_id = teams.get('home', {}).get('id')
            away_id = teams.get('away', {}).get('id')
            home_goals = goals.get('home', 0)
            away_goals = goals.get('away', 0)
            
            is_home = (home_id == team_id)
            team_goals = home_goals if is_home else away_goals
            opponent_goals = away_goals if is_home else home_goals
            
            stats['goals_scored'] += team_goals
            stats['goals_conceded'] += opponent_goals
            
            if opponent_goals == 0:
                stats['clean_sheets'] += 1
            
            # Определяне на резултата
            if team_goals > opponent_goals:
                stats['wins'] += 1
                stats['form'].append('W')
                stats['points'] += 3
                if is_home:
                    stats['home_performance']['wins'] += 1
                    stats['home_performance']['goals_for'] += team_goals
                    stats['home_performance']['goals_against'] += opponent_goals
                else:
                    stats['away_performance']['wins'] += 1
                    stats['away_performance']['goals_for'] += team_goals
                    stats['away_performance']['goals_against'] += opponent_goals
            elif team_goals < opponent_goals:
                stats['losses'] += 1
                stats['form'].append('L')
                if is_home:
                    stats['home_performance']['losses'] += 1
                    stats['home_performance']['goals_for'] += team_goals
                    stats['home_performance']['goals_against'] += opponent_goals
                else:
                    stats['away_performance']['losses'] += 1
                    stats['away_performance']['goals_for'] += team_goals
                    stats['away_performance']['goals_against'] += opponent_goals
            else:
                stats['draws'] += 1
                stats['form'].append('D')
                stats['points'] += 1
                if is_home:
                    stats['home_performance']['draws'] += 1
                    stats['home_performance']['goals_for'] += team_goals
                    stats['home_performance']['goals_against'] += opponent_goals
                else:
                    stats['away_performance']['draws'] += 1
                    stats['away_performance']['goals_for'] += team_goals
                    stats['away_performance']['goals_against'] += opponent_goals
        
        return stats
    
    def predict_match(self, match: Dict) -> Dict:
        """
        Прогнозира резултат на мач на база реална статистика от последните мачове
        
        Args:
            match: Информация за мача
            
        Returns:
            Dict: Прогноза с вероятности
        """
        home_team = match.get('home_team', '')
        away_team = match.get('away_team', '')
        league = match.get('league', '')
        
        # Получаване на team ID от мача
        home_team_id = match.get('home_team_id')
        away_team_id = match.get('away_team_id')
        
        logger.info(f"Predicting: {home_team} vs {away_team}")
        
        # Проверка дали статистиката вече е кеширана (от predict_all_matches)
        home_stats = match.get('_cached_home_stats')
        away_stats = match.get('_cached_away_stats')
        
        # Ако не е кеширана, извлечи я сега (fallback)
        if home_stats is None and away_stats is None and home_team_id and away_team_id:
            logger.info(f"No cached stats - fetching for teams {home_team_id} and {away_team_id}")
            home_matches = self.get_team_last_matches(home_team_id, last=5)
            away_matches = self.get_team_last_matches(away_team_id, last=5)
            
            if home_matches:
                home_stats = self.analyze_team_form(home_matches, home_team_id)
            
            if away_matches:
                away_stats = self.analyze_team_form(away_matches, away_team_id)
        
        # Логване на формата
        if home_stats:
            logger.info(f"{home_team} form: {home_stats.get('form')} - W:{home_stats.get('wins')} D:{home_stats.get('draws')} L:{home_stats.get('losses')}")
        
        if away_stats:
            logger.info(f"{away_team} form: {away_stats.get('form')} - W:{away_stats.get('wins')} D:{away_stats.get('draws')} L:{away_stats.get('losses')}")
        
        # Изчисляване на вероятности базирани на статистика
        home_win_prob, draw_prob, away_win_prob = self._calculate_match_probabilities_from_stats(
            home_team, away_team, match, home_stats, away_stats
        )
        
        # Проверка дали има коефициенти от API
        home_odds_api = match.get('home_odds')
        draw_odds_api = match.get('draw_odds')
        away_odds_api = match.get('away_odds')
        
        # Ако има коефициенти, комбинирай статистиката с тях
        if home_odds_api and draw_odds_api and away_odds_api:
            odds_home_prob, odds_draw_prob, odds_away_prob = self._probabilities_from_odds(
                home_odds_api, draw_odds_api, away_odds_api
            )
            
            # Ако имаме и статистика, направи 60/40 микс (60% статистика, 40% коефициенти)
            if home_stats and away_stats:
                home_win_prob = home_win_prob * 0.6 + odds_home_prob * 0.4
                draw_prob = draw_prob * 0.6 + odds_draw_prob * 0.4
                away_win_prob = away_win_prob * 0.6 + odds_away_prob * 0.4
                logger.info("Combined stats + odds prediction")
            else:
                # Само коефициенти
                home_win_prob = odds_home_prob
                draw_prob = odds_draw_prob
                away_win_prob = odds_away_prob
                logger.info("Odds-based prediction (no stats)")
            
            home_odds = home_odds_api
            draw_odds = draw_odds_api
            away_odds = away_odds_api
        else:
            # Само статистика - изчисли коефициенти
            home_odds = round(100 / home_win_prob, 2) if home_win_prob > 0 else 999
            draw_odds = round(100 / draw_prob, 2) if draw_prob > 0 else 999
            away_odds = round(100 / away_win_prob, 2) if away_win_prob > 0 else 999
            logger.info("Stats-based prediction (no odds)")
        
        # Класификация на прогнозата
        prediction_class = self._classify_prediction(home_win_prob)
        
        # Изчисляване на допълнителни прогнози за голове (използваме вече извлечените статистики)
        over_2_5_prob = self._calculate_over_2_5_goals(home_team, away_team, match, home_stats, away_stats)
        first_half_goals_prob = self._calculate_first_half_goals(home_team, away_team, match, home_stats, away_stats)
        btts_prob = self._calculate_btts(home_team, away_team, match, home_stats, away_stats)
        
        # Препоръка базирана на всички статистики
        recommendation = self._get_smart_recommendation(
            home_win_prob, draw_prob, away_win_prob,
            over_2_5_prob, first_half_goals_prob, btts_prob,
            home_odds, draw_odds, away_odds
        )
        
        result = {
            'match_id': match.get('id'),
            'home_team': home_team,
            'away_team': away_team,
            'league': match.get('league'),
            'date': match.get('date'),
            'home_win_probability': round(home_win_prob, 2),
            'draw_probability': round(draw_prob, 2),
            'away_win_probability': round(away_win_prob, 2),
            'home_odds': home_odds,
            'draw_odds': draw_odds,
            'away_odds': away_odds,
            'prediction_class': prediction_class,
            'recommendation': recommendation,
            'confidence': self._calculate_confidence(home_win_prob, draw_prob, away_win_prob),
            'over_2_5_goals': round(over_2_5_prob, 2),
            'first_half_goals': round(first_half_goals_prob, 2),
            'btts': round(btts_prob, 2)
        }
        
        return result
    
    def _probabilities_from_odds(self, home_odds: float, draw_odds: float, away_odds: float) -> tuple:
        """
        Конвертира коефициенти в вероятности
        
        Args:
            home_odds: Коефициент за домакин
            draw_odds: Коефициент за равен
            away_odds: Коефициент за гост
            
        Returns:
            tuple: (home_prob, draw_prob, away_prob) в проценти
        """
        # Конвертиране на коефициенти във вероятности
        home_implied = (1 / home_odds) * 100 if home_odds > 0 else 0
        draw_implied = (1 / draw_odds) * 100 if draw_odds > 0 else 0
        away_implied = (1 / away_odds) * 100 if away_odds > 0 else 0
        
        # Сумата обикновено е над 100% заради букмейкърския марж
        total = home_implied + draw_implied + away_implied
        
        # Нормализиране до 100%
        if total > 0:
            home_prob = (home_implied / total) * 100
            draw_prob = (draw_implied / total) * 100
            away_prob = (away_implied / total) * 100
        else:
            home_prob = 33.33
            draw_prob = 33.33
            away_prob = 33.34
        
        return home_prob, draw_prob, away_prob
    
    def _calculate_match_probabilities_from_stats(
        self, home_team: str, away_team: str, match: Dict,
        home_stats: Optional[Dict] = None, away_stats: Optional[Dict] = None
    ) -> tuple:
        """
        Изчислява вероятности базирани на реална статистика от последните 5 мача
        
        Args:
            home_team: Име на домакин
            away_team: Име на гост
            match: Информация за мача
            home_stats: Статистики на домакина (от последните 5 мача)
            away_stats: Статистики на госта (от последните 5 мача)
            
        Returns:
            tuple: (home_win_prob, draw_prob, away_win_prob) в проценти
        """
        # Ако няма статистика, използвай базови вероятности
        if not home_stats or not away_stats:
            logger.warning("No stats available - using fallback")
            return self._calculate_fallback_probabilities(home_team, away_team, match)
        
        # Базови вероятности с домакинско предимство
        home_win = 42.0
        draw = 28.0
        away_win = 30.0
        
        # ФАКТОР 1: Форма (последни 5 мача) - 30% влияние
        home_form_score = self._calculate_form_score(home_stats.get('form', []))
        away_form_score = self._calculate_form_score(away_stats.get('form', []))
        
        # Форма скор: W=3, D=1, L=0 точки -> максимум 15 точки от 5 мача
        form_diff = (home_form_score - away_form_score) / 15.0 * 100  # Процентна разлика
        home_win += form_diff * 0.3
        away_win -= form_diff * 0.3
        
        logger.info(f"Form: Home={home_form_score}/15, Away={away_form_score}/15")
        
        # ФАКТОР 2: Процент победи - 25% влияние
        home_total = home_stats.get('wins', 0) + home_stats.get('draws', 0) + home_stats.get('losses', 0)
        away_total = away_stats.get('wins', 0) + away_stats.get('draws', 0) + away_stats.get('losses', 0)
        
        if home_total > 0:
            home_win_rate = (home_stats.get('wins', 0) / home_total) * 100
            home_win += (home_win_rate - 40) * 0.25  # 40% е базата за домакин
        
        if away_total > 0:
            away_win_rate = (away_stats.get('wins', 0) / away_total) * 100
            away_win += (away_win_rate - 30) * 0.20  # 30% база за гост
        
        # ФАКТОР 3: Голова разлика - 20% влияние
        if home_total > 0:
            home_goal_diff = (home_stats.get('goals_scored', 0) - home_stats.get('goals_conceded', 0)) / home_total
            home_win += home_goal_diff * 4
            logger.info(f"Home goal diff/match: {home_goal_diff:.2f}")
        
        if away_total > 0:
            away_goal_diff = (away_stats.get('goals_scored', 0) - away_stats.get('goals_conceded', 0)) / away_total
            away_win += away_goal_diff * 3.5
            logger.info(f"Away goal diff/match: {away_goal_diff:.2f}")
        
        # ФАКТОР 4: Clean sheets (пази нулата) - 10% влияние
        home_clean_sheet_rate = (home_stats.get('clean_sheets', 0) / home_total) * 100 if home_total > 0 else 0
        away_clean_sheet_rate = (away_stats.get('clean_sheets', 0) / away_total) * 100 if away_total > 0 else 0
        
        home_win += home_clean_sheet_rate * 0.1
        away_win += away_clean_sheet_rate * 0.08
        
        # ФАКТОР 5: Home/Away специфична форма - 15% влияние
        home_perf = home_stats.get('home_performance', {})
        away_perf = away_stats.get('away_performance', {})
        
        home_home_matches = home_perf.get('wins', 0) + home_perf.get('draws', 0) + home_perf.get('losses', 0)
        away_away_matches = away_perf.get('wins', 0) + away_perf.get('draws', 0) + away_perf.get('losses', 0)
        
        if home_home_matches > 0:
            home_win_at_home = (home_perf.get('wins', 0) / home_home_matches) * 100
            home_win += (home_win_at_home - 45) * 0.25  # 45% е добър домакински процент
            logger.info(f"Home win rate at home: {home_win_at_home:.1f}%")
        
        if away_away_matches > 0:
            away_win_away = (away_perf.get('wins', 0) / away_away_matches) * 100
            away_win += (away_win_away - 25) * 0.2  # 25% е добър гостуващ процент
            logger.info(f"Away win rate away: {away_win_away:.1f}%")
        
        # ФАКТОР 6: Топ лиги - повече равенства
        league = match.get('league', '')
        if any(l in league for l in ['Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1']):
            draw += 3
            home_win -= 1.5
            away_win -= 1.5
        
        # ФАКТОР 7: Малък случаен фактор (симулира непредвидими обстоятелства)
        random_factor = random.uniform(-2, 2)
        home_win += random_factor
        away_win -= random_factor
        
        # Първа нормализация
        total = home_win + draw + away_win
        home_win = (home_win / total) * 100
        draw = (draw / total) * 100
        away_win = (away_win / total) * 100
        
        # Ограничаване на минимални/максимални стойности за реализъм
        home_win = max(15, min(75, home_win))
        draw = max(15, min(40, draw))
        away_win = max(15, min(70, away_win))
        
        # Финална нормализация до 100%
        total = home_win + draw + away_win
        home_win = (home_win / total) * 100
        draw = (draw / total) * 100
        away_win = (away_win / total) * 100
        
        logger.info(f"Final probabilities: H:{home_win:.1f}% D:{draw:.1f}% A:{away_win:.1f}%")
        
        return home_win, draw, away_win
    
    def _calculate_form_score(self, form: List[str]) -> float:
        """
        ИзчисляваScore базиран на форма (W/D/L)
        
        Args:
            form: Списък с резултати ['W', 'D', 'L', ...]
            
        Returns:
            float: Score (0-15)
        """
        if not form:
            return 7.5  # Средна стойност
        
        score = 0
        for result in form:
            if result == 'W':
                score += 3
            elif result == 'D':
                score += 1
        
        return score
    
    def _calculate_fallback_probabilities(
        self, home_team: str, away_team: str, match: Dict
    ) -> tuple:
        """
        Fallback метод когато няма реална статистика - използва само базови фактори
        
        Args:
            home_team: Име на домакин
            away_team: Име на гост
            match: Информация за мача
            
        Returns:
            tuple: (home_win_prob, draw_prob, away_win_prob)
        """
        # Базови вероятности с домакинско предимство
        home_win = 43.0
        draw = 28.0
        away_win = 29.0
        
        # Тип на първенството
        league = match.get('league', '')
        if any(l in league for l in ['Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1']):
            # В топ лиги има повече равни резултати
            draw += 5
            home_win -= 2.5
            away_win -= 2.5
        
        # Час на мача
        try:
            match_time = match.get('date', '')
            if 'T' in match_time:
                hour = int(match_time.split('T')[1].split(':')[0])
                if 18 <= hour <= 21:
                    # Вечерни мачове - леко предимство домакин
                    home_win += 3
                    away_win -= 2
                    draw -= 1
        except:
            pass
        
        # Случаен фактор
        random_home = random.uniform(-5, 5)
        random_away = random.uniform(-5, 5)
        
        home_win += random_home
        away_win += random_away
        
        # Нормализиране - сумата трябва да е 100%
        total = home_win + draw + away_win
        home_win = (home_win / total) * 100
        draw = (draw / total) * 100
        away_win = (away_win / total) * 100
        
        # Ограничаване на минимални/максимални стойности
        home_win = max(10, min(85, home_win))
        draw = max(5, min(40, draw))
        away_win = max(5, min(85, away_win))
        
        # Финална нормализация
        total = home_win + draw + away_win
        home_win = (home_win / total) * 100
        draw = (draw / total) * 100
        away_win = (away_win / total) * 100
        
        return home_win, draw, away_win
    
    def _calculate_home_win_probability(
        self, home_team: str, away_team: str, match: Dict
    ) -> float:
        """
        Изчислява вероятността за победа на домакина
        
        Args:
            home_team: Име на домакин
            away_team: Име на гост
            match: Информация за мача
            
        Returns:
            float: Вероятност в проценти (0-100)
        """
        # Базова вероятност - домакините имат предимство
        probability = 55.0
        
        # Фактор 1: Сила на отборите
        if home_team in self.strong_teams:
            probability += 15
        elif home_team in self.weak_teams:
            probability -= 10
        
        if away_team in self.strong_teams:
            probability -= 15
        elif away_team in self.weak_teams:
            probability += 10
        
        # Фактор 2: Тип на първенството (престижни първенства)
        league = match.get('league', '')
        if any(l in league for l in ['Premier League', 'La Liga', 'Serie A', 'Bundesliga']):
            # В престижни първенства домакинското предимство е по-голямо
            probability += 5
        
        # Фактор 3: Час на мача (вечерните мачове дават предимство на домакина)
        try:
            match_time = match.get('date', '')
            if 'T' in match_time:
                hour = int(match_time.split('T')[1].split(':')[0])
                if 18 <= hour <= 21:
                    probability += 3
        except:
            pass
        
        # Фактор 4: Случаен фактор (симулира форма, нараняния и т.н.)
        random_factor = random.uniform(-5, 5)
        probability += random_factor
        
        # Ограничаване между 5% и 95%
        probability = max(5, min(95, probability))
        
        return probability
    
    def _classify_prediction(self, probability: float) -> str:
        """
        Класифицира прогнозата според вероятността
        
        Args:
            probability: Вероятност за победа на домакина
            
        Returns:
            str: Класификация
        """
        if probability >= 70:
            return "Много вероятна победа на домакина"
        elif probability >= 60:
            return "Вероятна победа на домакина"
        elif probability >= 50:
            return "Леко предимство за домакина"
        elif probability >= 40:
            return "Балансиран мач"
        else:
            return "Предимство за госта"
    
    def _get_recommendation(self, probability: float) -> str:
        """
        Дава препоръка за залог
        
        Args:
            probability: Вероятност за победа на домакина
            
        Returns:
            str: Препоръка
        """
        if probability >= 70:
            return "⭐⭐⭐ СИЛНА препоръка за победа на домакина"
        elif probability >= 60:
            return "⭐⭐ Добра препоръка за победа на домакина"
        elif probability >= 50:
            return "⭐ Умерена препоръка за победа на домакина"
        else:
            return "❌ НЕ се препоръчва залог на домакина"
    
    def _get_smart_recommendation(
        self, home_prob: float, draw_prob: float, away_prob: float,
        over_2_5: float, first_half: float, btts: float,
        home_odds: float = None, draw_odds: float = None, away_odds: float = None
    ) -> str:
        """
        Интелигентна препоръка базирана на всички статистики с коефициенти
        
        Args:
            home_prob: Вероятност за победа домакин
            draw_prob: Вероятност за равен
            away_prob: Вероятност за победа гост
            over_2_5: Вероятност за над 2.5 гола
            first_half: Вероятност за гол в 1во полувреме
            btts: Вероятност за BTTS
            home_odds: Коефициент за домакин
            draw_odds: Коефициент за равен
            away_odds: Коефициент за гост
            
        Returns:
            str: Препоръка за залог
        """
        recommendations = []
        
        # Проверка за резултат (1/X/2)
        if home_prob >= 65:
            if home_odds and home_odds < 999:
                recommendations.append(f"1 (Коеф {home_odds})")
            else:
                recommendations.append(f"1 ({home_prob:.0f}%)")
        elif away_prob >= 60:
            if away_odds and away_odds < 999:
                recommendations.append(f"2 (Коеф {away_odds})")
            else:
                recommendations.append(f"2 ({away_prob:.0f}%)")
        elif draw_prob >= 35:
            if draw_odds and draw_odds < 999:
                recommendations.append(f"X (Коеф {draw_odds})")
            else:
                recommendations.append(f"X ({draw_prob:.0f}%)")
        
        # Double Chance - изчисляваме приблизителни коефициенти
        if home_prob + draw_prob >= 75:
            # 1X коефициент е приблизително обратното на комбинираната вероятност
            prob_1x = (home_prob + draw_prob) / 100
            odds_1x = round(1 / prob_1x, 2) if prob_1x > 0 else 0
            recommendations.append(f"1X (~{odds_1x})")
        elif away_prob + draw_prob >= 70:
            prob_x2 = (away_prob + draw_prob) / 100
            odds_x2 = round(1 / prob_x2, 2) if prob_x2 > 0 else 0
            recommendations.append(f"X2 (~{odds_x2})")
        elif home_prob + away_prob >= 75:
            prob_12 = (home_prob + away_prob) / 100
            odds_12 = round(1 / prob_12, 2) if prob_12 > 0 else 0
            recommendations.append(f"12 (~{odds_12})")
        
        # Голове - изчисляваме приблизителни коефициенти
        if over_2_5 >= 65:
            over_odds = round(100 / over_2_5, 2) if over_2_5 > 0 else 0
            recommendations.append(f"Над 2.5 (~{over_odds})")
        elif over_2_5 <= 35:
            under_odds = round(100 / (100 - over_2_5), 2) if over_2_5 < 100 else 0
            recommendations.append(f"Под 2.5 (~{under_odds})")
        
        if first_half >= 65:
            fh_odds = round(100 / first_half, 2) if first_half > 0 else 0
            recommendations.append(f"Гол 1во (~{fh_odds})")
        
        if btts >= 65:
            btts_odds = round(100 / btts, 2) if btts > 0 else 0
            recommendations.append(f"BTTS Да (~{btts_odds})")
        elif btts <= 35:
            btts_no_odds = round(100 / (100 - btts), 2) if btts < 100 else 0
            recommendations.append(f"BTTS Не (~{btts_no_odds})")
        
        # Комбинирани залози
        if home_prob >= 60 and over_2_5 >= 60:
            recommendations.append(f"1 & Над 2.5")
        elif away_prob >= 55 and over_2_5 >= 60:
            recommendations.append(f"2 & Над 2.5")
        
        if home_prob >= 60 and btts >= 60:
            recommendations.append(f"1 & BTTS")
        
        # Връщане на най-добрите 2-3 препоръки
        if recommendations:
            return " • ".join(recommendations[:3])
        else:
            # Ако няма силни препоръки, покажи най-вероятното
            max_prob = max(home_prob, draw_prob, away_prob)
            if max_prob == home_prob:
                if home_odds and home_odds < 999:
                    return f"Леко предимство: 1 (Коеф {home_odds})"
                else:
                    return f"Леко предимство: 1 ({home_prob:.0f}%)"
            elif max_prob == away_prob:
                if away_odds and away_odds < 999:
                    return f"Леко предимство: 2 (Коеф {away_odds})"
                else:
                    return f"Леко предимство: 2 ({away_prob:.0f}%)"
            else:
                if draw_odds and draw_odds < 999:
                    return f"Балансиран мач: X (Коеф {draw_odds})"
                else:
                    return f"Балансиран мач: X ({draw_prob:.0f}%)"
    
    def _calculate_confidence(self, home_prob: float, draw_prob: float, away_prob: float) -> str:
        """
        Изчислява ниво на увереност базирано на разликата между вероятностите
        
        Args:
            home_prob: Вероятност за победа домакин
            draw_prob: Вероятност за равен
            away_prob: Вероятност за победа гост
            
        Returns:
            str: Ниво на увереност
        """
        # Намираме най-високата вероятност
        max_prob = max(home_prob, draw_prob, away_prob)
        
        # Изчисляваме разликата с втората най-висока
        probs = sorted([home_prob, draw_prob, away_prob], reverse=True)
        difference = probs[0] - probs[1]
        
        if difference >= 30:
            return "Много висока"
        elif difference >= 20:
            return "Висока"
        elif difference >= 10:
            return "Средна"
        else:
            return "Ниска"
    
    def _calculate_over_2_5_goals(
        self, home_team: str, away_team: str, match: Dict,
        home_stats: Optional[Dict] = None, away_stats: Optional[Dict] = None
    ) -> float:
        """
        Изчислява вероятността за над 2.5 гола базирано на реална статистика
        
        Args:
            home_team: Име на домакин
            away_team: Име на гост
            match: Информация за мача
            home_stats: Статистики на домакина
            away_stats: Статистики на госта
            
        Returns:
            float: Вероятност в проценти (0-100)
        """
        # Базова вероятност
        probability = 45.0
        
        # Ако имаме реална статистика
        if home_stats and away_stats:
            home_games = home_stats.get('wins', 0) + home_stats.get('draws', 0) + home_stats.get('losses', 0)
            away_games = away_stats.get('wins', 0) + away_stats.get('draws', 0) + away_stats.get('losses', 0)
            
            # Средно голове на мач за двата отбора
            if home_games > 0:
                home_avg_scored = home_stats.get('goals_scored', 0) / home_games
                home_avg_conceded = home_stats.get('goals_conceded', 0) / home_games
                
                # Колкото повече голове отбелязва/допуска, толкова по-вероятно е над 2.5
                probability += (home_avg_scored - 1.2) * 12
                probability += (home_avg_conceded - 1.0) * 10
            
            if away_games > 0:
                away_avg_scored = away_stats.get('goals_scored', 0) / away_games
                away_avg_conceded = away_stats.get('goals_conceded', 0) / away_games
                
                probability += (away_avg_scored - 1.0) * 10
                probability += (away_avg_conceded - 1.0) * 10
        
        # Топ първенства - повече голове
        league = match.get('league', '')
        if any(l in league for l in ['Premier League', 'Bundesliga']):
            probability += 8
        elif 'Serie A' in league:
            probability -= 5
        
        # Случаен фактор
        random_factor = random.uniform(-6, 6)
        probability += random_factor
        
        # Ограничаване
        probability = max(20, min(85, probability))
        
        return probability
    
    def _calculate_first_half_goals(
        self, home_team: str, away_team: str, match: Dict,
        home_stats: Optional[Dict] = None, away_stats: Optional[Dict] = None
    ) -> float:
        """
        Изчислява вероятността за гол в първото полувреме
        
        Args:
            home_team: Име на домакин
            away_team: Име на гост
            match: Информация за мача
            home_stats: Статистики на домакина
            away_stats: Статистики на госта
            
        Returns:
            float: Вероятност в проценти (0-100)
        """
        # Базова вероятност
        probability = 52.0
        
        # Ако имаме реална статистика
        if home_stats and away_stats:
            home_games = home_stats.get('wins', 0) + home_stats.get('draws', 0) + home_stats.get('losses', 0)
            away_games = away_stats.get('wins', 0) + away_stats.get('draws', 0) + away_stats.get('losses', 0)
            
            # Отбори с добра голова сметка започват агресивно
            if home_games > 0:
                home_avg_scored = home_stats.get('goals_scored', 0) / home_games
                if home_avg_scored >= 1.5:
                    probability += 10
                elif home_avg_scored >= 1.0:
                    probability += 5
            
            if away_games > 0:
                away_avg_scored = away_stats.get('goals_scored', 0) / away_games
                if away_avg_scored >= 1.5:
                    probability += 8
                elif away_avg_scored >= 1.0:
                    probability += 4
        
        # Топ първенства - по-бързо темпо
        league = match.get('league', '')
        if any(l in league for l in ['Premier League', 'Bundesliga']):
            probability += 8
        
        # Случаен фактор
        random_factor = random.uniform(-6, 6)
        probability += random_factor
        
        # Ограничаване
        probability = max(30, min(80, probability))
        
        return probability
    
    def _calculate_btts(
        self, home_team: str, away_team: str, match: Dict,
        home_stats: Optional[Dict] = None, away_stats: Optional[Dict] = None
    ) -> float:
        """
        Изчислява вероятността за голове и за двата отбора (BTTS)
        
        Args:
            home_team: Име на домакин
            away_team: Име на гост
            match: Информация за мача
            home_stats: Статистики на домакина
            away_stats: Статистики на госта
            
        Returns:
            float: Вероятност в проценти (0-100)
        """
        # Базова вероятност
        probability = 48.0
        
        # Ако имаме реална статистика
        if home_stats and away_stats:
            home_games = home_stats.get('wins', 0) + home_stats.get('draws', 0) + home_stats.get('losses', 0)
            away_games = away_stats.get('wins', 0) + away_stats.get('draws', 0) + away_stats.get('losses', 0)
            
            # И двата отбора вкарват редовно?
            if home_games > 0:
                home_avg_scored = home_stats.get('goals_scored', 0) / home_games
                if home_avg_scored >= 1.2:
                    probability += 12
                elif home_avg_scored >= 0.8:
                    probability += 5
            
            if away_games > 0:
                away_avg_scored = away_stats.get('goals_scored', 0) / away_games
                if away_avg_scored >= 1.0:
                    probability += 12
                elif away_avg_scored >= 0.7:
                    probability += 5
            
            # Слаби защити?
            if home_games > 0:
                home_avg_conceded = home_stats.get('goals_conceded', 0) / home_games
                if home_avg_conceded >= 1.2:
                    probability += 8
            
            if away_games > 0:
                away_avg_conceded = away_stats.get('goals_conceded', 0) / away_games
                if away_avg_conceded >= 1.2:
                    probability += 8
        
        # Топ лиги - повече голове
        league = match.get('league', '')
        if any(l in league for l in ['Premier League', 'Bundesliga', 'La Liga']):
            probability += 7
        
        # Случаен фактор
        random_factor = random.uniform(-5, 5)
        probability += random_factor
        
        # Ограничаване
        probability = max(25, min(80, probability))
        
        return probability
    
    def predict_all_matches(self, matches: List[Dict]) -> List[Dict]:
        """
        Прогнозира всички мачове и сортира по вероятност
        Оптимизация: извлича статистиката за всички отбори само веднъж
        
        Args:
            matches: Списък с мачове
            
        Returns:
            List[Dict]: Прогнози, сортирани по вероятност
        """
        logger.info(f"Predicting {len(matches)} matches...")
        
        # Стъпка 1: Събиране на всички уникални team IDs
        unique_team_ids = set()
        for match in matches:
            home_id = match.get('home_team_id')
            away_id = match.get('away_team_id')
            if home_id:
                unique_team_ids.add(home_id)
            if away_id:
                unique_team_ids.add(away_id)
        
        logger.info(f"Found {len(unique_team_ids)} unique teams")
        
        # Стъпка 2: Извличане на статистика за всички отбори ВЕДНЪЖ
        team_stats_cache = {}
        for team_id in unique_team_ids:
            logger.info(f"Fetching stats for team {team_id}...")
            matches_data = self.get_team_last_matches(team_id, last=5)
            if matches_data:
                team_stats_cache[team_id] = self.analyze_team_form(matches_data, team_id)
            else:
                team_stats_cache[team_id] = None
        
        logger.info(f"Stats fetched for {len(team_stats_cache)} teams")
        
        # Стъпка 3: Прогнозиране на всички мачове с готовите статистики
        predictions = []
        for match in matches:
            # Вземи статистиката от кеша вместо да я извличаш отново
            home_id = match.get('home_team_id')
            away_id = match.get('away_team_id')
            
            match['_cached_home_stats'] = team_stats_cache.get(home_id)
            match['_cached_away_stats'] = team_stats_cache.get(away_id)
            
            prediction = self.predict_match(match)
            predictions.append(prediction)
        
        # Сортиране по най-висока вероятност (домакин, равен или гост)
        predictions.sort(
            key=lambda x: max(x['home_win_probability'], x['draw_probability'], x['away_win_probability']), 
            reverse=True
        )
        
        logger.info(f"Predictions completed for {len(predictions)} matches")
        
        return predictions
    
    def get_top_predictions(
        self, predictions: List[Dict], min_probability: float = 60.0, limit: int = 5
    ) -> List[Dict]:
        """
        Връща топ прогнози над определена вероятност
        
        Args:
            predictions: Всички прогнози
            min_probability: Минимална вероятност
            limit: Максимален брой резултати
            
        Returns:
            List[Dict]: Топ прогнози
        """
        top_predictions = [
            p for p in predictions 
            if p['home_win_probability'] >= min_probability
        ]
        
        return top_predictions[:limit]


if __name__ == "__main__":
    # Тест на предиктора
    from match_scraper import MatchScraper
    
    scraper = MatchScraper()
    matches = scraper.get_today_matches()
    
    predictor = MatchPredictor()
    predictions = predictor.predict_all_matches(matches)
    
    print("\n" + "="*70)
    print("ПРОГНОЗИ ЗА ПОБЕДИ НА ДОМАКИНИ")
    print("="*70 + "\n")
    
    top_predictions = predictor.get_top_predictions(predictions, min_probability=55)
    
    if top_predictions:
        for i, pred in enumerate(top_predictions, 1):
            print(f"{i}. {pred['home_team']} vs {pred['away_team']}")
            print(f"   Първенство: {pred['league']}")
            print(f"   Вероятност за победа на домакина: {pred['home_win_probability']}%")
            print(f"   {pred['recommendation']}")
            print(f"   Увереност: {pred['confidence']}\n")
    else:
        print("Няма силни препоръки за днес.")
