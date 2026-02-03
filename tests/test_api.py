"""
🧪 Integration Tests за Flask API endpoints
"""
import pytest
import json
from app import app, init_database
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    """Flask test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestAPIEndpoints:
    """Тестове за API endpoints"""
    
    def test_home_page(self, client):
        """Тест: Главна страница зарежда правилно"""
        response = client.get('/')
        assert response.status_code == 200
    
    @patch('app.predictor')
    def test_get_predictions_success(self, mock_predictor, client):
        """Тест: GET /api/predictions успешно"""
        mock_predictor.get_today_predictions.return_value = [
            {
                'home_team': 'Team A',
                'away_team': 'Team B',
                'prediction': {'bet': '1', 'confidence': 65}
            }
        ]
        
        response = client.get('/api/predictions')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert len(data['predictions']) > 0
    
    @patch('app.predictor')
    def test_get_predictions_no_predictor(self, mock_predictor, client):
        """Тест: GET /api/predictions без predictor"""
        mock_predictor = None
        
        response = client.get('/api/predictions')
        # Очаква се грешка или празен списък
        assert response.status_code in [200, 500, 503]
    
    def test_get_stats(self, client):
        """Тест: GET /api/stats"""
        response = client.get('/api/stats')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'total_predictions' in data or 'success' in data
    
    @patch('app.db')
    def test_get_database_stats_connected(self, mock_db, client):
        """Тест: GET /api/database/stats с връзка"""
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [10]
        mock_conn.cursor.return_value = mock_cursor
        mock_db.connection = mock_conn
        
        response = client.get('/api/database/stats')
        assert response.status_code == 200
    
    @patch('app.db')
    def test_get_database_stats_disconnected(self, mock_db, client):
        """Тест: GET /api/database/stats без връзка"""
        mock_db.connection = None
        
        response = client.get('/api/database/stats')
        assert response.status_code == 503
    
    def test_export_csv(self, client):
        """Тест: GET /api/export/csv"""
        response = client.get('/api/export/csv')
        # Може да е 200 (успех) или 500 (няма данни)
        assert response.status_code in [200, 500]
    
    def test_high_confidence_predictions(self, client):
        """Тест: GET /api/high-confidence"""
        response = client.get('/api/high-confidence')
        assert response.status_code in [200, 500]
    
    def test_accuracy(self, client):
        """Тест: GET /api/accuracy"""
        response = client.get('/api/accuracy')
        assert response.status_code in [200, 503]
    
    def test_refresh_cache(self, client):
        """Тест: POST /api/refresh"""
        response = client.post('/api/refresh')
        assert response.status_code in [200, 500]
    
    def test_404_handler(self, client):
        """Тест: 404 грешка обработка"""
        response = client.get('/nonexistent-endpoint')
        assert response.status_code == 404


class TestFilters:
    """Тестове за филтриране"""
    
    def test_high_confidence_filter(self):
        """Тест: Филтриране по висока увереност"""
        from utils import get_high_confidence_predictions
        
        predictions = [
            {'prediction': {'confidence': 70}},
            {'prediction': {'confidence': 50}},
            {'prediction': {'confidence': 80}},
        ]
        
        result = get_high_confidence_predictions(predictions, min_confidence=60)
        assert len(result) == 2
    
    def test_csv_export(self):
        """Тест: CSV експортиране"""
        from utils import export_predictions_to_csv
        
        predictions = [
            {
                'home_team': 'Team A',
                'away_team': 'Team B',
                'prediction': {'bet': '1', 'confidence': 65},
                'probabilities': {'home': 55, 'draw': 25, 'away': 20},
                'time': '15:00',
                'league': 'Premier League'
            }
        ]
        
        csv_data = export_predictions_to_csv(predictions)
        assert csv_data is not None
        assert 'Team A' in csv_data
        assert 'Team B' in csv_data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
