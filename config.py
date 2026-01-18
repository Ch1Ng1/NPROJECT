"""
Конфигурационен файл за приложението
"""

import os
from dotenv import load_dotenv

# Зареждане на променливи от .env файл
load_dotenv()

class Config:
    """Основна конфигурация"""
    
    # API-Football конфигурация
    # Получете безплатен API ключ от: https://www.api-football.com/
    API_FOOTBALL_KEY = os.environ.get('API_FOOTBALL_KEY', '')
    
    # Football-Data.org API конфигурация
    FOOTBALL_DATA_KEY = os.environ.get('FOOTBALL_DATA_KEY', '')
    
    # Flask конфигурация
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # Прогнозиране - настройки
    MIN_PROBABILITY_DEFAULT = 60.0
    MAX_RESULTS_DEFAULT = 10
    
    # Домакинско предимство (%)
    HOME_ADVANTAGE = 5.0
    
    # Тайм зона
    TIMEZONE = 'Europe/Sofia'


class ProductionConfig(Config):
    """Продукционна конфигурация"""
    DEBUG = False


class DevelopmentConfig(Config):
    """Development конфигурация"""
    DEBUG = True


# Избор на конфигурация според среда
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
