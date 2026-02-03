# Пусни всички тестове
pytest tests/ -v --cov=. --cov-report=html --cov-report=term

# Пусни само unit тестове
pytest tests/test_predictor.py -v

# Пусни само integration тестове
pytest tests/test_api.py -v

# Пусни с покритие
pytest tests/ --cov=predictor --cov=database --cov=app --cov-report=html
