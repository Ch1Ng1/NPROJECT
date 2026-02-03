# 🚀 Deployment & DevOps Improvements

## 1. **Docker Support**

### Dockerfile
```dockerfile
FROM python:3.11-slim

# Работна директория
WORKDIR /app

# Копирай requirements
COPY requirements.txt .

# Инсталирай dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Копирай приложението
COPY . .

# Създай необходими директории
RUN mkdir -p logs cache

# Експозирай порт
EXPOSE 5000

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/stats')"

# Стартирай приложението
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]
```

### docker-compose.yml
```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DB_HOST=mysql
      - DB_USER=root
      - DB_PASSWORD=password
      - DB_NAME=football_predictor
      - API_FOOTBALL_KEY=${API_FOOTBALL_KEY}
    depends_on:
      - mysql
      - redis
    volumes:
      - ./logs:/app/logs
      - ./cache:/app/cache
    networks:
      - app-network
    restart: unless-stopped

  mysql:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=password
      - MYSQL_DATABASE=football_predictor
    ports:
      - "3306:3306"
    volumes:
      - mysql-data:/var/lib/mysql
      - ./database.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - app-network
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    networks:
      - app-network
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    networks:
      - app-network
    restart: unless-stopped

volumes:
  mysql-data:
  redis-data:

networks:
  app-network:
    driver: bridge
```

### .dockerignore
```
.git
.gitignore
.venv
venv
__pycache__
*.pyc
*.pyo
*.log
.env
.env.local
.DS_Store
Thumbs.db
*.md
tests/
.vscode/
.idea/
```

---

## 2. **CI/CD Pipeline**

### GitHub Actions

#### `.github/workflows/ci.yml`
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov flake8 black mypy
    
    - name: Lint with flake8
      run: flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
    
    - name: Check formatting with black
      run: black --check .
    
    - name: Type check with mypy
      run: mypy . --ignore-missing-imports
    
    - name: Run tests
      run: |
        pytest tests/ --cov=. --cov-report=xml --cov-report=term
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests

  build:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: docker build -t football-predictor:${{ github.sha }} .
    
    - name: Test Docker image
      run: |
        docker run -d -p 5000:5000 --name test-app football-predictor:${{ github.sha }}
        sleep 10
        curl -f http://localhost:5000/ || exit 1
        docker stop test-app

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to production
      run: echo "Deploy to production server"
      # Добави deployment скрипт тук
```

---

## 3. **Nginx Configuration**

### nginx.conf
```nginx
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:5000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=general_limit:10m rate=100r/s;

    server {
        listen 80;
        server_name your-domain.com;

        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;

        # Compression
        gzip on;
        gzip_vary on;
        gzip_min_length 1024;
        gzip_types text/plain text/css text/xml text/javascript application/javascript application/json;

        # Static files
        location /static/ {
            alias /app/static/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }

        # API routes with rate limiting
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
        }

        # General routes
        location / {
            limit_req zone=general_limit burst=50 nodelay;
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check
        location /health {
            access_log off;
            proxy_pass http://app/api/stats;
        }
    }
}
```

---

## 4. **Production WSGI Server**

### gunicorn_config.py
```python
"""Gunicorn конфигурация за production"""
import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', 5000)}"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = 'logs/gunicorn_access.log'
errorlog = 'logs/gunicorn_error.log'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Process naming
proc_name = 'football_predictor'

# Server mechanics
daemon = False
pidfile = 'gunicorn.pid'
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (ако не използваш nginx)
# keyfile = 'ssl/key.pem'
# certfile = 'ssl/cert.pem'

# Preload app
preload_app = True

# Server hooks
def on_starting(server):
    print("🚀 Starting Gunicorn server...")

def on_reload(server):
    print("🔄 Reloading Gunicorn...")

def when_ready(server):
    print("✅ Gunicorn ready to serve requests")

def on_exit(server):
    print("🛑 Shutting down Gunicorn...")
```

### Стартиране:
```bash
gunicorn --config gunicorn_config.py app:app
```

---

## 5. **Monitoring & Logging**

### Prometheus metrics

```python
# metrics.py
from prometheus_flask_exporter import PrometheusMetrics

def init_metrics(app):
    """Инициализира Prometheus metrics"""
    metrics = PrometheusMetrics(app)
    
    # Custom metrics
    metrics.info('app_info', 'Application info', version='2.0')
    
    # Request duration histogram
    @metrics.histogram('request_duration_seconds', 'Request duration')
    def before_request():
        pass
    
    return metrics
```

### В app.py:
```python
from metrics import init_metrics

metrics = init_metrics(app)

# Custom counter
prediction_counter = metrics.counter(
    'predictions_total',
    'Total predictions made',
    labels={'type': lambda: 'api'}
)

@app.route('/api/predictions')
@prediction_counter
def get_predictions():
    ...
```

### Grafana Dashboard (JSON export)
```json
{
  "dashboard": {
    "title": "Football Predictor Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(flask_http_request_total[5m])"
          }
        ]
      },
      {
        "title": "Response Time",
        "targets": [
          {
            "expr": "flask_http_request_duration_seconds_bucket"
          }
        ]
      }
    ]
  }
}
```

---

## 6. **Environment Management**

### .env.production
```bash
# Production Environment Variables
FLASK_ENV=production
FLASK_DEBUG=False

# Server
HOST=0.0.0.0
PORT=5000

# Database
DB_HOST=mysql
DB_USER=prod_user
DB_PASSWORD=strong_password_here
DB_NAME=football_predictor
DB_PORT=3306

# API
API_FOOTBALL_KEY=your_production_api_key
API_TIMEOUT=10
MAX_RETRIES=3

# Cache
CACHE_DURATION=3600
REDIS_HOST=redis
REDIS_PORT=6379

# Logging
LOG_LEVEL=WARNING
LOG_FILE=logs/app.log

# Security
SECRET_KEY=generate_strong_secret_key_here
```

### Генериране на SECRET_KEY:
```python
import secrets
print(secrets.token_hex(32))
```

---

## 7. **Backup Strategy**

### backup.sh
```bash
#!/bin/bash

# Backup скрипт за база данни и файлове

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_NAME="football_predictor"

# Създай backup директория
mkdir -p $BACKUP_DIR

# Database backup
docker exec mysql mysqldump -u root -p$DB_PASSWORD $DB_NAME > "$BACKUP_DIR/db_$DATE.sql"

# Compress
gzip "$BACKUP_DIR/db_$DATE.sql"

# Cache backup
tar -czf "$BACKUP_DIR/cache_$DATE.tar.gz" cache/

# Logs backup
tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" logs/

# Изтрий стари backups (по-стари от 30 дни)
find $BACKUP_DIR -name "*.gz" -type f -mtime +30 -delete

echo "✅ Backup завършен: $DATE"
```

### Cron job за автоматични backups:
```bash
# Добави в crontab -e
0 2 * * * /path/to/backup.sh >> /var/log/backup.log 2>&1
```

---

## 8. **Deploy Script**

### deploy.sh
```bash
#!/bin/bash

echo "🚀 Starting deployment..."

# Pull latest code
git pull origin main

# Build Docker images
docker-compose build

# Stop old containers
docker-compose down

# Start new containers
docker-compose up -d

# Wait for services to be ready
sleep 10

# Health check
curl -f http://localhost/api/stats || {
    echo "❌ Health check failed!"
    docker-compose logs
    exit 1
}

echo "✅ Deployment successful!"

# Clean up old Docker images
docker image prune -f
```

---

## Стъпки за deployment:

```bash
# 1. Build
docker-compose build

# 2. Test locally
docker-compose up

# 3. Push to production
./deploy.sh

# 4. Monitor
docker-compose logs -f

# 5. Check health
curl https://your-domain.com/api/stats
```
