# 🎯 Code Quality Improvements

## 1. **Linting и Formatting**

### Setup:
```bash
pip install black flake8 pylint mypy isort
```

### Конфигурация:

#### `.flake8`
```ini
[flake8]
max-line-length = 100
exclude = .git,__pycache__,.venv,venv,build,dist
ignore = E203, W503
per-file-ignores =
    __init__.py:F401
```

#### `pyproject.toml`
```toml
[tool.black]
line-length = 100
target-version = ['py39', 'py310', 'py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.venv
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3
include_trailing_comma = true

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### Pre-commit hooks:

#### `.pre-commit-config.yaml`
```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.0
    hooks:
      - id: black
        language_version: python3.9

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8

  - repo: https://github.com/pycqa/isort
    rev: 5.13.0
    hooks:
      - id: isort

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

```bash
# Инсталиране
pip install pre-commit
pre-commit install

# Ръчно пускане
pre-commit run --all-files
```

---

## 2. **Type Hints подобрения**

### Проблеми в текущия код:

#### predictor.py
```python
# ПРЕДИ:
def _make_api_call(self, endpoint: str, params: dict = None):
    # dict е твърде общо

# СЛЕД:
from typing import Dict, Any, Optional

def _make_api_call(
    self, 
    endpoint: str, 
    params: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    ...
```

#### database.py
```python
# ПРЕДИ:
def get_team_by_id(self, team_id: int):
    # Няма return type

# СЛЕД:
def get_team_by_id(self, team_id: int) -> Optional[Dict[str, Any]]:
    ...
```

---

## 3. **Error Handling подобрения**

### Създай custom exceptions:

```python
# exceptions.py
class FootballPredictorError(Exception):
    """Базова грешка за приложението"""
    pass

class APIError(FootballPredictorError):
    """API грешка"""
    def __init__(self, message: str, status_code: int = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class DatabaseError(FootballPredictorError):
    """Database грешка"""
    pass

class ValidationError(FootballPredictorError):
    """Валидационна грешка"""
    pass

class ConfigurationError(FootballPredictorError):
    """Конфигурационна грешка"""
    pass
```

### Използване:

```python
# В predictor.py
from exceptions import APIError

def _make_api_call(self, endpoint: str, params: dict = None):
    try:
        response = self.session.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as e:
        raise APIError(f"HTTP грешка: {e}", status_code=e.response.status_code)
    except requests.Timeout:
        raise APIError("API timeout", status_code=408)
    except Exception as e:
        raise APIError(f"Неочаквана грешка: {e}")
```

---

## 4. **Docstring подобрения**

### Използвай Google Style:

```python
def calculate_prediction(
    self,
    home_team: str,
    away_team: str,
    league_id: int
) -> Dict[str, Any]:
    """
    Калкулира прогноза за мач между два отбора.
    
    Използва комбинация от ELO рейтинг, форма и статистики за
    генериране на прогноза с ниво на увереност.
    
    Args:
        home_team: Име на домакина
        away_team: Име на госта
        league_id: ID на лигата
        
    Returns:
        Dict съдържащ:
            - prediction (str): '1', 'X' или '2'
            - confidence (float): Увереност в прогнозата (0-100)
            - probabilities (Dict[str, float]): Вероятности за всеки изход
            
    Raises:
        APIError: При проблем с API заявката
        ValidationError: При невалидни входни данни
        
    Example:
        >>> predictor = SmartPredictor(api_key="key")
        >>> result = predictor.calculate_prediction("Arsenal", "Chelsea", 39)
        >>> print(result['prediction'])
        '1'
    """
    ...
```

---

## 5. **Constants и Magic Numbers**

### Проблем:
```python
# В predictor.py - магически числа навсякъде
if confidence >= 60:  # Защо 60?
    ...

avg_elo = 1500  # Защо 1500?
```

### Решение:

```python
# constants.py
"""Константи за приложението"""

# ELO Constants
DEFAULT_ELO_RATING: int = 1500
ELO_K_FACTOR: int = 32
MAX_ELO_CHANGE: int = 50

# Prediction Constants
HIGH_CONFIDENCE_THRESHOLD: int = 60
MEDIUM_CONFIDENCE_THRESHOLD: int = 50
LOW_CONFIDENCE_THRESHOLD: int = 40

# Form Points
FORM_WIN_POINTS: int = 3
FORM_DRAW_POINTS: int = 1
FORM_LOSS_POINTS: int = 0

# API Constants
API_TIMEOUT_SECONDS: int = 10
MAX_API_RETRIES: int = 3
MAX_FIXTURES_PER_REQUEST: int = 30

# Database Constants
MAX_FORM_LENGTH: int = 50
CONNECTION_POOL_SIZE: int = 5

# Cache Constants
DEFAULT_CACHE_DURATION: int = 3600  # 1 час

# League IDs
PREMIER_LEAGUE_ID: int = 39
LA_LIGA_ID: int = 140
BUNDESLIGA_ID: int = 78
SERIE_A_ID: int = 135

TOP_LEAGUE_IDS: set = {
    PREMIER_LEAGUE_ID,
    LA_LIGA_ID,
    BUNDESLIGA_ID,
    SERIE_A_ID,
    # ... други
}
```

### Използване:

```python
from constants import HIGH_CONFIDENCE_THRESHOLD, DEFAULT_ELO_RATING

if prediction['confidence'] >= HIGH_CONFIDENCE_THRESHOLD:
    logger.info("Висока увереност!")

self.elo_ratings = defaultdict(lambda: DEFAULT_ELO_RATING)
```

---

## 6. **Dependency Injection**

### Проблем:
```python
# Твърда зависимост в app.py
predictor = SmartPredictor(api_key=API_KEY)
```

### Решение:

```python
# services.py
from typing import Protocol

class PredictorProtocol(Protocol):
    """Interface за predictor"""
    def get_today_predictions(self) -> List[Dict]:
        ...

class ServiceContainer:
    """Dependency injection контейнер"""
    def __init__(self):
        self._services = {}
    
    def register(self, name: str, service: Any):
        self._services[name] = service
    
    def get(self, name: str) -> Any:
        return self._services.get(name)

# В app.py
container = ServiceContainer()
container.register('predictor', SmartPredictor(api_key=API_KEY))
container.register('database', DatabaseManager())

@app.route('/api/predictions')
def get_predictions():
    predictor = container.get('predictor')
    predictions = predictor.get_today_predictions()
    ...
```

---

## 7. **Environment-specific config**

```python
# config.py
class Config:
    """Базова конфигурация"""
    DEBUG = False
    TESTING = False
    
class DevelopmentConfig(Config):
    """Development конфигурация"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    CACHE_DURATION = 60  # 1 минута за testing
    
class ProductionConfig(Config):
    """Production конфигурация"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    CACHE_DURATION = 3600
    
class TestingConfig(Config):
    """Testing конфигурация"""
    TESTING = True
    DATABASE = 'test_football_predictor'

# В app.py
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

env = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config_map[env])
```

---

## 8. **Logging improvements**

```python
# logging_config.py
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import sys

def setup_logging(app):
    """Конфигурира логването"""
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    # File handler (rotating)
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10485760,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Error handler
    error_handler = TimedRotatingFileHandler(
        'logs/errors.log',
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    
    # Конфигурирай root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)
    
    # Flask app logger
    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

---

## Команди за проверка:

```bash
# Format код
black .

# Sort imports
isort .

# Linting
flake8 .
pylint *.py

# Type checking
mypy .

# Всичко наведнъж
black . && isort . && flake8 . && mypy .
```

## Препоръчителни стъпки:

1. ✅ Инсталирай linting tools
2. ✅ Конфигурирай pre-commit hooks
3. ✅ Създай constants.py
4. ✅ Създай exceptions.py
5. ✅ Подобри docstrings
6. ✅ Добави type hints навсякъде
7. ✅ Настрой environment-specific configs
