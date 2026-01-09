"""
Модул за събиране на футболни мачове от API-football
Използва безплатно API за получаване на мачове за текущия ден
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict
import json
from bs4 import BeautifulSoup
import re


class MatchScraper:
    """Клас за събиране на информация за футболни мачове"""
    
    def __init__(self, api_key: str = None, use_livescore: bool = True):
        """
        Инициализация на scraper
        
        Args:
            api_key: API ključ за API-Football (опционален за demo режим)
            use_livescore: Използване на LiveScore за реални данни (True по подразбиране)
        """
        self.api_key = api_key
        self.use_livescore = use_livescore
        self.base_url = "https://v3.football.api-sports.io"
        self.headers = {
            'x-apisports-key': api_key if api_key else 'YOUR_API_KEY',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def get_today_matches(self) -> List[Dict]:
        """
        Получава всички мачове САМО за днес
        
        Returns:
            List[Dict]: Списък с мачове за днешната дата
        """
        # Ако е зададено да се използва LiveScore
        if self.use_livescore:
            try:
                matches = self._scrape_flashscore_matches()
                return self._filter_today_only(matches)
            except Exception as e:
                # Fallback to demo data
                return self._get_demo_matches()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        try:
            if not self.api_key or self.api_key == 'YOUR_API_KEY' or self.api_key == 'YOUR_API_FOOTBALL_KEY_HERE':
                print("[!] No API key configured - using DEMO data")
                print("    Get your free API key from: https://www.api-football.com/")
                return self._get_demo_matches()
            
            print(f"[API-Football] Fetching matches for {today}...")
            
            url = f"{self.base_url}/fixtures"
            params = {
                'date': today,
                'timezone': 'Europe/Sofia'
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('response'):
                    matches = self._parse_matches(data['response'])
                    filtered = self._filter_today_only(matches)
                    print(f"[API-Football] [OK] Found {len(filtered)} matches for today")
                    return filtered
                else:
                    print("[API-Football] No matches found for today")
                    return self._get_demo_matches()
            elif response.status_code == 403:
                print("[API-Football] [X] Invalid API key")
                return self._get_demo_matches()
            elif response.status_code == 429:
                print("[API-Football] [X] Rate limit exceeded")
                return self._get_demo_matches()
            else:
                print(f"[API-Football] [X] Error {response.status_code}")
                return self._get_demo_matches()
                
        except Exception as e:
            print(f"[API-Football] [X] Error: {str(e)[:50]}")
            return self._get_demo_matches()
    
    def _parse_matches(self, matches_data: List[Dict]) -> List[Dict]:
        """
        Парсва данните от API в по-прост формат
        
        Args:
            matches_data: Сурови данни от API
            
        Returns:
            List[Dict]: Обработени данни за мачове
        """
        parsed_matches = []
        
        for match in matches_data:
            fixture = match.get('fixture', {})
            teams = match.get('teams', {})
            league = match.get('league', {})
            
            parsed_match = {
                'id': fixture.get('id'),
                'date': fixture.get('date'),
                'status': fixture.get('status', {}).get('long', 'Not Started'),
                'league': league.get('name', 'Unknown'),
                'country': league.get('country', 'Unknown'),
                'home_team': teams.get('home', {}).get('name', 'Unknown'),
                'away_team': teams.get('away', {}).get('name', 'Unknown'),
                'home_logo': teams.get('home', {}).get('logo', ''),
                'away_logo': teams.get('away', {}).get('logo', ''),
            }
            
            parsed_matches.append(parsed_match)
        
        return parsed_matches
    
    def _get_demo_matches(self) -> List[Dict]:
        """
        Връща примерни мачове за демонстрация
        
        Returns:
            List[Dict]: Демо мачове
        """
        print("[DEMO MODE] Using sample data - no real API configured")
        today = datetime.now().strftime('%Y-%m-%d')
        
        demo_matches = [
            {
                'id': 1,
                'date': f'{today}T15:00:00+00:00',
                'status': 'Not Started',
                'league': 'Premier League',
                'country': 'England',
                'home_team': 'Manchester United',
                'away_team': 'Liverpool',
                'home_logo': '',
                'away_logo': '',
                'is_demo': True,
            },
            {
                'id': 2,
                'date': f'{today}T17:30:00+00:00',
                'status': 'Not Started',
                'league': 'La Liga',
                'country': 'Spain',
                'home_team': 'Real Madrid',
                'away_team': 'Barcelona',
                'home_logo': '',
                'away_logo': '',
                'is_demo': True,
            },
            {
                'id': 3,
                'date': f'{today}T20:00:00+00:00',
                'status': 'Not Started',
                'league': 'Serie A',
                'country': 'Italy',
                'home_team': 'Juventus',
                'away_team': 'AC Milan',
                'home_logo': '',
                'away_logo': '',
                'is_demo': True,
            },
            {
                'id': 4,
                'date': f'{today}T18:00:00+00:00',
                'status': 'Not Started',
                'league': 'Bundesliga',
                'country': 'Germany',
                'home_team': 'Bayern Munich',
                'away_team': 'Borussia Dortmund',
                'home_logo': '',
                'away_logo': '',
                'is_demo': True,
            },
            {
                'id': 5,
                'date': f'{today}T19:00:00+00:00',
                'status': 'Not Started',
                'league': 'Ligue 1',
                'country': 'France',
                'home_team': 'Paris Saint Germain',
                'away_team': 'Marseille',
                'home_logo': '',
                'away_logo': '',
                'is_demo': True,
            },
        ]
        
        return demo_matches
    
    def get_team_stats(self, team_id: int, season: int = 2024) -> Dict:
        """
        Получава статистики за отбор
        
        Args:
            team_id: ID на отбора
            season: Сезон
            
        Returns:
            Dict: Статистики на отбора
        """
        if not self.api_key or self.api_key == 'YOUR_API_KEY':
            return self._get_demo_team_stats()
        
        try:
            url = f"{self.base_url}/teams/statistics"
            params = {
                'team': team_id,
                'season': season
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"Грешка при извличане на статистики: {e}")
            return self._get_demo_team_stats()
    
    def _filter_today_only(self, matches: List[Dict]) -> List[Dict]:
        """
        Филтрира мачовете да показва САМО днешни
        
        Args:
            matches: Списък с всички мачове
            
        Returns:
            List[Dict]: Само мачове за днес
        """
        today = datetime.now().date()
        filtered = []
        
        for match in matches:
            try:
                # Парсване на датата от мача
                match_date_str = match.get('date', '')
                if 'T' in match_date_str:
                    match_date = datetime.fromisoformat(match_date_str.replace('Z', '+00:00')).date()
                else:
                    match_date = datetime.strptime(match_date_str[:10], '%Y-%m-%d').date()
                
                # Включване само ако е днес
                if match_date == today:
                    filtered.append(match)
            except:
                # Ако има проблем с датата, включваме мача (за сигурност)
                filtered.append(match)
        
        return filtered
    
    def _get_demo_team_stats(self) -> Dict:
        """Връща демо статистики"""
        return {
            'wins': 15,
            'draws': 5,
            'losses': 3,
            'goals_for': 45,
            'goals_against': 20
        }
    
    def _scrape_flashscore_matches(self) -> List[Dict]:
        """
        Scrape мачове от FlashScore (алтернатива на LiveScore)
        
        Returns:
            List[Dict]: Списък с мачове
        """
        try:
            # FlashScore URL за днешни мачове
            url = "https://www.flashscore.com/football/"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'bg,en-US;q=0.7,en;q=0.3',
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            # Ако scraping не работи, използвай алтернативно API
            if response.status_code != 200:
                # FlashScore not available, using alternative source
                return self._scrape_livescore_api()
            
            # Поради динамичното съдържание на FlashScore, ще използваме алтернативен подход
            return self._scrape_livescore_api()
            
        except Exception as e:
            # Error during scraping, using alternative
            return self._scrape_livescore_api()
    
    def _scrape_livescore_api(self) -> List[Dict]:
        """
        Използва безплатно LiveScore API за получаване на мачове
        
        Returns:
            List[Dict]: Списък с мачове
        """
        try:
            # Livescore API endpoint (безплатен, без нужда от API key)
            # Този API предоставя основна информация за мачове
            url = "https://livescore-api.com/api-client/scores/live.json"
            
            headers = {
                'X-Auth-Token': '0e95643aa9a2439ca379b5bf60011974',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_livescore_data(data)
            else:
                # LiveScore API unavailable, using alternative
                return self._scrape_football_data()
                
        except Exception as e:
            # Error with LiveScore API, fallback
            return self._scrape_football_data()
    
    def _scrape_football_data(self) -> List[Dict]:
        """
        Scrape от football-data.org API (безплатно)
        
        Returns:
            List[Dict]: Списък с мачове
        """
        try:
            # Football-data.org безплатно API
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Топ европейски лиги
            leagues = [
                2021,  # Premier League
                2014,  # La Liga
                2002,  # Bundesliga
                2019,  # Serie A
                2015,  # Ligue 1
            ]
            
            all_matches = []
            
            headers = {
                'X-Auth-Token': 'YOUR_TOKEN_HERE'  # Може да работи и без token за ограничен брой заявки
            }
            
            for league_id in leagues:
                try:
                    url = f"https://api.football-data.org/v4/competitions/{league_id}/matches"
                    params = {'dateFrom': today, 'dateTo': today}
                    
                    response = requests.get(url, headers=headers, params=params, timeout=5)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('matches'):
                            all_matches.extend(self._parse_football_data_matches(data['matches']))
                            print(f"[OK] Loaded {len(data['matches'])} matches from {data.get('competition', {}).get('name', 'league')}")
                    elif response.status_code == 403:
                        print(f"[!] API requires authentication token for league {league_id}")
                    else:
                        print(f"[!] API returned status {response.status_code} for league {league_id}")
                except Exception as e:
                    print(f"[!] Error fetching league {league_id}: {str(e)[:50]}")
                    continue
            
            if all_matches:
                print(f"[OK] Found {len(all_matches)} real matches for today")
                return all_matches
            else:
                # No matches available, using demo data
                return self._get_demo_matches()
                
        except Exception as e:
            # Error, using demo data
            return self._get_demo_matches()
    
    def _parse_livescore_data(self, data: Dict) -> List[Dict]:
        """
        Парсва данни от LiveScore API
        
        Args:
            data: JSON данни от API
            
        Returns:
            List[Dict]: Обработени мачове
        """
        matches = []
        
        try:
            if 'data' in data and 'match' in data['data']:
                for match in data['data']['match']:
                    parsed = {
                        'id': match.get('id', 0),
                        'date': match.get('time', datetime.now().isoformat()),
                        'status': match.get('status', 'Not Started'),
                        'league': match.get('competition_name', 'Unknown'),
                        'country': match.get('country', 'Unknown'),
                        'home_team': match.get('home_name', 'Unknown'),
                        'away_team': match.get('away_name', 'Unknown'),
                        'home_logo': '',
                        'away_logo': '',
                    }
                    matches.append(parsed)
        except:
            pass
        
        return matches if matches else self._get_demo_matches()
    
    def _parse_football_data_matches(self, matches_data: List[Dict]) -> List[Dict]:
        """
        Парсва данни от Football-Data.org API
        
        Args:
            matches_data: Списък с мачове от API
            
        Returns:
            List[Dict]: Обработени мачове
        """
        parsed_matches = []
        
        for match in matches_data:
            try:
                parsed = {
                    'id': match.get('id', 0),
                    'date': match.get('utcDate', datetime.now().isoformat()),
                    'status': match.get('status', 'SCHEDULED'),
                    'league': match.get('competition', {}).get('name', 'Unknown'),
                    'country': match.get('area', {}).get('name', 'Unknown'),
                    'home_team': match.get('homeTeam', {}).get('name', 'Unknown'),
                    'away_team': match.get('awayTeam', {}).get('name', 'Unknown'),
                    'home_logo': match.get('homeTeam', {}).get('crest', ''),
                    'away_logo': match.get('awayTeam', {}).get('crest', ''),
                }
                parsed_matches.append(parsed)
            except:
                continue
        
        return parsed_matches


if __name__ == "__main__":
    # Тест на scraper
    scraper = MatchScraper()
    matches = scraper.get_today_matches()
    
    print(f"\nНамерени {len(matches)} мача за днес:\n")
    for match in matches:
        print(f"{match['league']} ({match['country']})")
        print(f"  {match['home_team']} vs {match['away_team']}")
        print(f"  Час: {match['date']}")
        print(f"  Статус: {match['status']}\n")
