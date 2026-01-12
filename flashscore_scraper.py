"""
FlashScore Web Scraper за коефициенти на мачове
Извлича betting odds от FlashScore.bg за футболни мачове
"""

import requests
from bs4 import BeautifulSoup
import time
import re
from typing import Optional, Dict, List
from datetime import datetime


class FlashScoreScraper:
    """Scraper за извличане на коефициенти от FlashScore"""
    
    BASE_URL = "https://www.flashscore.bg"
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'bg-BG,bg;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    }
    
    def __init__(self, delay_between_requests: float = 2.0):
        """
        Инициализация на scraper
        
        Args:
            delay_between_requests: Забавяне между заявки (seconds) за избягване на rate limiting
        """
        self.delay = delay_between_requests
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
        self._last_request_time = 0
        
    def _rate_limit(self):
        """Прилага rate limiting между заявките"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self.delay:
            time.sleep(self.delay - time_since_last)
        self._last_request_time = time.time()
    
    def get_football_matches_today(self) -> Optional[str]:
        """
        Извлича HTML на днешните футболни мачове
        
        Returns:
            HTML съдържание или None при грешка
        """
        try:
            self._rate_limit()
            url = f"{self.BASE_URL}/football/"
            print(f"[FlashScore] Fetching: {url}")
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            print(f"[FlashScore] Response status: {response.status_code}")
            return response.text
            
        except requests.exceptions.RequestException as e:
            print(f"[FlashScore] Error fetching matches: {e}")
            return None
    
    def parse_odds_from_html(self, html: str, home_team: str, away_team: str) -> Optional[Dict[str, float]]:
        """
        Парсва HTML и извлича коефициенти за конкретен мач
        
        Args:
            html: HTML съдържание
            home_team: Име на домакина
            away_team: Име на госта
            
        Returns:
            Dict с home_odds, draw_odds, away_odds или None
        """
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # FlashScore използва динамично генериран HTML
            # Търсим елементи с класове като 'event__match', 'event__participant', etc.
            
            # Опит 1: Търсене по имена на отбори
            matches = soup.find_all('div', class_=re.compile(r'event__match'))
            
            for match_div in matches:
                # Проверяваме дали това е търсеният мач
                participants = match_div.find_all('div', class_=re.compile(r'event__participant'))
                
                if len(participants) >= 2:
                    home = participants[0].get_text(strip=True)
                    away = participants[1].get_text(strip=True)
                    
                    # Проверка дали имената съвпадат (частично или пълно)
                    if self._team_names_match(home, home_team) and self._team_names_match(away, away_team):
                        # Намерихме мача, сега търсим коефициентите
                        odds_divs = match_div.find_all('div', class_=re.compile(r'odds'))
                        
                        if len(odds_divs) >= 3:
                            try:
                                home_odds = float(odds_divs[0].get_text(strip=True))
                                draw_odds = float(odds_divs[1].get_text(strip=True))
                                away_odds = float(odds_divs[2].get_text(strip=True))
                                
                                print(f"[FlashScore] Found odds for {home_team} vs {away_team}: {home_odds}/{draw_odds}/{away_odds}")
                                
                                return {
                                    'home_odds': home_odds,
                                    'draw_odds': draw_odds,
                                    'away_odds': away_odds
                                }
                            except (ValueError, AttributeError) as e:
                                print(f"[FlashScore] Error parsing odds: {e}")
                                continue
            
            print(f"[FlashScore] No odds found for {home_team} vs {away_team}")
            return None
            
        except Exception as e:
            print(f"[FlashScore] Error parsing HTML: {e}")
            return None
    
    def _team_names_match(self, name1: str, name2: str) -> bool:
        """
        Проверява дали две имена на отбори съвпадат
        
        Args:
            name1: Първо име
            name2: Второ име
            
        Returns:
            True ако съвпадат
        """
        # Премахваме специални символи и правим lowercase за сравнение
        clean1 = re.sub(r'[^a-zA-Z0-9\s]', '', name1.lower()).strip()
        clean2 = re.sub(r'[^a-zA-Z0-9\s]', '', name2.lower()).strip()
        
        # Проверка за пълно съвпадение
        if clean1 == clean2:
            return True
        
        # Проверка за частично съвпадение (поне 60% от думите)
        words1 = set(clean1.split())
        words2 = set(clean2.split())
        
        if not words1 or not words2:
            return False
        
        common = words1.intersection(words2)
        match_ratio = len(common) / min(len(words1), len(words2))
        
        return match_ratio >= 0.6
    
    def get_match_odds(self, home_team: str, away_team: str) -> Optional[Dict[str, float]]:
        """
        Извлича коефициенти за конкретен мач
        
        Args:
            home_team: Име на домакина
            away_team: Име на госта
            
        Returns:
            Dict с odds или None
        """
        html = self.get_football_matches_today()
        if not html:
            return None
        
        return self.parse_odds_from_html(html, home_team, away_team)
    
    def get_multiple_matches_odds(self, matches: List[Dict]) -> Dict[str, Dict[str, float]]:
        """
        Извлича коефициенти за множество мачове
        
        Args:
            matches: List от dict-ове с 'home_team' и 'away_team'
            
        Returns:
            Dict с ключ "{home_team} vs {away_team}" и value odds dict
        """
        # Извличаме HTML веднъж за всички мачове
        html = self.get_football_matches_today()
        if not html:
            return {}
        
        results = {}
        
        for match in matches:
            home_team = match.get('home_team', '')
            away_team = match.get('away_team', '')
            
            if not home_team or not away_team:
                continue
            
            match_key = f"{home_team} vs {away_team}"
            odds = self.parse_odds_from_html(html, home_team, away_team)
            
            if odds:
                results[match_key] = odds
            
            # Малко забавяне между обработките
            time.sleep(0.1)
        
        print(f"[FlashScore] Retrieved odds for {len(results)}/{len(matches)} matches")
        return results


def test_scraper():
    """Тестова функция"""
    scraper = FlashScoreScraper()
    
    # Тест с примерни отбори
    print("\n=== Testing FlashScore Scraper ===\n")
    
    test_matches = [
        {'home_team': 'Manchester United', 'away_team': 'Liverpool'},
        {'home_team': 'Real Madrid', 'away_team': 'Barcelona'},
    ]
    
    odds = scraper.get_multiple_matches_odds(test_matches)
    
    print("\n=== Results ===")
    for match_key, match_odds in odds.items():
        print(f"{match_key}: {match_odds}")


if __name__ == "__main__":
    test_scraper()
