# ❓ FAQ - Често задавани въпроси

## 📋 Общи въпроси

### Q: Какво представлява този проект?
**A:** Smart Football Predictor е интелигентна система за прогнозиране на футболни мачове, използваща ELO рейтинг, форма на отборите и статистически данни.

### Q: Откъде идват данните?
**A:** Данните се получават от API-Football (api-sports.io) чрез REST API.

### Q: Колко струва API-то?
**A:** API-Football има безплатен план с ограничения. За production се препоръчва платен план.

---

## 🔧 Технически въпроси

### Q: Защо кешът е изключен по подразбиране?
**A:** За по-лесно тестване и разработка. За production ТРЯБВА да се активира:
```python
# В app.py, промени:
'cache_duration': 3600  # вместо 0
```

### Q: Как да добавя нови лиги?
**A:** Добави ID-та на лигите в `predictor.py`:
```python
TOP_LEAGUES = {
    39,    # Premier League
    140,   # La Liga
    # ... твоите лиги
}
```

### Q: Как да променя максималния брой мачове?
**A:** В `predictor.py`:
```python
MAX_FIXTURES: int = 30  # Промени на желаното число
```

### Q: Защо базата данни не се свързва?
**A:** Провери:
1. XAMPP MySQL сървърът работи ли?
2. `.env` файлът има ли правилни credentials?
3. Базата данни `football_predictor` съществува ли?

```bash
# Създай базата ръчно:
mysql -u root -p
CREATE DATABASE football_predictor;
```

---

## 🐛 Често срещани грешки

### Грешка: "API_FOOTBALL_KEY не е задан"
**Решение:**
1. Създай `.env` файл в root директорията
2. Добави: `API_FOOTBALL_KEY=твоят_ключ`
3. Рестартирай приложението

### Грешка: "Connection refused" (MySQL)
**Решение:**
```bash
# Windows (XAMPP):
1. Стартирай XAMPP Control Panel
2. Start MySQL модула
3. Провери status

# Linux:
sudo systemctl start mysql
```

### Грешка: "Data too long for column 'home_form'"
**Решение:**
Вече е поправено в [database.py](database.py). Ако продължава:
```sql
ALTER TABLE team_statistics MODIFY home_form VARCHAR(50);
ALTER TABLE team_statistics MODIFY away_form VARCHAR(50);
```

### Грешка: "ModuleNotFoundError: No module named 'flask'"
**Решение:**
```bash
pip install -r requirements.txt

# Или за пълни зависимости:
pip install -r requirements-full.txt
```

### Грешка: "429 Too Many Requests"
**Решение:**
- Твоят API план е изчерпан
- Активирай кеширането (виж по-горе)
- Използвай платен API план

---

## 🚀 Deployment въпроси

### Q: Как да deploy-на на production?
**A:** 
**Вариант 1: Docker (Препоръчително)**
```bash
docker-compose up -d
```

**Вариант 2: Традиционен hosting**
```bash
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 app:app
```

Виж [DEPLOYMENT_IMPROVEMENTS.md](DEPLOYMENT_IMPROVEMENTS.md) за детайли.

### Q: Как да setup-нам HTTPS?
**A:** Използвай nginx като reverse proxy със SSL сертификат:
```bash
# С Let's Encrypt:
sudo certbot --nginx -d your-domain.com
```

Виж [DEPLOYMENT_IMPROVEMENTS.md](DEPLOYMENT_IMPROVEMENTS.md#3-nginx-configuration).

### Q: Как да мониторирам приложението?
**A:** Използвай Prometheus + Grafana:
```bash
docker-compose up prometheus grafana
# Отвори http://localhost:3000
```

---

## 📊 Performance въпроси

### Q: Приложението е бавно, какво да направя?
**A:** Провери:
1. **Кешът активиран ли е?** → `cache_duration: 3600`
2. **Database индекси добавени ли са?** → Виж [PERFORMANCE_IMPROVEMENTS.md](PERFORMANCE_IMPROVEMENTS.md#4-database-indexing)
3. **HTTP compression включен ли е?** → `pip install flask-compress`
4. **Използваш ли Gunicorn?** → По-бърз от Flask dev сървър

### Q: API заявките отнемат много време
**A:** 
1. Използвай async API calls → Виж [PERFORMANCE_IMPROVEMENTS.md](PERFORMANCE_IMPROVEMENTS.md#3-async-api-calls)
2. Активирай кеширане
3. Използвай Redis вместо file-based кеш

### Q: База данни заявките са бавни
**A:**
```sql
-- Добави индекси:
ALTER TABLE matches ADD INDEX idx_match_date (match_date);
ALTER TABLE predictions ADD INDEX idx_match_id (match_id);
```

---

## 🔒 Security въпроси

### Q: Сигурно ли е приложението?
**A:** Текущо има критични проблеми:
- ❌ SQL Injection уязвимост
- ❌ Липсва Rate Limiting
- ❌ Липсва CORS защита

**Приложи критичните поправки от [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) СЕГА!**

### Q: Как да защитя API ключа?
**A:** 
1. Никога не го commit-вай в Git
2. Използвай `.env` файл (вече в `.gitignore`)
3. За production използвай environment variables или key vault

### Q: Как да добавя authentication?
**A:** Използвай Flask-Login или JWT:
```bash
pip install flask-login
# Или
pip install flask-jwt-extended
```

---

## 🧪 Testing въпроси

### Q: Как да пусна тестовете?
**A:**
```bash
# Инсталирай pytest
pip install pytest pytest-cov

# Пусни всички тестове
pytest tests/ -v

# С coverage
pytest tests/ --cov=. --cov-report=html
```

### Q: Липсват ми тестове?
**A:** Копирай готовите тестове от директория [tests/](tests/):
- `test_predictor.py` - 13 теста
- `test_database.py` - 6 теста
- `test_api.py` - 12 теста

### Q: Как да мокна API заявките в тестовете?
**A:** Използвай `unittest.mock`:
```python
from unittest.mock import patch, Mock

@patch('predictor.requests.Session.get')
def test_api_call(mock_get):
    mock_get.return_value.json.return_value = {'response': []}
    # ... test code
```

---

## 🎨 UI/UX въпроси

### Q: Как да променя цветовете?
**A:** В `styles.css` или `static/styles.css`:
```css
:root {
    --primary-color: #667eea;  /* Промени тук */
    --secondary-color: #764ba2;
}
```

### Q: Как да добавя нови филтри?
**A:** 
1. Добави в `index.html`:
```html
<select id="newFilter">
    <option value="all">Всички</option>
</select>
```

2. Добави логика в `script.js`:
```javascript
function applyFilters() {
    const newFilter = document.getElementById('newFilter').value;
    // ... filter logic
}
```

### Q: Темният режим не работи
**A:** Провери:
1. JavaScript файлът се зарежда ли? (Виж browser console)
2. localStorage работи ли? (Може да е блокиран)
3. CSS файлът се зарежда ли?

---

## 💾 Database въпроси

### Q: Как да backup-нам базата данни?
**A:**
```bash
# Export
mysqldump -u root -p football_predictor > backup.sql

# Import
mysql -u root -p football_predictor < backup.sql
```

### Q: Как да изчистя старите данни?
**A:**
```sql
-- Изтрий прогнози по-стари от 30 дни
DELETE FROM predictions WHERE created_at < DATE_SUB(NOW(), INTERVAL 30 DAY);

-- Изтрий мачове по-стари от 90 дни
DELETE FROM matches WHERE match_date < DATE_SUB(NOW(), INTERVAL 90 DAY);
```

### Q: Базата данни стана твърде голяма
**A:**
1. Изтрий стари данни (виж по-горе)
2. Optimize таблиците:
```sql
OPTIMIZE TABLE predictions;
OPTIMIZE TABLE matches;
```

---

## 🔄 Update въпроси

### Q: Как да update-нам зависимостите?
**A:**
```bash
# Виж outdated пакети
pip list --outdated

# Update всички
pip install --upgrade -r requirements.txt

# Или конкретен пакет
pip install --upgrade flask
```

### Q: Има ли нова версия на проекта?
**A:** Провери:
```bash
git fetch origin
git log HEAD..origin/main --oneline
```

### Q: Как да мигрирам към нова версия?
**A:**
1. Backup база данни
2. `git pull origin main`
3. `pip install -r requirements.txt`
4. Провери миграции в `DATABASE_SETUP.md`
5. Рестартирай приложението

---

## 📞 Помощ и поддръжка

### Q: Къде да докладвам bug?
**A:** Създай issue в GitHub repository-то с:
- Описание на проблема
- Стъпки за възпроизвеждане
- Error logs от `logs/app.log`
- Environment (OS, Python версия)

### Q: Къде мога да получа помощ?
**A:** 
1. Провери документацията:
   - [PROJECT_REVIEW.md](PROJECT_REVIEW.md)
   - [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md)
   - Специфичните документи за подобрения

2. Провери логовете:
   - `logs/app.log`
   - Browser console (F12)

3. Провери GitHub issues

### Q: Как да допринеса към проекта?
**A:**
1. Fork проекта
2. Създай feature branch
3. Напиши тестове за новата функционалност
4. Submit pull request

---

## 🎓 Learning Resources

### Q: Как работи ELO рейтинг системата?
**A:** ELO е математически модел за изчисляване на относителна сила. Виж:
- [Wikipedia - Elo rating](https://en.wikipedia.org/wiki/Elo_rating_system)
- [predictor.py](predictor.py) - Имплементацията

### Q: Къде мога да науча повече за Flask?
**A:**
- [Official Flask Documentation](https://flask.palletsprojects.com/)
- [Flask Mega-Tutorial](https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world)

### Q: Как да подобря прогнозите?
**A:** 
1. Добави повече фактори (injuries, weather, H2H history)
2. Използвай machine learning (scikit-learn, TensorFlow)
3. Fine-tune параметрите (ELO K-factor, weights)
4. Анализирай историческата точност и коригирай

---

**Нямаш отговор на въпроса си? Провери документацията или създай GitHub issue.**
