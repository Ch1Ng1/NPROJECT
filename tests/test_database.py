"""
🧪 Unit Tests за Database модул
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from database import DatabaseManager
import mysql.connector


class TestDatabaseManager:
    """Тестове за DatabaseManager клас"""
    
    @patch('database.mysql.connector.connect')
    def test_successful_connection(self, mock_connect):
        """Тест: Успешна връзка към базата данни"""
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True
        mock_connect.return_value = mock_conn
        
        db = DatabaseManager()
        
        assert db.connection is not None
        assert mock_connect.called
    
    @patch('database.mysql.connector.connect')
    def test_failed_connection(self, mock_connect):
        """Тест: Неуспешна връзка към базата данни"""
        mock_connect.side_effect = mysql.connector.Error("Connection failed")
        
        db = DatabaseManager()
        
        assert db.connection is None
    
    @patch('database.mysql.connector.connect')
    def test_insert_team(self, mock_connect):
        """Тест: Вмъкване на отбор"""
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        db = DatabaseManager()
        result = db.insert_team(1, "Test Team", "Test Country", "logo.png", "test-venue")
        
        assert mock_cursor.execute.called
        assert mock_conn.commit.called
    
    @patch('database.mysql.connector.connect')
    def test_get_team_by_id(self, mock_connect):
        """Тест: Получаване на отбор по ID"""
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'name': 'Test Team',
            'country': 'Test Country'
        }
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        db = DatabaseManager()
        team = db.get_team_by_id(1)
        
        assert team is not None
        assert team['name'] == 'Test Team'
    
    @patch('database.mysql.connector.connect')
    def test_validate_form_length(self, mock_connect):
        """Тест: Валидация на дължина на форма"""
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True
        mock_connect.return_value = mock_conn
        
        db = DatabaseManager()
        
        # Валидна форма
        assert db._validate_form("WWWWW") is True
        
        # Невалидна форма (твърде дълга)
        long_form = "W" * 100
        assert db._validate_form(long_form) is False
    
    @patch('database.mysql.connector.connect')
    def test_close_connection(self, mock_connect):
        """Тест: Затваряне на връзка"""
        mock_conn = MagicMock()
        mock_conn.is_connected.return_value = True
        mock_connect.return_value = mock_conn
        
        db = DatabaseManager()
        db.close()
        
        assert mock_conn.close.called


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
