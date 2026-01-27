"""
🗄️ Database Module - Работа с MySQL база данни
Всички операции за съхранение и четене на данни от таблиците
"""
import mysql.connector
from mysql.connector import Error, pooling
from typing import List, Dict, Optional, Any, Tuple
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import re

load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Управление на MySQL базата данни с connection pooling"""
    
    def __init__(
        self,
        host: str = os.getenv('DB_HOST', 'localhost'),
        user: str = os.getenv('DB_USER', 'root'),
        password: str = os.getenv('DB_PASSWORD', ''),
        database: str = os.getenv('DB_NAME', 'football_predictor'),
        port: int = int(os.getenv('DB_PORT', 3306))
    ):
        """Инициализира връзката към базата с connection pooling"""
        self.config = {
            'host': host,
            'user': user,
            'password': password,
            'database': database,
            'port': port,
            'autocommit': True,
            'pool_size': 5,
            'pool_reset_session': True
        }
        
        self.connection = None
        try:
            self.connection = mysql.connector.connect(**self.config)
            if self.connection.is_connected():
                logger.info(f"✅ Свързано към {database}")
                # Увери се, че схемата е съвместима
                try:
                    self._ensure_schema()
                    logger.info("✅ Схемата е актуализирана")
                except Exception as e:
                    logger.warning(f"⚠️  Схемата не можа да бъде проверена/актуализирана: {e}")
        except Error as e:
            logger.error(f"❌ Грешка при свързване към базата: {e}")
            self.connection = None
    
    def close(self):
        """Затва връзката"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Връзка затворена")
    
    def _execute_query(self, query: str, params: tuple = None) -> Optional[Any]:
        """Изпълнява SELECT запитване"""
        if not self.connection:
            logger.error("Нямаме връзка към базата")
            return None
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except Error as e:
            logger.error(f"Грешка при запитване: {e}")
            return None
    
    def _insert_update_delete(self, query: str, params: tuple = None) -> bool:
        """Изпълнява INSERT/UPDATE/DELETE запитване"""
        if not self.connection:
            logger.error("Нямаме връзка към базата")
            return False
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            self.connection.commit()
            return True
        except Error as e:
            logger.error(f"Грешка при операция: {e}")
            self.connection.rollback()
            return False

    def _ensure_schema(self) -> None:
        """Проверява и коригира дължините на колони при нужда"""
        if not self.connection or not self.connection.is_connected():
            logger.error("❌ База данни не е свързана")
            return
        
        try:
            cursor = self.connection.cursor(dictionary=True)
            
            # Проверка на home_form и away_form размер
            cursor.execute("SHOW COLUMNS FROM predictions LIKE 'home_form'")
            home_col = cursor.fetchone()
            cursor.execute("SHOW COLUMNS FROM predictions LIKE 'away_form'")
            away_col = cursor.fetchone()
            
            def _varchar_len(col: dict) -> Optional[int]:
                if not col or 'Type' not in col:
                    return None
                match = re.match(r"varchar\((\d+)\)", col['Type'], re.IGNORECASE)
                if match:
                    try:
                        return int(match.group(1))
                    except ValueError:
                        return None
                return None

            home_len = _varchar_len(home_col)
            away_len = _varchar_len(away_col)

            if (home_len is not None and home_len < 100) or (away_len is not None and away_len < 100):
                alter_sql = (
                    "ALTER TABLE predictions "
                    "MODIFY home_form VARCHAR(100), "
                    "MODIFY away_form VARCHAR(100)"
                )
                cursor = self.connection.cursor()
                cursor.execute(alter_sql)
                self.connection.commit()
                cursor.close()
                logger.info("✅ Актуализирана дължина на колоните home_form/away_form до VARCHAR(100)")
            
            # Проверка за новите колони expected_yellow_cards и expected_corners
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute("SHOW COLUMNS FROM predictions LIKE 'expected_yellow_cards'")
            yellow_cards_col = cursor.fetchone()
            cursor.execute("SHOW COLUMNS FROM predictions LIKE 'expected_corners'")
            corners_col = cursor.fetchone()
            
            # Добавяне на новите колони ако липсват
            if not yellow_cards_col or not corners_col:
                alter_sql_parts = []
                if not yellow_cards_col:
                    alter_sql_parts.append("ADD COLUMN expected_yellow_cards DECIMAL(5,2) DEFAULT 1.8")
                if not corners_col:
                    alter_sql_parts.append("ADD COLUMN expected_corners DECIMAL(5,2) DEFAULT 4.2")
                
                if alter_sql_parts:
                    alter_sql = "ALTER TABLE predictions " + ", ".join(alter_sql_parts)
                    cursor = self.connection.cursor()
                    cursor.execute(alter_sql)
                    self.connection.commit()
                    cursor.close()
                    logger.info(f"✅ Добавени нови колони: {', '.join(alter_sql_parts)}")
            
            cursor.close()
        except Exception as e:
            logger.error(f"❌ Грешка при актуализация на схема: {e}")
    
    # ===== ОПЕРАЦИИ СЪС ОТБОРИТЕ =====
    
    def add_team(self, api_id: int, name: str, league: str, country: str = None) -> Optional[int]:
        """Добавя отбор в базата"""
        query = """
        INSERT INTO teams (api_id, name, league, country)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE name=VALUES(name), league=VALUES(league)
        """
        if self._insert_update_delete(query, (api_id, name, league, country)):
            # Върни team_id
            result = self._execute_query(
                "SELECT team_id FROM teams WHERE api_id = %s",
                (api_id,)
            )
            return result[0]['team_id'] if result else None
        return None
    
    def get_team_id(self, api_id: int) -> Optional[int]:
        """Получава team_id по api_id"""
        result = self._execute_query(
            "SELECT team_id FROM teams WHERE api_id = %s",
            (api_id,)
        )
        return result[0]['team_id'] if result else None
    
    def get_team(self, team_id: int) -> Optional[Dict]:
        """Получава информация за отбор"""
        result = self._execute_query(
            "SELECT * FROM teams WHERE team_id = %s",
            (team_id,)
        )
        return result[0] if result else None
    
    # ===== ОПЕРАЦИИ С МАЧОВЕ =====
    
    def add_match(
        self,
        api_id: int,
        home_team_id: int,
        away_team_id: int,
        match_date: datetime,
        league: str,
        home_goals: int = None,
        away_goals: int = None,
        status: str = 'pending'
    ) -> Optional[int]:
        """Добавя мач в базата"""
        query = """
        INSERT INTO matches (api_id, home_team_id, away_team_id, match_date, league, 
                           home_goals, away_goals, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE status=VALUES(status), home_goals=VALUES(home_goals), 
                                 away_goals=VALUES(away_goals)
        """
        if self._insert_update_delete(query, (
            api_id, home_team_id, away_team_id, match_date, league,
            home_goals, away_goals, status
        )):
            result = self._execute_query(
                "SELECT match_id FROM matches WHERE api_id = %s",
                (api_id,)
            )
            return result[0]['match_id'] if result else None
        return None
    
    def get_team_last_matches(self, team_id: int, limit: int = 5) -> List[Dict]:
        """Получава последните мачове на отбор"""
        query = """
        SELECT m.*, 
               t1.name as home_team_name, t2.name as away_team_name
        FROM matches m
        JOIN teams t1 ON m.home_team_id = t1.team_id
        JOIN teams t2 ON m.away_team_id = t2.team_id
        WHERE (m.home_team_id = %s OR m.away_team_id = %s)
        AND m.status IN ('finished', 'live')
        ORDER BY m.match_date DESC
        LIMIT %s
        """
        return self._execute_query(query, (team_id, team_id, limit)) or []
    
    # ===== ОПЕРАЦИИ СА СТАТИСТИКА НА ОТБОРИТЕ =====
    
    def add_team_stats(
        self,
        team_id: int,
        match_id: int,
        goals_for: int,
        goals_against: int,
        result: str,
        shots: int = None,
        shots_on_target: int = None,
        possession: float = None,
        passes: int = None,
        accuracy: float = None,
        fouls: int = None,
        yellow_cards: int = None,
        red_cards: int = None,
        expected_goals: float = None,
        expected_goals_against: float = None,
        match_date: datetime = None
    ) -> bool:
        """Добавя статистика на отбор за конкретен мач"""
        query = """
        INSERT INTO team_statistics 
        (team_id, match_id, goals_for, goals_against, result, shots, shots_on_target,
         possession, passes, accuracy, fouls, yellow_cards, red_cards, 
         expected_goals, expected_goals_against, match_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        return self._insert_update_delete(query, (
            team_id, match_id, goals_for, goals_against, result, shots, shots_on_target,
            possession, passes, accuracy, fouls, yellow_cards, red_cards,
            expected_goals, expected_goals_against, match_date
        ))
    
    def get_team_stats_last_5(self, team_id: int) -> List[Dict]:
        """Получава статистика на отбор за последните 5 мача"""
        query = """
        SELECT * FROM team_statistics
        WHERE team_id = %s
        ORDER BY match_date DESC
        LIMIT 5
        """
        return self._execute_query(query, (team_id,)) or []
    
    def calculate_team_averages(self, team_id: int, matches: int = 5) -> Dict[str, float]:
        """Изчислява средни статистики на отбор"""
        stats = self.get_team_stats_last_5(team_id)
        
        if not stats:
            return {
                'avg_goals_for': 0,
                'avg_goals_against': 0,
                'avg_shots': 0,
                'avg_possession': 0,
                'avg_xg': 0
            }
        
        avg_goals_for = sum(s['goals_for'] or 0 for s in stats) / len(stats)
        avg_goals_against = sum(s['goals_against'] or 0 for s in stats) / len(stats)
        avg_shots = sum(s['shots'] or 0 for s in stats) / len(stats)
        avg_possession = sum(s['possession'] or 0 for s in stats) / len(stats)
        avg_xg = sum(s['expected_goals'] or 0 for s in stats) / len(stats)
        
        return {
            'avg_goals_for': round(avg_goals_for, 2),
            'avg_goals_against': round(avg_goals_against, 2),
            'avg_shots': round(avg_shots, 2),
            'avg_possession': round(avg_possession, 2),
            'avg_xg': round(avg_xg, 2)
        }
    
    def get_team_form(self, team_id: int) -> str:
        """Получава форма на отбор (последните 5 мача) - WDWDL"""
        stats = self.get_team_stats_last_5(team_id)
        form = ''.join([s['result'] for s in stats])
        return form
    
    # ===== ОПЕРАЦИИ С ПРОГНОЗИ =====
    
    def save_prediction(
        self,
        match_id: int,
        home_team_id: int,
        away_team_id: int,
        home_elo: float,
        away_elo: float,
        probability_home: float,
        probability_draw: float,
        probability_away: float,
        prediction_bet: str,
        confidence: int,
        expected_goals: float,
        over_25_probability: float,
        expected_yellow_cards: float,
        expected_corners: float,
        home_form: str,
        away_form: str,
        home_avg_goals_for: float,
        home_avg_goals_against: float,
        away_avg_goals_for: float,
        away_avg_goals_against: float,
        match_date: datetime
    ) -> Optional[int]:
        """Запазва прогноза за мач със всички статистики"""
        query = """
        INSERT INTO predictions
        (match_id, home_team_id, away_team_id, home_elo, away_elo, 
         probability_home, probability_draw, probability_away,
         prediction_bet, confidence, expected_goals, over_25_probability,
         expected_yellow_cards, expected_corners,
         home_form, away_form, home_avg_goals_for, home_avg_goals_against,
         away_avg_goals_for, away_avg_goals_against, match_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s)
        """
        if self._insert_update_delete(query, (
            match_id, home_team_id, away_team_id, home_elo, away_elo,
            probability_home, probability_draw, probability_away,
            prediction_bet, confidence, expected_goals, over_25_probability,
            expected_yellow_cards, expected_corners,
            home_form, away_form, home_avg_goals_for, home_avg_goals_against,
            away_avg_goals_for, away_avg_goals_against, match_date
        )):
            result = self._execute_query(
                "SELECT prediction_id FROM predictions WHERE match_id = %s ORDER BY prediction_id DESC LIMIT 1",
                (match_id,)
            )
            return result[0]['prediction_id'] if result else None
        return None
    
    def update_prediction_result(
        self,
        prediction_id: int,
        actual_result: str,
        actual_goals_home: int,
        actual_goals_away: int,
        was_correct: bool
    ) -> bool:
        """Актуализира резултат на прогноза когато мачът е завършен"""
        query = """
        UPDATE predictions
        SET actual_result = %s, actual_goals_home = %s, actual_goals_away = %s, was_correct = %s
        WHERE prediction_id = %s
        """
        return self._insert_update_delete(query, (
            actual_result, actual_goals_home, actual_goals_away, was_correct, prediction_id
        ))
    
    def get_predictions_today(self) -> List[Dict]:
        """Получава всички прогнози за днес"""
        query = """
        SELECT p.*, 
               t1.name as home_team_name, t2.name as away_team_name
        FROM predictions p
        JOIN teams t1 ON p.home_team_id = t1.team_id
        JOIN teams t2 ON p.away_team_id = t2.team_id
        WHERE DATE(p.match_date) = CURDATE()
        ORDER BY p.match_date
        """
        return self._execute_query(query) or []
    
    def get_prediction_accuracy(self, days: int = 7) -> Dict[str, Any]:
        """Изчислява точност на прогнозите за последния период"""
        query = """
        SELECT 
            COUNT(*) as total_predictions,
            SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) as correct_predictions,
            ROUND(SUM(CASE WHEN was_correct = 1 THEN 1 ELSE 0 END) / COUNT(*) * 100, 2) as accuracy_rate,
            SUM(CASE WHEN was_correct = 1 AND confidence >= 70 THEN 1 ELSE 0 END) as high_confidence_correct,
            SUM(CASE WHEN confidence >= 70 THEN 1 ELSE 0 END) as high_confidence_total
        FROM predictions
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL %s DAY)
        AND was_correct IS NOT NULL
        """
        result = self._execute_query(query, (days,))
        return result[0] if result else None
    
    # ===== ОПЕРАЦИИ С ELO РЕЙТИНГИ =====
    
    def save_elo_change(
        self,
        team_id: int,
        match_id: int,
        old_elo: float,
        new_elo: float
    ) -> bool:
        """Запазва промяна на ELO рейтинг"""
        query = """
        INSERT INTO elo_history (team_id, match_id, old_elo, new_elo, elo_change)
        VALUES (%s, %s, %s, %s, %s)
        """
        elo_change = new_elo - old_elo
        return self._insert_update_delete(query, (team_id, match_id, old_elo, new_elo, elo_change))
    
    def get_team_elo_history(self, team_id: int, limit: int = 10) -> List[Dict]:
        """Получава история на ELO рейтинг на отбор"""
        query = """
        SELECT * FROM elo_history
        WHERE team_id = %s
        ORDER BY recorded_at DESC
        LIMIT %s
        """
        return self._execute_query(query, (team_id, limit)) or []
    
    # ===== ОПЕРАЦИИ С H2H СТАТИСТИКА =====
    
    def update_h2h_stats(
        self,
        team_a_id: int,
        team_b_id: int,
        team_a_goals: int,
        team_b_goals: int
    ) -> bool:
        """Актуализира head-to-head статистика"""
        # Намери или създай запис
        result = self._execute_query(
            "SELECT h2h_id FROM h2h_statistics WHERE team_a_id = %s AND team_b_id = %s",
            (team_a_id, team_b_id)
        )
        
        if result:
            # Актуализиране
            query = """
            UPDATE h2h_statistics
            SET total_matches = total_matches + 1,
                team_a_goals_for = team_a_goals_for + %s,
                team_a_goals_against = team_a_goals_against + %s
            WHERE team_a_id = %s AND team_b_id = %s
            """
            self._insert_update_delete(query, (team_a_goals, team_b_goals, team_a_id, team_b_id))
        else:
            # Въвеждане
            query = """
            INSERT INTO h2h_statistics (team_a_id, team_b_id, total_matches, 
                                       team_a_goals_for, team_a_goals_against)
            VALUES (%s, %s, 1, %s, %s)
            """
            self._insert_update_delete(query, (team_a_id, team_b_id, team_a_goals, team_b_goals))
        
        return True
    
    def get_h2h_stats(self, team_a_id: int, team_b_id: int) -> Optional[Dict]:
        """Получава H2H статистика между два отбора"""
        query = """
        SELECT * FROM h2h_statistics
        WHERE (team_a_id = %s AND team_b_id = %s)
        OR (team_a_id = %s AND team_b_id = %s)
        """
        result = self._execute_query(query, (team_a_id, team_b_id, team_b_id, team_a_id))
        return result[0] if result else None


# Глобална инстанция
db = None

def init_database():
    """Инициализира глобалния database manager"""
    global db
    db = DatabaseManager()
    return db

def get_database() -> DatabaseManager:
    """Връща глобалния database manager"""
    global db
    if db is None:
        db = init_database()
    return db
