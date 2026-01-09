"""
Конфигурационен файл за приложението
"""

import os

class Config:
    """Основна конфигурация"""
    
    # API-Football конфигурация
    # Получете безплатен API ключ от: https://www.api-football.com/
    API_FOOTBALL_KEY = os.environ.get('API_FOOTBALL_KEY', 'YOUR_API_KEY')
    
    # Flask конфигурация
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = True
    
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
