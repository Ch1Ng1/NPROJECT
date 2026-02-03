# 🎨 UI/UX Подобрения

## Предложения за по-добро потребителско изживяване:

### 1. **Loading States**

#### Проблем:
- Само един общ loading индикатор
- Няма скелетон екрани

#### Решение:
```html
<!-- Skeleton loader за всяка карта -->
<div class="skeleton-card">
    <div class="skeleton-header"></div>
    <div class="skeleton-teams">
        <div class="skeleton-line"></div>
        <div class="skeleton-line"></div>
    </div>
    <div class="skeleton-prediction"></div>
</div>

<style>
.skeleton-card {
    background: #fff;
    border-radius: 12px;
    padding: 20px;
    animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

.skeleton-line {
    height: 20px;
    background: #e0e0e0;
    border-radius: 4px;
    margin: 10px 0;
}
</style>
```

---

### 2. **Error Handling UI**

#### Проблем:
- Грешките са само в console
- Потребителят не вижда ясни съобщения

#### Решение:
```javascript
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-icon">${getIcon(type)}</span>
            <p>${message}</p>
            <button class="notification-close">&times;</button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 100);
    
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

function getIcon(type) {
    const icons = {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️'
    };
    return icons[type] || icons.info;
}
```

```css
.notification {
    position: fixed;
    top: 20px;
    right: -400px;
    background: white;
    padding: 15px 20px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    transition: right 0.3s ease;
    z-index: 10000;
    min-width: 300px;
}

.notification.show {
    right: 20px;
}

.notification-success {
    border-left: 4px solid #4caf50;
}

.notification-error {
    border-left: 4px solid #f44336;
}
```

---

### 3. **Progressive Web App (PWA)**

#### Решение:
```javascript
// service-worker.js
const CACHE_NAME = 'football-predictor-v1';
const urlsToCache = [
    '/',
    '/static/styles.css',
    '/static/script.js',
    '/static/logo.png'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => response || fetch(event.request))
    );
});
```

```json
// manifest.json
{
    "name": "Smart Football Predictor",
    "short_name": "FootballPro",
    "description": "Интелигентни прогнози за футболни мачове",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#667eea",
    "theme_color": "#667eea",
    "icons": [
        {
            "src": "/static/icon-192.png",
            "sizes": "192x192",
            "type": "image/png"
        },
        {
            "src": "/static/icon-512.png",
            "sizes": "512x512",
            "type": "image/png"
        }
    ]
}
```

---

### 4. **Accessibility (A11y)**

#### Проблем:
- Липсват ARIA labels
- Лоша поддръжка на клавиатурна навигация
- Недостатъчен контраст в някои части

#### Решение:
```html
<!-- Добави ARIA labels -->
<button 
    id="themeToggle" 
    aria-label="Превключи тема"
    aria-pressed="false"
>
    🌙 Тъмен
</button>

<select 
    id="confidenceFilter" 
    aria-label="Филтър по увереност"
>
    <option value="all">Всички</option>
</select>

<!-- Keyboard navigation -->
<div 
    class="match-card" 
    tabindex="0"
    role="article"
    aria-label="Мач между Team A и Team B"
>
    ...
</div>
```

```css
/* Focus styles */
*:focus {
    outline: 2px solid #667eea;
    outline-offset: 2px;
}

/* Skip to main content */
.skip-link {
    position: absolute;
    top: -40px;
    left: 0;
    background: #667eea;
    color: white;
    padding: 8px;
    text-decoration: none;
}

.skip-link:focus {
    top: 0;
}
```

---

### 5. **Search & Sort**

#### Решение:
```html
<div class="search-sort">
    <input 
        type="text" 
        id="searchInput" 
        placeholder="🔍 Търси отбор..."
        aria-label="Търси отбор"
    />
    
    <select id="sortBy" aria-label="Сортирай по">
        <option value="confidence">Увереност</option>
        <option value="time">Време</option>
        <option value="league">Лига</option>
    </select>
</div>
```

```javascript
function filterAndSort() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const sortBy = document.getElementById('sortBy').value;
    
    let filtered = allPredictions.filter(match => {
        const homeTeam = match.home_team.toLowerCase();
        const awayTeam = match.away_team.toLowerCase();
        return homeTeam.includes(searchTerm) || awayTeam.includes(searchTerm);
    });
    
    filtered.sort((a, b) => {
        switch(sortBy) {
            case 'confidence':
                return b.prediction.confidence - a.prediction.confidence;
            case 'time':
                return a.time.localeCompare(b.time);
            case 'league':
                return a.league.localeCompare(b.league);
            default:
                return 0;
        }
    });
    
    displayMatches(filtered);
}
```

---

### 6. **Match Details Modal**

#### Решение:
```html
<div id="matchModal" class="modal" role="dialog" aria-hidden="true">
    <div class="modal-content">
        <button class="modal-close" aria-label="Затвори">&times;</button>
        
        <div class="modal-header">
            <h2 id="modalTitle"></h2>
        </div>
        
        <div class="modal-body">
            <!-- Детайлна статистика -->
            <div class="stat-comparison">
                <div class="stat-item">
                    <span>ELO Рейтинг</span>
                    <div class="progress-bar">
                        <div class="progress home" style="width: 55%">1650</div>
                        <div class="progress away" style="width: 45%">1450</div>
                    </div>
                </div>
                
                <div class="stat-item">
                    <span>Форма</span>
                    <div class="form-display">
                        <span class="home-form">WWDWL</span>
                        <span class="away-form">LWLDD</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
```

```css
.modal {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0,0,0,0.7);
    z-index: 9999;
}

.modal.show {
    display: flex;
    align-items: center;
    justify-content: center;
}

.modal-content {
    background: white;
    border-radius: 16px;
    max-width: 800px;
    width: 90%;
    max-height: 90vh;
    overflow-y: auto;
    animation: slideUp 0.3s ease;
}

@keyframes slideUp {
    from {
        transform: translateY(50px);
        opacity: 0;
    }
    to {
        transform: translateY(0);
        opacity: 1;
    }
}
```

---

### 7. **Responsive Design Improvements**

#### Проблем:
- Не е напълно оптимизиран за мобилни

#### Решение:
```css
/* Mobile optimizations */
@media (max-width: 768px) {
    .predictions-grid {
        grid-template-columns: 1fr;
    }
    
    .filters {
        flex-direction: column;
        align-items: stretch;
    }
    
    .filter-item {
        width: 100%;
    }
    
    .stats-bar {
        flex-direction: column;
    }
    
    header h1 {
        font-size: 1.8em;
    }
    
    .match-card {
        padding: 15px;
    }
}

/* Touch-friendly buttons */
.action-button {
    min-height: 44px;
    min-width: 44px;
}
```

---

### 8. **Data Visualization**

#### Решение:
```html
<!-- Използвай Chart.js за визуализация -->
<canvas id="accuracyChart"></canvas>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
const ctx = document.getElementById('accuracyChart').getContext('2d');
const chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: ['1 ден', '7 дни', '30 дни'],
        datasets: [{
            label: 'Точност на прогнозите',
            data: [75, 68, 71],
            borderColor: '#667eea',
            backgroundColor: 'rgba(102, 126, 234, 0.1)',
            tension: 0.4
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {
                display: true,
                position: 'top'
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                max: 100,
                ticks: {
                    callback: value => value + '%'
                }
            }
        }
    }
});
</script>
```

---

## Реализация:

```bash
# Добави Chart.js в requirements
echo "chart.js" >> frontend_dependencies.txt

# Генерирай PWA икони
# Използвай https://realfavicongenerator.net/
```
