"""
🧪 Unit Tests за SmartPredictor
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from predictor import SmartPredictor
import requests


class TestSmartPredictor:
    """Тестове за SmartPredictor клас"""
    
    def test_initialization_with_valid_api_key(self):
        """Тест: Инициализация с валиден API ключ"""
        predictor = SmartPredictor(api_key="valid_key_12345")
        assert predictor.api_key == "valid_key_12345"
        assert predictor.INITIAL_ELO == 1500
    
    def test_initialization_with_empty_api_key(self):
        """Тест: Инициализация с празен API ключ трябва да хвърли грешка"""
        with pytest.raises(ValueError, match="API ключът трябва да е непразна строка"):
            SmartPredictor(api_key="")
    
    def test_initialization_with_short_api_key(self):
        """Тест: Инициализация с къс API ключ трябва да хвърли грешка"""
        with pytest.raises(ValueError, match="API ключът има неправилната дължина"):
            SmartPredictor(api_key="short")
    
    def test_initialization_with_none_api_key(self):
        """Тест: Инициализация с None API ключ трябва да хвърли грешка"""
        with pytest.raises(ValueError):
            SmartPredictor(api_key=None)
    
    def test_calculate_elo_home_win(self):
        """Тест: ELO калкулация при домакинска победа"""
        predictor = SmartPredictor(api_key="valid_key_12345")
        predictor.elo_ratings[1] = 1500
        predictor.elo_ratings[2] = 1500
        
        home_elo, away_elo = predictor._calculate_elo(1, 2, home_score=2, away_score=0)
        
        assert home_elo > 1500  # Домакинът трябва да се увеличи
        assert away_elo < 1500  # Гостът трябва да намалее
    
    def test_calculate_elo_draw(self):
        """Тест: ELO калкулация при равенство"""
        predictor = SmartPredictor(api_key="valid_key_12345")
        predictor.elo_ratings[1] = 1600
        predictor.elo_ratings[2] = 1400
        
        home_elo, away_elo = predictor._calculate_elo(1, 2, home_score=1, away_score=1)
        
        # При равенство по-силният отбор губи, по-слабият печели
        assert home_elo < 1600
        assert away_elo > 1400
    
    def test_parse_form_valid(self):
        """Тест: Парсване на валидна форма"""
        predictor = SmartPredictor(api_key="valid_key_12345")
        points = predictor._parse_form("WWDLW")
        assert points == 3 + 3 + 1 + 0 + 3  # 10 точки
    
    def test_parse_form_empty(self):
        """Тест: Парсване на празна форма"""
        predictor = SmartPredictor(api_key="valid_key_12345")
        points = predictor._parse_form("")
        assert points == 0
    
    def test_parse_form_invalid_characters(self):
        """Тест: Парсване на форма с невалидни символи"""
        predictor = SmartPredictor(api_key="valid_key_12345")
        points = predictor._parse_form("WWXYZ")
        assert points == 6  # Само W и W се броят
    
    @patch('predictor.requests.Session.get')
    def test_api_call_success(self, mock_get):
        """Тест: Успешно API извикване"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'response': []}
        mock_get.return_value = mock_response
        
        predictor = SmartPredictor(api_key="valid_key_12345")
        result = predictor._make_api_call('/fixtures')
        
        assert result == {'response': []}
        assert mock_get.called
    
    @patch('predictor.requests.Session.get')
    def test_api_call_timeout(self, mock_get):
        """Тест: API timeout обработка"""
        mock_get.side_effect = requests.Timeout("Connection timeout")
        
        predictor = SmartPredictor(api_key="valid_key_12345")
        result = predictor._make_api_call('/fixtures')
        
        assert result is None
    
    @patch('predictor.requests.Session.get')
    def test_api_call_http_error(self, mock_get):
        """Тест: HTTP грешка обработка"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_get.return_value = mock_response
        
        predictor = SmartPredictor(api_key="valid_key_12345")
        result = predictor._make_api_call('/fixtures')
        
        assert result is None
    
    def test_calculate_probabilities(self):
        """Тест: Калкулация на вероятности"""
        predictor = SmartPredictor(api_key="valid_key_12345")
        
        # Симулиране на равностоен мач
        fixture = {
            'teams': {
                'home': {'id': 1, 'name': 'Team A'},
                'away': {'id': 2, 'name': 'Team B'}
            }
        }
        
        predictor.elo_ratings[1] = 1500
        predictor.elo_ratings[2] = 1500
        
        home_stats = {'form': 'WWWWW', 'goals_avg': 2.0, 'yellow_cards_avg': 2.0, 'corners_avg': 5.0}
        away_stats = {'form': 'LLLLL', 'goals_avg': 0.5, 'yellow_cards_avg': 3.0, 'corners_avg': 3.0}
        
        result = predictor._analyze_match(fixture, home_stats, away_stats)
        
        assert result is not None
        assert 'probabilities' in result
        assert 'prediction' in result
        assert result['probabilities']['home'] > result['probabilities']['away']
    
    def test_get_stats(self):
        """Тест: Получаване на статистики"""
        predictor = SmartPredictor(api_key="valid_key_12345")
        predictor.elo_ratings[1] = 1600
        predictor.elo_ratings[2] = 1400
        
        stats = predictor.get_stats()
        
        assert stats['total_teams'] == 2
        assert stats['avg_elo'] == 1500.0
        assert stats['api_key_configured'] is True
        assert stats['system_status'] == 'operational'
    
    def test_league_averages(self):
        """Тест: Лигови средни стойности"""
        predictor = SmartPredictor(api_key="valid_key_12345")
        
        # Premier League
        cards, corners = predictor._get_league_averages(39)
        assert cards > 0
        assert corners > 0
        
        # Неизвестна лига
        cards, corners = predictor._get_league_averages(99999)
        assert cards == 2.8  # Дефолт
        assert corners == 10.5  # Дефолт


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
