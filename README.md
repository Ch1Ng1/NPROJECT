# ⚽ Smart Football Predictor v2.0

Интелигентен прогнозатор за футболни мачове с поддръжка на кеширане и експортиране

---

## 📋 ВАЖНО: Преглед и подобрения на проекта

**🎯 Направен е пълен анализ на проекта!**

### 📊 Резултати:
- ✅ **Общ рейтинг:** 7/10
- ✅ **Критични проблеми:** 3 (отстранени)
- 📝 **Създадени:** 10+ документа с подобрения
- 🧪 **Готови тестове:** 31 unit/integration теста

### 🚀 Бърз старт:
1. **[ANALYSIS_SUMMARY.md](ANALYSIS_SUMMARY.md)** - Кратко резюме на анализа
2. **[PROJECT_REVIEW.md](PROJECT_REVIEW.md)** - Пълен преглед (⭐ ГЛАВЕН ДОКУМЕНТ)
3. **[QUICK_START_GUIDE.md](QUICK_START_GUIDE.md)** - Критични поправки за 1 час

### 📚 Детайлни подобрения:
- 🔒 [SECURITY_IMPROVEMENTS.md](SECURITY_IMPROVEMENTS.md) - Сигурност
- ⚡ [PERFORMANCE_IMPROVEMENTS.md](PERFORMANCE_IMPROVEMENTS.md) - Производителност
- 🎨 [UI_UX_IMPROVEMENTS.md](UI_UX_IMPROVEMENTS.md) - Потребителски опит
- 📝 [CODE_QUALITY_IMPROVEMENTS.md](CODE_QUALITY_IMPROVEMENTS.md) - Качество на код
- 🚀 [DEPLOYMENT_IMPROVEMENTS.md](DEPLOYMENT_IMPROVEMENTS.md) - Deployment & DevOps
- 🧪 [tests/](tests/) - Unit и Integration тестове

---

## ✨ Нови функции (v2.0)

✅ **Кеширане** - Кеш на прогнозите за 1 час (намалява API заявките)  
✅ **Темен режим** - Поддържа светъл и тъмен режим  
✅ **Запазване на филтри** - Филтрите се запазват в localStorage  
✅ **CSV експортиране** - Експортирай прогнозите като CSV  
✅ **Подобрена обработка на грешки** - Детайлни логове в logs/app.log  
✅ **Type hints** - Всички функции имат Python type annotations  
✅ **Docstrings** - Пълна документация на методите  
✅ **Retry логика** - Автоматични повторни опити при API грешки  

## 🎯 Методология

1. **ELO Рейтинг** - Математически модел за сила на отборите
2. **Форма** - Последни 5 резултата (W/D/L)
3. **Статистики** - Средни голове, защита
4. **Комбинирани Алгоритми** - Интегрирана прогноза с увереност

## 🚀 Основни функции

- ✅ Анализ на максимум 20 мача дневно
- ✅ Вероятности за 1/X/2 с процент увереност
- ✅ Прогноза за Over 2.5
- ✅ ELO рейтинги и форма визуализация
- ✅ Интелигентни филтри по увереност и тип
- ✅ CSV експортиране
- ✅ Темен режим и отзивчив дизайн
- ✅ Кеширане на резултатите

## 📦 Инсталация

```bash
pip install -r requirements.txt
```

Конфигуриране на API ключ в .env:
```
API_FOOTBALL_KEY=твоят_ключ_от_api-sports.io
FLASK_ENV=development
FLASK_DEBUG=True
HOST=0.0.0.0
PORT=5000
CACHE_DURATION=1
```

## 🌐 Стартиране

```bash
python app.py
```

Отвори: `http://localhost:5000`

## 📄 GitHub Pages (Railway + fallback demo)

Проектът вече има автоматичен deployment към GitHub Pages чрез workflow:

- `.github/workflows/deploy-pages.yml`
- `scripts/build_pages.py`

Как работи:

1. При push към `main` се генерира папка `pages/`
2. В `pages/` се публикуват:
  - статична версия на UI (`index.html`, `404.html`, `styles.css`, `script.js`)
  - demo данни от `cache/predictions_cache.json` → `pages/data/predictions.json`
3. GitHub Actions публикува съдържанието в GitHub Pages

Важно:

- GitHub Pages е **само статичен хостинг**
- За live данни използвай външен backend (напр. Railway)
- Ако няма конфигуриран backend, Pages автоматично ползва `data/predictions.json`

### Railway backend за Pages

1. Deploy-ни Flask приложението в Railway
2. Копирай публичния URL (пример: `https://nproject-production.up.railway.app`)
3. В GitHub repo: `Settings` → `Secrets and variables` → `Actions`
4. Създай secret: `PAGES_API_BASE_URL` със стойност Railway URL
5. Push към `main` (или rerun на workflow)

След това GitHub Pages ще вика:

- `https://...railway.app/api/predictions`
- `https://...railway.app/api/export/csv`

Активиране в GitHub:

1. Repo `Settings` → `Pages`
2. Source: `GitHub Actions`
3. Push към `main` (или стартирай workflow ръчно от `Actions`)

## 🔗 API Endpoints

| Endpoint | Описание |
|----------|----------|
| `/` | Главна страница |
| `/api/predictions` | Всички прогнози за днес (със кеширане) |
| `/api/stats` | Статистики на системата |
| `/api/high-confidence` | Само прогнози със висока увереност (≥60%) |
| `/api/export/csv` | Експортирай прогнози като CSV |
| `/api/refresh` | Обновяване на кеша |

## 🎨 UI/UX Функции

- **Темен режим** 🌙 - Кликни за тъмен режим
- **Филтриране** 🎯 - По увереност, тип и голове
- **Експортиране** 📥 - Сваляне на CSV
- **Обновяване** 🔄 - Пречисти кеша
- **Отзивчив дизайн** 📱 - Перфектно на мобилни

## 📝 Логване

Логовете се запазват в `logs/app.log`. Проверете за детайли при грешки.

## 🔧 Структура

```
.
├── app.py           # Flask сървър с кеширане
├── predictor.py     # Основна логика на прогнозирането  
├── utils.py         # CSV експортиране и филтриране
├── requirements.txt # Зависимости (flask, requests, python-dotenv)
├── .env.example     # Пример на конфигурация
├── README.md        # Този файл
└── templates/
    ├── index.html        # Главна страница (HTML)
    ├── styles.css        # Стилове (светъл/тъмен режим)
    └── script.js         # JavaScript (темен режим, филтри, кеш, експорт)
```

## 📊 Алгоритми

**ELO формула:**
```
Expected_Home = 1 / (1 + 10^(-(ELO_Home - ELO_Away)/400))
Expected_Away = 1 - Expected_Home
```

**Форма оценка:**
```
W=3, D=1, L=0
Средна на последните 5 мача (0-3)
```

**Комбинирана вероятност:**
```
Final_Home = min(95, max(5, ELO_prob + форма_фактор))
Нормализирана между 5-95%
```

## 🛠️ Технологии

- **Backend:** Flask, Python 3.8+, requests
- **Frontend:** HTML5, CSS3, JavaScript (vanilla)
- **API:** api-sports.io за футболни данни
- **Кеширане:** In-memory кеш с localStorage

## 🔐 Безопасност

- API ключът се зарежда от `.env` файла (не се комитва)
- Валидация на всички входни данни
- Обработка на грешки на всички нива

## 📖 Използване

1. Отвори `http://localhost:5000`
2. Избери филтри (увереност, тип прогноза, голове)
3. Кликни 🔄 за обновяване на прогнозите
4. Кликни 📥 за експортиране като CSV
5. Включи темен режим с 🌙
6. Филтрите се запазват автоматично

## 🎯 Примерна прогноза

```json
{
  "time": "19:00",
  "league": "Premier League",
  "home_team": "Manchester City",
  "away_team": "Chelsea",
  "probabilities": {
    "1": 65.5,      // Домакин
    "X": 22.3,      // Равен
    "2": 12.2       // Гост
  },
  "prediction": {
    "bet": "1",
    "confidence": 65.5,
    "level": "Висока"
  },
  "over_25": 68.5,
  "expected_goals": 2.8
}
```

## 🐛 Обработка на грешки

- API грешки -> Автоматични повторни опити
- Липса API ключ -> Информативна грешка
- Мрежови проблеми -> Graceful fallback
- Всички грешки се логват

## 📧 Контакт

За въпроси или предложения свържи се с разработчика.

## 📝 Лицензия

Лично използване

---

**Версия:** 2.0  
**Последна актуализация:** Януари 2026
