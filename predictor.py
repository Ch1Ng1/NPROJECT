"""
Модул за прогнозиране на победители в футболни мачове
Използва реална статистика от Football-Data.org API
"""

import random
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class MatchPredictor:
    """Клас за прогнозиране на резултати от футболни мачове"""
    
    def __init__(self, api_key: str = None):
        """
        Инициализация на предиктора
        
        Args:
            api_key: Football-Data.org API ключ
        """
        self.api_key = api_key
        self.base_url = "https://api.football-data.org/v4"
        self.headers = {
            'X-Auth-Token': api_key if api_key else 'YOUR_API_KEY'
        }
        self.team_cache = {}  # Кеш за статистики на отбори
    
    def get_team_stats(self, team_name: str, league: str) -> Optional[Dict]:
        """
        Извлича статистики за отбор от API
        
        Args:
            team_name: Име на отбора
            league: Лига
            
        Returns:
            Optional[Dict]: Статистики или None
        """
        cache_key = f"{team_name}_{league}"
        
        # Проверка в кеша
        if cache_key in self.team_cache:
            return self.team_cache[cache_key]
        
        if not self.api_key or self.api_key == 'YOUR_API_KEY':
            return None
        
        try:
            # Търсене на отбора
            url = f"{self.base_url}/teams"
            params = {'name': team_name}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('teams'):
                    team_id = data['teams'][0]['id']
                    
                    # Вземане на статистики
                    stats_url = f"{self.base_url}/teams/{team_id}/matches"
                    params = {
                        'status': 'FINISHED',
                        'limit': 10  # Последни 10 мача
                    }
                    
                    stats_response = requests.get(stats_url, headers=self.headers, params=params, timeout=10)
                    
                    if stats_response.status_code == 200:
                        matches_data = stats_response.json()
                        stats = self._parse_team_stats(matches_data, team_name)
                        self.team_cache[cache_key] = stats
                        return stats
        except:
            pass
        
        return None
    
    def _parse_team_stats(self, matches_data: Dict, team_name: str) -> Dict:
        """
        Обработва статистики от мачове
        
        Args:
            matches_data: Данни за мачове
            team_name: Име на отбора
            
        Returns:
            Dict: Обработени статистики
        """
        matches = matches_data.get('matches', [])
        
        stats = {
            'wins': 0,
            'draws': 0,
            'losses': 0,
            'goals_scored': 0,
            'goals_conceded': 0,
            'home_wins': 0,
            'home_games': 0,
            'away_wins': 0,
            'away_games': 0,
            'form': []  # Последни 5 мача (W/D/L)
        }
        
        for match in matches[:10]:
            home_team = match.get('homeTeam', {}).get('name', '')
            away_team = match.get('awayTeam', {}).get('name', '')
            score = match.get('score', {}).get('fullTime', {})
            
            home_score = score.get('home', 0)
            away_score = score.get('away', 0)
            
            is_home = home_team == team_name
            team_score = home_score if is_home else away_score
            opponent_score = away_score if is_home else home_score
            
            stats['goals_scored'] += team_score
            stats['goals_conceded'] += opponent_score
            
            # Определяне на резултата
            if team_score > opponent_score:
                stats['wins'] += 1
                stats['form'].append('W')
                if is_home:
                    stats['home_wins'] += 1
                else:
                    stats['away_wins'] += 1
            elif team_score < opponent_score:
                stats['losses'] += 1
                stats['form'].append('L')
            else:
                stats['draws'] += 1
                stats['form'].append('D')
            
            if is_home:
                stats['home_games'] += 1
            else:
                stats['away_games'] += 1
        
        # Форма - само последните 5
        stats['form'] = stats['form'][:5]
        
        return stats
    
    def predict_match(self, match: Dict) -> Dict:
        """
        Прогнозира резултат на мач на база реална статистика или коефициенти
        
        Args:
            match: Информация за мача
            
        Returns:
            Dict: Прогноза с вероятности
        """
        home_team = match.get('home_team', '')
        away_team = match.get('away_team', '')
        league = match.get('league', '')
        
        # Проверка дали има коефициенти от API
        home_odds_api = match.get('home_odds')
        draw_odds_api = match.get('draw_odds')
        away_odds_api = match.get('away_odds')
        
        # Ако има коефициенти, използвай ги
        if home_odds_api and draw_odds_api and away_odds_api:
            home_win_prob, draw_prob, away_win_prob = self._probabilities_from_odds(
                home_odds_api, draw_odds_api, away_odds_api
            )
            home_odds = home_odds_api
            draw_odds = draw_odds_api
            away_odds = away_odds_api
        else:
            # Опит за вземане на реална статистика
            home_stats = self.get_team_stats(home_team, league)
            away_stats = self.get_team_stats(away_team, league)
            
            # Изчисляване на вероятности
            home_win_prob, draw_prob, away_win_prob = self._calculate_match_probabilities(
                home_team, away_team, match, home_stats, away_stats
            )
            
            # Изчисляване на коефициенти (букмейкърски)
            home_odds = round(100 / home_win_prob, 2) if home_win_prob > 0 else 999
            draw_odds = round(100 / draw_prob, 2) if draw_prob > 0 else 999
            away_odds = round(100 / away_win_prob, 2) if away_win_prob > 0 else 999
        
        # Класификация на прогнозата
        prediction_class = self._classify_prediction(home_win_prob)
        
        # Изчисляване на допълнителни прогнози за голове
        home_stats = self.get_team_stats(home_team, league)
        away_stats = self.get_team_stats(away_team, league)
        over_2_5_prob = self._calculate_over_2_5_goals(home_team, away_team, match, home_stats, away_stats)
        first_half_goals_prob = self._calculate_first_half_goals(home_team, away_team, match, home_stats, away_stats)
        btts_prob = self._calculate_btts(home_team, away_team, match, home_stats, away_stats)
        
        # Препоръка базирана на всички статистики
        recommendation = self._get_smart_recommendation(
            home_win_prob, draw_prob, away_win_prob,
            over_2_5_prob, first_half_goals_prob, btts_prob
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
    
    def _calculate_match_probabilities(
        self, home_team: str, away_team: str, match: Dict,
        home_stats: Optional[Dict] = None, away_stats: Optional[Dict] = None
    ) -> tuple:
        """
        Изчислява вероятности базирани на реална статистика
        
        Args:
            home_team: Име на домакин
            away_team: Име на гост
            match: Информация за мача
            home_stats: Статистики на домакина
            away_stats: Статистики на госта
            
        Returns:
            tuple: (home_win_prob, draw_prob, away_win_prob)
        """
        # Ако няма реална статистика, използвай базови вероятности
        if not home_stats or not away_stats:
            return self._calculate_fallback_probabilities(home_team, away_team, match)
        
        # Базови вероятности с домакинско предимство
        home_win = 40.0
        draw = 30.0
        away_win = 30.0
        
        # Фактор 1: Форма (последни 5 мача)
        home_form_score = self._calculate_form_score(home_stats.get('form', []))
        away_form_score = self._calculate_form_score(away_stats.get('form', []))
        
        form_diff = home_form_score - away_form_score
        home_win += form_diff * 2
        away_win -= form_diff * 2
        
        # Фактор 2: Win rate (процент победи)
        home_total_games = home_stats.get('wins', 0) + home_stats.get('draws', 0) + home_stats.get('losses', 0)
        away_total_games = away_stats.get('wins', 0) + away_stats.get('draws', 0) + away_stats.get('losses', 0)
        
        if home_total_games > 0:
            home_win_rate = (home_stats.get('wins', 0) / home_total_games) * 100
            home_win += (home_win_rate - 33) * 0.4  # 33% е базата
        
        if away_total_games > 0:
            away_win_rate = (away_stats.get('wins', 0) / away_total_games) * 100
            away_win += (away_win_rate - 33) * 0.3  # По-малък коефициент за гости
        
        # Фактор 3: Голова разлика (отбелязани vs допуснати)
        if home_total_games > 0:
            home_goal_diff = (home_stats.get('goals_scored', 0) - home_stats.get('goals_conceded', 0)) / home_total_games
            home_win += home_goal_diff * 3
        
        if away_total_games > 0:
            away_goal_diff = (away_stats.get('goals_scored', 0) - away_stats.get('goals_conceded', 0)) / away_total_games
            away_win += away_goal_diff * 2.5
        
        # Фактор 4: Home/Away специфична форма
        if home_stats.get('home_games', 0) > 0:
            home_win_home_rate = (home_stats.get('home_wins', 0) / home_stats.get('home_games', 1)) * 100
            home_win += (home_win_home_rate - 40) * 0.3
        
        if away_stats.get('away_games', 0) > 0:
            away_win_away_rate = (away_stats.get('away_wins', 0) / away_stats.get('away_games', 1)) * 100
            away_win += (away_win_away_rate - 25) * 0.3
        
        # Фактор 5: Топ лиги - повече равни
        league = match.get('league', '')
        if any(l in league for l in ['Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1']):
            draw += 5
            home_win -= 2.5
            away_win -= 2.5
        
        # Случаен фактор (симулира непредвидими фактори)
        random_factor = random.uniform(-4, 4)
        home_win += random_factor
        away_win -= random_factor
        
        # Нормализиране - сумата трябва да е 100%
        total = home_win + draw + away_win
        home_win = (home_win / total) * 100
        draw = (draw / total) * 100
        away_win = (away_win / total) * 100
        
        # Ограничаване на минимални/максимални стойности
        home_win = max(10, min(80, home_win))
        draw = max(10, min(40, draw))
        away_win = max(10, min(75, away_win))
        
        # Финална нормализация
        total = home_win + draw + away_win
        home_win = (home_win / total) * 100
        draw = (draw / total) * 100
        away_win = (away_win / total) * 100
        
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
        over_2_5: float, first_half: float, btts: float
    ) -> str:
        """
        Интелигентна препоръка базирана на всички статистики
        
        Args:
            home_prob: Вероятност за победа домакин
            draw_prob: Вероятност за равен
            away_prob: Вероятност за победа гост
            over_2_5: Вероятност за над 2.5 гола
            first_half: Вероятност за гол в 1во полувреме
            btts: Вероятност за BTTS
            
        Returns:
            str: Препоръка за залог
        """
        recommendations = []
        
        # Проверка за резултат (1/X/2)
        if home_prob >= 65:
            recommendations.append(f"1 (Домакин {home_prob:.0f}%)")
        elif away_prob >= 60:
            recommendations.append(f"2 (Гост {away_prob:.0f}%)")
        elif draw_prob >= 35:
            recommendations.append(f"X (Равен {draw_prob:.0f}%)")
        
        # Double Chance
        if home_prob + draw_prob >= 75:
            recommendations.append(f"1X ({home_prob + draw_prob:.0f}%)")
        elif away_prob + draw_prob >= 70:
            recommendations.append(f"X2 ({away_prob + draw_prob:.0f}%)")
        elif home_prob + away_prob >= 75:
            recommendations.append(f"12 ({home_prob + away_prob:.0f}%)")
        
        # Голове
        if over_2_5 >= 65:
            recommendations.append(f"Над 2.5 ({over_2_5:.0f}%)")
        elif over_2_5 <= 35:
            recommendations.append(f"Под 2.5 ({100 - over_2_5:.0f}%)")
        
        if first_half >= 65:
            recommendations.append(f"Гол 1во пол. ({first_half:.0f}%)")
        
        if btts >= 65:
            recommendations.append(f"BTTS Да ({btts:.0f}%)")
        elif btts <= 35:
            recommendations.append(f"BTTS Не ({100 - btts:.0f}%)")
        
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
                return f"Леко предимство: 1 ({home_prob:.0f}%)"
            elif max_prob == away_prob:
                return f"Леко предимство: 2 ({away_prob:.0f}%)"
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
        
        Args:
            matches: Списък с мачове
            
        Returns:
            List[Dict]: Прогнози, сортирани по вероятност
        """
        predictions = []
        
        for match in matches:
            prediction = self.predict_match(match)
            predictions.append(prediction)
        
        # Сортиране по вероятност (намаляващ ред)
        predictions.sort(key=lambda x: x['home_win_probability'], reverse=True)
        
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
