-- 🎯 Smart Football Predictor Database Schema
-- База данни за събиране и анализ на статистика на отбори

CREATE DATABASE IF NOT EXISTS football_predictor;
USE football_predictor;

-- ========================================
-- 1. ТАБЛИЦА НА ОТБОРИТЕ
-- ========================================
CREATE TABLE IF NOT EXISTS teams (
    team_id INT PRIMARY KEY AUTO_INCREMENT,
    api_id INT UNIQUE NOT NULL COMMENT 'ID от API',
    name VARCHAR(100) NOT NULL,
    league VARCHAR(50) NOT NULL,
    country VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_league (league)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- 2. ТАБЛИЦА НА МАЧОВЕТЕ
-- ========================================
CREATE TABLE IF NOT EXISTS matches (
    match_id INT PRIMARY KEY AUTO_INCREMENT,
    api_id INT UNIQUE NOT NULL COMMENT 'ID от API',
    home_team_id INT NOT NULL,
    away_team_id INT NOT NULL,
    home_goals INT,
    away_goals INT,
    match_date DATETIME NOT NULL,
    league VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending' COMMENT 'pending, live, finished, postponed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (home_team_id) REFERENCES teams(team_id),
    FOREIGN KEY (away_team_id) REFERENCES teams(team_id),
    INDEX idx_date (match_date),
    INDEX idx_status (status),
    INDEX idx_league (league)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- 3. ТАБЛИЦА НА СТАТИСТИКАТА НА ОТБОРИТЕ (ПОСЛЕДНИ 5 МАЧА)
-- ========================================
CREATE TABLE IF NOT EXISTS team_statistics (
    stat_id INT PRIMARY KEY AUTO_INCREMENT,
    team_id INT NOT NULL,
    match_id INT NOT NULL,
    
    -- Резултат
    goals_for INT,
    goals_against INT,
    result CHAR(1) COMMENT 'W=победа, D=равенство, L=поражение',
    
    -- Статистика от мача
    shots INT,
    shots_on_target INT,
    possession DECIMAL(5,2),
    passes INT,
    accuracy DECIMAL(5,2),
    fouls INT,
    yellow_cards INT,
    red_cards INT,
    
    -- xG (очаквани голове)
    expected_goals DECIMAL(5,2),
    expected_goals_against DECIMAL(5,2),
    
    -- Дата на мача
    match_date DATETIME,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (team_id) REFERENCES teams(team_id),
    FOREIGN KEY (match_id) REFERENCES matches(match_id),
    INDEX idx_team_date (team_id, match_date),
    INDEX idx_match (match_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- 4. ТАБЛИЦА НА ПРОГНОЗИТЕ
-- ========================================
CREATE TABLE IF NOT EXISTS predictions (
    prediction_id INT PRIMARY KEY AUTO_INCREMENT,
    match_id INT NOT NULL,
    home_team_id INT NOT NULL,
    away_team_id INT NOT NULL,
    
    -- ELO рейтинги
    home_elo DECIMAL(6,2),
    away_elo DECIMAL(6,2),
    elo_difference DECIMAL(6,2),
    
    -- Вероятности
    probability_home DECIMAL(5,2) COMMENT 'Вероятност победа на домакин',
    probability_draw DECIMAL(5,2) COMMENT 'Вероятност равенство',
    probability_away DECIMAL(5,2) COMMENT 'Вероятност победа на гост',
    
    -- Прогноза
    prediction_bet VARCHAR(10) COMMENT '1, X, 2',
    confidence INT COMMENT 'Увереност 0-100%',
    expected_goals DECIMAL(5,2),
    over_25_probability DECIMAL(5,2),
    expected_yellow_cards DECIMAL(5,2) COMMENT 'Очаквани жълти картони',
    expected_corners DECIMAL(5,2) COMMENT 'Очаквани корнери',
    
    -- Форма
    home_form VARCHAR(10) COMMENT 'Последни 5 мача - WDWDL',
    away_form VARCHAR(10),
    
    -- Средни статистики (последни 5 мача)
    home_avg_goals_for DECIMAL(5,2),
    home_avg_goals_against DECIMAL(5,2),
    away_avg_goals_for DECIMAL(5,2),
    away_avg_goals_against DECIMAL(5,2),
    
    -- Резултат (ако мачът е завършен)
    actual_result VARCHAR(10) COMMENT '1, X, 2',
    actual_goals_home INT,
    actual_goals_away INT,
    was_correct BOOLEAN,
    
    -- Дати
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    match_date DATETIME,
    
    FOREIGN KEY (match_id) REFERENCES matches(match_id),
    FOREIGN KEY (home_team_id) REFERENCES teams(team_id),
    FOREIGN KEY (away_team_id) REFERENCES teams(team_id),
    INDEX idx_match (match_id),
    INDEX idx_date (created_at),
    INDEX idx_confidence (confidence),
    INDEX idx_accuracy (was_correct)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- 5. ТАБЛИЦА НА ELO РЕЙТИНГИТЕ
-- ========================================
CREATE TABLE IF NOT EXISTS elo_history (
    elo_id INT PRIMARY KEY AUTO_INCREMENT,
    team_id INT NOT NULL,
    match_id INT NOT NULL,
    old_elo DECIMAL(6,2),
    new_elo DECIMAL(6,2),
    elo_change DECIMAL(6,2),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (team_id) REFERENCES teams(team_id),
    FOREIGN KEY (match_id) REFERENCES matches(match_id),
    INDEX idx_team (team_id),
    INDEX idx_date (recorded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- 6. ТАБЛИЦА НА ТОЧНОСТ НА ПРОГНОЗИТЕ (СТАТИСТИКА)
-- ========================================
CREATE TABLE IF NOT EXISTS prediction_accuracy (
    accuracy_id INT PRIMARY KEY AUTO_INCREMENT,
    total_predictions INT DEFAULT 0,
    correct_predictions INT DEFAULT 0,
    accuracy_rate DECIMAL(5,2),
    high_confidence_correct INT DEFAULT 0 COMMENT 'Коректни с 70%+ увереност',
    high_confidence_total INT DEFAULT 0,
    period_start DATE,
    period_end DATE,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_period (period_start, period_end)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- 7. ТАБЛИЦА НА HEAD-TO-HEAD СТАТИСТИКАТА
-- ========================================
CREATE TABLE IF NOT EXISTS h2h_statistics (
    h2h_id INT PRIMARY KEY AUTO_INCREMENT,
    team_a_id INT NOT NULL,
    team_b_id INT NOT NULL,
    total_matches INT DEFAULT 0,
    team_a_wins INT DEFAULT 0,
    draws INT DEFAULT 0,
    team_b_wins INT DEFAULT 0,
    team_a_goals_for INT DEFAULT 0,
    team_a_goals_against INT DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (team_a_id) REFERENCES teams(team_id),
    FOREIGN KEY (team_b_id) REFERENCES teams(team_id),
    UNIQUE KEY unique_h2h (team_a_id, team_b_id),
    INDEX idx_teams (team_a_id, team_b_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- ПРИМЕРНИ ИНДЕКСИ ЗА БЪРЗИ ЗАПИТВАНИЯ
-- ========================================
CREATE INDEX idx_team_stats_last_5 ON team_statistics(team_id, match_date DESC);
CREATE INDEX idx_predictions_accuracy ON predictions(was_correct, confidence);
CREATE INDEX idx_matches_league_date ON matches(league, match_date DESC);
