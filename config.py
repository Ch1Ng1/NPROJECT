"""
⚙️ Configuration Management
Централизирано управление на конфигурациите за приложението
"""
import os
from dotenv import load_dotenv
from typing import Optional
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    """Основна конфигурация"""
    
    # Flask
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # API Configuration
    API_KEY = os.getenv('API_FOOTBALL_KEY', '').strip()
    API_TIMEOUT = int(os.getenv('API_TIMEOUT', 10))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
    
    # Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'football_predictor')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', 5))
    
    # Cache Configuration
    CACHE_DURATION = int(os.getenv('CACHE_DURATION', 3600))  # 1 час
    MAX_PREDICTIONS = int(os.getenv('MAX_PREDICTIONS', 20))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    
    @classmethod
    def validate(cls) -> bool:
        """Валидира конфигурацията"""
        errors = []
        
        if not cls.API_KEY:
            errors.append("❌ API_FOOTBALL_KEY не е задан в .env файла")
        
        if cls.PORT < 1000 or cls.PORT > 65535:
            errors.append(f"❌ PORT {cls.PORT} е извън допустимия диапазон (1000-65535)")
        
        if cls.DB_PORT < 1000 or cls.DB_PORT > 65535:
            errors.append(f"❌ DB_PORT {cls.DB_PORT} е извън допустимия диапазон (1000-65535)")
        
        if errors:
            for error in errors:
                logger.warning(error)
            return False
        
        return True
    
    @classmethod
    def get_db_config(cls) -> dict:
        """Връща конфигурацията за базата данни"""
        return {
            'host': cls.DB_HOST,
            'user': cls.DB_USER,
            'password': cls.DB_PASSWORD,
            'database': cls.DB_NAME,
            'port': cls.DB_PORT,
            'autocommit': True,
            'pool_size': cls.DB_POOL_SIZE,
            'pool_reset_session': True
        }
    
    @classmethod
    def get_api_headers(cls) -> dict:
        """Връща headers за API заявките"""
        return {
            'x-apisports-key': cls.API_KEY,
            'User-Agent': 'SmartFootballPredictor/2.0'
        }
    
    @classmethod
    def log_config(cls) -> None:
        """Логира текущата конфигурация (без чувствителни данни)"""
        logger.info("⚙️  Конфигурация на приложението:")
        logger.info(f"  📍 Хост: {cls.HOST}:{cls.PORT}")
        logger.info(f"  🗄️  База данни: {cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}")
        logger.info(f"  🔑 API ключ: {'✅ Конфигуриран' if cls.API_KEY else '❌ Липсва'}")
        logger.info(f"  💾 Кеш длителност: {cls.CACHE_DURATION}с")
        logger.info(f"  🎯 Максимум прогнози: {cls.MAX_PREDICTIONS}")
