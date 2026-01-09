"""
Модул за прогнозиране на победители в футболни мачове
Използва различни фактори за определяне на вероятността за победа на домакина
"""

import random
from typing import Dict, List
from datetime import datetime


class MatchPredictor:
    """Клас за прогнозиране на резултати от футболни мачове"""
    
    def __init__(self):
        """Инициализация на предиктора"""
        # Известни силни отбори (за демо целите)
        self.strong_teams = {
            'Manchester United', 'Liverpool', 'Manchester City', 'Chelsea', 'Arsenal',
            'Real Madrid', 'Barcelona', 'Atletico Madrid',
            'Bayern Munich', 'Borussia Dortmund',
            'Juventus', 'AC Milan', 'Inter Milan',
            'Paris Saint Germain', 'Monaco'
        }
        
        # Известни слаби отбори
        self.weak_teams = {
            'Norwich', 'Watford', 'Burnley',
            'Huesca', 'Eibar',
            'Crotone', 'Benevento'
        }
    
    def predict_match(self, match: Dict) -> Dict:
        """
        Прогнозира резултат на мач
        
        Args:
            match: Информация за мача
            
        Returns:
            Dict: Прогноза с вероятности
        """
        home_team = match.get('home_team', '')
        away_team = match.get('away_team', '')
        
        # Изчисляване на вероятности за всички изходи
        home_win_prob, draw_prob, away_win_prob = self._calculate_match_probabilities(
            home_team, away_team, match
        )
        
        # Изчисляване на коефициенти (букмейкърски)
        home_odds = round(100 / home_win_prob, 2) if home_win_prob > 0 else 999
        draw_odds = round(100 / draw_prob, 2) if draw_prob > 0 else 999
        away_odds = round(100 / away_win_prob, 2) if away_win_prob > 0 else 999
        
        # Класификация на прогнозата
        prediction_class = self._classify_prediction(home_win_prob)
        
        # Препоръка
        recommendation = self._get_recommendation(home_win_prob)
        
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
            'confidence': self._calculate_confidence(home_win_prob, draw_prob, away_win_prob)
        }
        
        return result
    
    def _calculate_match_probabilities(
        self, home_team: str, away_team: str, match: Dict
    ) -> tuple:
        """
        Изчислява вероятности за победа домакин, равен и победа гост
        
        Args:
            home_team: Име на домакин
            away_team: Име на гост
            match: Информация за мача
            
        Returns:
            tuple: (home_win_prob, draw_prob, away_win_prob)
        """
        # Базови вероятности
        home_win = 45.0  # Домакинско предимство
        draw = 27.0      # Базова вероятност за равен
        away_win = 28.0  # Победа на гост
        
        # Фактор 1: Сила на отборите
        if home_team in self.strong_teams:
            home_win += 20
            draw -= 5
            away_win -= 15
        elif home_team in self.weak_teams:
            home_win -= 15
            draw -= 5
            away_win += 20
        
        if away_team in self.strong_teams:
            home_win -= 15
            draw -= 5
            away_win += 20
        elif away_team in self.weak_teams:
            home_win += 20
            draw -= 5
            away_win -= 15
        
        # Фактор 2: И двата отбора силни - по-голям шанс за равен
        if home_team in self.strong_teams and away_team in self.strong_teams:
            draw += 10
            home_win -= 5
            away_win -= 5
        
        # Фактор 3: И двата слаби - по-малък шанс за равен
        if home_team in self.weak_teams and away_team in self.weak_teams:
            draw -= 5
            home_win += 2.5
            away_win += 2.5
        
        # Фактор 4: Тип на първенството
        league = match.get('league', '')
        if any(l in league for l in ['Premier League', 'La Liga', 'Serie A', 'Bundesliga']):
            # В топ лиги има повече равни резултати
            draw += 5
            home_win -= 2.5
            away_win -= 2.5
        
        # Фактор 5: Час на мача
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
        
        # Фактор 6: Случаен фактор (симулира форма, тактика и т.н.)
        import random
        random_home = random.uniform(-3, 3)
        random_away = random.uniform(-3, 3)
        random_draw = random.uniform(-2, 2)
        
        home_win += random_home
        away_win += random_away
        draw += random_draw
        
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
