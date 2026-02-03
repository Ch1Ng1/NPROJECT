# 🔒 Подобрения по сигурността

## Критични подобрения:

### 1. SQL Injection защита
**Проблем:** В [database.py](database.py#L523) има директно вмъкване на име на таблица:
```python
cursor.execute(f"SELECT COUNT(*) FROM {table}")
```

**Решение:** Използвай whitelist на валидни таблици:
```python
VALID_TABLES = {'teams', 'matches', 'predictions', 'team_statistics'}
if table not in VALID_TABLES:
    raise ValueError(f"Невалидна таблица: {table}")
cursor.execute(f"SELECT COUNT(*) FROM {table}")
```

### 2. Rate Limiting
**Проблем:** Липсва защита от злоупотреба с API endpoints

**Решение:** Добави Flask-Limiter:
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/predictions')
@limiter.limit("10 per minute")
def get_predictions():
    ...
```

### 3. CORS защита
**Проблем:** Липсва CORS конфигурация

**Решение:** Добави Flask-CORS:
```python
from flask_cors import CORS

CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5000"],
        "methods": ["GET", "POST"],
        "allow_headers": ["Content-Type"]
    }
})
```

### 4. Криптиране на чувствителни данни
**Проблем:** API ключът се съхранява в plaintext в .env

**Решение:** Използвай криптиране или key vault сървис

### 5. Input Validation
**Проблем:** Липсва валидация на query параметри

**Решение:** Добави Marshmallow схеми за валидация

### 6. HTTPS
**Проблем:** Приложението работи на HTTP

**Решение:** Конфигурирай SSL/TLS за production или използвай reverse proxy (nginx)

### 7. Защита на headers
**Решение:** Добави Flask-Talisman:
```python
from flask_talisman import Talisman

Talisman(app, 
    force_https=True,
    strict_transport_security=True,
    content_security_policy={
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline'",
        'style-src': "'self' 'unsafe-inline'"
    }
)
```

## Реализация:

```bash
pip install flask-limiter flask-cors flask-talisman marshmallow
```
