/**
 * Smart Football Predictor - JavaScript
 * Управление на филтри, кеш, темен режим и експортиране
 */

// Глобално състояние
let allPredictions = [];
const CACHE_EXPIRY = 60 * 60 * 1000; // 1 час
const STORAGE_KEY = 'football_predictor_';

// ==================== Управление на тема ====================

function initTheme() {
    const savedTheme = localStorage.getItem(STORAGE_KEY + 'theme') || 'light';
    if (savedTheme === 'dark') {
        document.body.classList.add('dark-mode');
        updateThemeToggle();
    }
}

function toggleTheme() {
    document.body.classList.toggle('dark-mode');
    const theme = document.body.classList.contains('dark-mode') ? 'dark' : 'light';
    localStorage.setItem(STORAGE_KEY + 'theme', theme);
    updateThemeToggle();
}

function updateThemeToggle() {
    const btn = document.getElementById('themeToggle');
    const isDark = document.body.classList.contains('dark-mode');
    btn.textContent = isDark ? '☀️ Светъл' : '🌙 Тъмен';
}

// ==================== Управление на филтрите ====================

function saveFilters() {
    const filters = {
        confidence: document.getElementById('confidenceFilter').value,
        prediction: document.getElementById('predictionFilter').value,
        goals: document.getElementById('goalsFilter').value
    };
    localStorage.setItem(STORAGE_KEY + 'filters', JSON.stringify(filters));
}

function loadFilters() {
    const saved = localStorage.getItem(STORAGE_KEY + 'filters');
    if (saved) {
        const filters = JSON.parse(saved);
        document.getElementById('confidenceFilter').value = filters.confidence || 'all';
        document.getElementById('predictionFilter').value = filters.prediction || 'all';
        document.getElementById('goalsFilter').value = filters.goals || 'all';
    }
}

// ==================== Управление на кеша ====================

function getCachedPredictions() {
    const cached = localStorage.getItem(STORAGE_KEY + 'predictions');
    if (!cached) return null;
    
    const data = JSON.parse(cached);
    const now = Date.now();
    
    if (now - data.timestamp > CACHE_EXPIRY) {
        localStorage.removeItem(STORAGE_KEY + 'predictions');
        return null;
    }
    
    return data.predictions;
}

function setCachedPredictions(predictions) {
    const data = {
        predictions: predictions,
        timestamp: Date.now()
    };
    localStorage.setItem(STORAGE_KEY + 'predictions', JSON.stringify(data));
}

// ==================== Зареждане на прогнози ====================

async function loadPredictions() {
    try {
        // Зареждане на прогнози
        document.getElementById('loading').style.display = 'block';
        document.getElementById('error').style.display = 'none';
        
        const response = await fetch('/api/predictions');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        
        if (!data.success) {
            throw new Error(data.error || 'Грешка при зареждане');
        }
        
        allPredictions = data.predictions;
        setCachedPredictions(allPredictions);
        updateStats();
        displayPredictions();
        
        document.getElementById('loading').style.display = 'none';
        
    } catch (error) {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('error').style.display = 'block';
        document.getElementById('error').textContent = '❌ ' + error.message;
        console.error('Error:', error);
    }
}

// ==================== Статистики ====================

function updateStats() {
    const total = allPredictions.length;
    const highConf = allPredictions.filter(p => p.prediction && p.prediction.confidence >= 60).length;
    const validPredictions = allPredictions.filter(p => p.prediction);
    const avgConf = validPredictions.length > 0 ? (validPredictions.reduce((sum, p) => sum + p.prediction.confidence, 0) / validPredictions.length) : 0;
    
    document.getElementById('totalMatches').textContent = total;
    document.getElementById('highConfidence').textContent = highConf;
    document.getElementById('avgConfidence').textContent = avgConf.toFixed(1) + '%';
}

// ==================== Показване на прогнози ====================

function displayPredictions() {
    const container = document.getElementById('predictions');
    const confidenceFilter = document.getElementById('confidenceFilter').value;
    const predictionFilter = document.getElementById('predictionFilter').value;
    const goalsFilter = document.getElementById('goalsFilter').value;
    
    let filtered = allPredictions.filter(p => {
        // Филтър увереност
        if (confidenceFilter === 'high' && (!p.prediction || p.prediction.confidence < 60)) return false;
        if (confidenceFilter === 'medium' && (!p.prediction || p.prediction.confidence < 45 || p.prediction.confidence >= 60)) return false;
        if (confidenceFilter === 'low' && (!p.prediction || p.prediction.confidence >= 45)) return false;
        
        // Филтър прогноза
        if (predictionFilter !== 'all' && (!p.prediction || p.prediction.bet !== predictionFilter)) return false;
        
        // Филтър голове
        if (goalsFilter === 'high' && p.over_25 < 60) return false;
        if (goalsFilter === 'low' && p.over_25 >= 60) return false;
        
        return true;
    });
    
    if (filtered.length === 0) {
        container.innerHTML = '<div class="loading">Няма мачове с избраните филтри</div>';
        return;
    }
    
    container.innerHTML = filtered.map(match => `
        <div class="match-card">
            <div class="match-header">
                <div>
                    <div class="match-time">🕐 ${match.time || 'N/A'}</div>
                    <div class="match-league">${match.league || 'N/A'}</div>
                </div>
            </div>
            
            <div class="teams">
                <div class="team-row">
                    <span class="team-name">🏠 ${match.home_team || 'Unknown'}</span>
                    <div class="form-badges">
                        ${(match.home_form || '').split('').slice(0, 5).map(r => 
                            `<span class="form-badge ${r}">${r}</span>`
                        ).join('')}
                    </div>
                    <span class="team-elo">⭐ ${match.home_elo || 'N/A'}</span>
                </div>
                
                <div class="team-row">
                    <span class="team-name">✈️ ${match.away_team || 'Unknown'}</span>
                    <div class="form-badges">
                        ${(match.away_form || '').split('').slice(0, 5).map(r => 
                            `<span class="form-badge ${r}">${r}</span>`
                        ).join('')}
                    </div>
                    <span class="team-elo">⭐ ${match.away_elo || 'N/A'}</span>
                </div>
            </div>
            
            <div class="probabilities">
                <div class="prob-item ${match.prediction && match.prediction.bet === '1' ? 'highlight' : ''}">
                    <div class="prob-label">Домакин</div>
                    <div class="prob-value">${match.probabilities ? match.probabilities['1'] || 0 : 0}%</div>
                </div>
                <div class="prob-item ${match.prediction && match.prediction.bet === 'X' ? 'highlight' : ''}">
                    <div class="prob-label">Равен</div>
                    <div class="prob-value">${match.probabilities ? match.probabilities['X'] || 0 : 0}%</div>
                </div>
                <div class="prob-item ${match.prediction && match.prediction.bet === '2' ? 'highlight' : ''}">
                    <div class="prob-label">Гост</div>
                    <div class="prob-value">${match.probabilities ? match.probabilities['2'] || 0 : 0}%</div>
                </div>
            </div>
            
            <div class="prediction-box">
                <div class="prediction-label">🎯 Препоръка</div>
                <div class="prediction-value">${match.prediction ? getBetLabel(match.prediction.bet) : 'Няма'}</div>
                <span class="confidence-badge">
                    ${match.prediction ? match.prediction.confidence + '%' : '0%'} увереност
                </span>
            </div>
            
            <div class="details">
                <div class="detail-row">
                    <span>⚽ Очаквани голове:</span>
                    <strong>${match.expected_goals || 'N/A'}</strong>
                </div>
                <div class="detail-row">
                    <span>📊 Over 2.5:</span>
                    <strong>${match.over_25 || 'N/A'}%</strong>
                </div>
                <div class="detail-row">
                    <span>� Очаквани картони:</span>
                    <strong>${match.expected_yellow_cards || 'N/A'}</strong>
                </div>
                <div class="detail-row">
                    <span>🚩 Очаквани корнери:</span>
                    <strong>${match.expected_corners || 'N/A'}</strong>
                </div>
                <div class="detail-row">
                    <span>📈 ${match.home_team}:</span>
                    <strong>${match.details ? match.details.home_goals_avg || 'N/A' : 'N/A'} гола/мач</strong>
                </div>
                <div class="detail-row">
                    <span>📈 ${match.away_team}:</span>
                    <strong>${match.details ? match.details.away_goals_avg || 'N/A' : 'N/A'} гола/мач</strong>
                </div>
                <div class="detail-row">
                    <span>🟨 ${match.home_team} (картони):</span>
                    <strong>${match.details ? match.details.home_yellow_cards_avg || 'N/A' : 'N/A'}/мач</strong>
                </div>
                <div class="detail-row">
                    <span>🟨 ${match.away_team} (картони):</span>
                    <strong>${match.details ? match.details.away_yellow_cards_avg || 'N/A' : 'N/A'}/мач</strong>
                </div>
                <div class="detail-row">
                    <span>🚩 ${match.home_team} (корнери):</span>
                    <strong>${match.details ? match.details.home_corners_avg || 'N/A' : 'N/A'}/мач</strong>
                </div>
                <div class="detail-row">
                    <span>🚩 ${match.away_team} (корнери):</span>
                    <strong>${match.details ? match.details.away_corners_avg || 'N/A' : 'N/A'}/мач</strong>
                </div>
            </div>
        </div>
    `).join('');
}

function getBetLabel(bet) {
    const labels = {
        '1': '1 (Домакин)',
        'X': 'X (Равен)',
        '2': '2 (Гост)'
    };
    return labels[bet] || bet;
}

// ==================== Експортиране ====================

async function exportToCSV() {
    try {
        const response = await fetch('/api/export/csv');
        if (!response.ok) throw new Error('Грешка при експортиране');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `predictions_${new Date().toISOString().split('T')[0]}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showMessage('✅ Прогнозите са експортирани успешно', 'success');
    } catch (error) {
        showMessage('❌ Грешка при експортиране: ' + error.message, 'error');
    }
}

// ==================== Допълнителни функции ====================

function refreshPredictions() {
    localStorage.removeItem(STORAGE_KEY + 'predictions');
    loadPredictions();
}

function showCacheInfo() {
    const cached = localStorage.getItem(STORAGE_KEY + 'predictions');
    if (cached) {
        const data = JSON.parse(cached);
        const age = Math.round((Date.now() - data.timestamp) / 1000 / 60);
        console.log(`Кеш възраст: ${age} минути`);
    }
}

function showMessage(text, type = 'info') {
    const msg = document.createElement('div');
    msg.className = type === 'error' ? 'error' : type === 'success' ? 'success-message' : 'loading';
    msg.textContent = text;
    msg.style.position = 'fixed';
    msg.style.top = '20px';
    msg.style.right = '20px';
    msg.style.zIndex = '9999';
    msg.style.minWidth = '300px';
    document.body.appendChild(msg);
    
    setTimeout(() => msg.remove(), 3000);
}

// ==================== Инициализация ====================

document.addEventListener('DOMContentLoaded', function() {
    // Инициализация на тема
    initTheme();
    
    // Зареждане на филтри
    loadFilters();
    
    // Event listeners
    document.getElementById('themeToggle').addEventListener('click', toggleTheme);
    document.getElementById('confidenceFilter').addEventListener('change', () => {
        saveFilters();
        displayPredictions();
    });
    document.getElementById('predictionFilter').addEventListener('change', () => {
        saveFilters();
        displayPredictions();
    });
    document.getElementById('goalsFilter').addEventListener('change', () => {
        saveFilters();
        displayPredictions();
    });
    
    document.getElementById('refreshBtn').addEventListener('click', refreshPredictions);
    document.getElementById('exportBtn').addEventListener('click', exportToCSV);
    
    // Зареждане на прогнози
    loadPredictions();
});
