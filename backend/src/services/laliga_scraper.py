"""FBref LaLiga scraper with rate limiting and retry logic."""

import logging
import time
import re
from typing import List, Dict, Optional, Any
from datetime import datetime
from urllib.parse import urljoin
from io import StringIO

import requests
import cloudscraper
from bs4 import BeautifulSoup
import pandas as pd

logger = logging.getLogger(__name__)


class FBrefScraper:
    """Scraper for FBref.com LaLiga player statistics with rate limiting."""
    
    BASE_URL = "https://fbref.com"
    LALIGA_COMP_ID = "12"  # FBref's competition ID for LaLiga
    
    # Rate limiting
    REQUEST_DELAY = 2.5  # seconds between requests
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds to wait before retry
    
    def __init__(self, season: str = "2025-2026"):
        """
        Initialize the scraper.
        
        Args:
            season: Season string in format "YYYY-YYYY" (e.g., "2024-2025")
        """
        self.season = season
        try:
            # cloudscraper helps bypass Cloudflare blocks that return HTTP 403
            self.session = cloudscraper.create_scraper(
                browser={
                    "browser": "chrome",
                    "platform": "windows",
                    "mobile": False,
                }
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("cloudscraper init failed (%s), falling back to requests", exc)
            self.session = requests.Session()

        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://fbref.com/',
        })
        self.last_request_time = 0
        
        logger.info(f"FBref scraper initialized for LaLiga season {season}")
    
    def _rate_limit(self):
        """Implement rate limiting between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.REQUEST_DELAY:
            sleep_time = self.REQUEST_DELAY - elapsed
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, retries: int = 0) -> Optional[requests.Response]:
        """
        Make a HTTP request with error handling and retries.
        
        Args:
            url: URL to request
            retries: Current retry count
            
        Returns:
            Response object or None if failed
        """
        self._rate_limit()
        
        try:
            logger.debug(f"Requesting: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response
        
        except requests.RequestException as e:
            logger.warning(f"Request failed for {url}: {e}")
            
            if retries < self.MAX_RETRIES:
                logger.info(f"Retrying... (attempt {retries + 1}/{self.MAX_RETRIES})")
                time.sleep(self.RETRY_DELAY)
                return self._make_request(url, retries + 1)
            else:
                logger.error(f"Max retries reached for {url}")
                return None
    
    def get_season_schedule_url(self) -> str:
        """
        Get the URL for the LaLiga season schedule page.
        
        Returns:
            URL string
        """
        return f"{self.BASE_URL}/en/comps/{self.LALIGA_COMP_ID}/{self.season}/schedule/{self.season}-La-Liga-Scores-and-Fixtures"
    
    def get_matches_for_matchday(self, matchday: int) -> List[Dict[str, Any]]:
        """
        Get all match information for a specific matchday.
        
        Args:
            matchday: Matchday/gameweek number (1-38 for LaLiga)
            
        Returns:
            List of match dictionaries containing match info and URLs
        """
        logger.info(f"Fetching matches for matchday {matchday}")
        
        schedule_url = self.get_season_schedule_url()
        response = self._make_request(schedule_url)
        
        if not response:
            logger.error(f"Failed to fetch schedule page")
            return []
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Find the schedule table (ID format: sched_YYYY-YYYY_COMP_1)
        schedule_table = soup.find('table', {'id': re.compile(r'^sched_.*')})
        if not schedule_table:
            logger.error("Could not find schedule table on page")
            return []
        
        matches = []
        rows = schedule_table.find('tbody').find_all('tr')
        
        for row in rows:
            # Skip rows that are just headers
            if row.get('class') and 'spacer' in row.get('class'):
                continue
            
            # Get matchday number from the row
            matchday_cell = row.find('th', {'data-stat': 'gameweek'})
            if not matchday_cell:
                continue
            
            try:
                row_matchday = int(matchday_cell.text.strip())
            except (ValueError, AttributeError):
                continue
            
            # Only process rows for the requested matchday
            if row_matchday != matchday:
                continue
            
            # Extract match information
            date_cell = row.find('td', {'data-stat': 'date'})
            home_team_cell = row.find('td', {'data-stat': 'home_team'})
            away_team_cell = row.find('td', {'data-stat': 'away_team'})
            score_cell = row.find('td', {'data-stat': 'score'})
            match_report_cell = row.find('td', {'data-stat': 'match_report'})
            
            if not all([home_team_cell, away_team_cell]):
                continue
            
            # Get match report link
            match_report_link = None
            if match_report_cell:
                link = match_report_cell.find('a')
                if link and link.get('href'):
                    match_report_link = urljoin(self.BASE_URL, link['href'])
            
            # Skip if no match report available (match not played yet)
            if not match_report_link:
                logger.debug(f"No match report available yet for {home_team_cell.text.strip()} vs {away_team_cell.text.strip()}")
                continue
            
            # Parse score if available
            home_score = None
            away_score = None
            if score_cell and score_cell.text.strip() and '–' in score_cell.text:
                try:
                    scores = score_cell.text.strip().split('–')
                    home_score = int(scores[0].strip())
                    away_score = int(scores[1].strip())
                except (ValueError, IndexError):
                    pass
            
            match_info = {
                'matchday': matchday,
                'home_team': home_team_cell.text.strip(),
                'away_team': away_team_cell.text.strip(),
                'home_score': home_score,
                'away_score': away_score,
                'match_date': date_cell.text.strip() if date_cell else None,
                'match_report_url': match_report_link,
                'season': self.season
            }
            
            matches.append(match_info)
            logger.debug(f"Found match: {match_info['home_team']} vs {match_info['away_team']}")
        
        logger.info(f"Found {len(matches)} matches for matchday {matchday}")
        return matches
    
    def parse_match_stats(self, match_url: str, match_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse player statistics from a match report page.
        
        Args:
            match_url: URL of the match report
            match_info: Dictionary containing match information (home_team, away_team, scores, etc.)
            
        Returns:
            List of player statistics dictionaries
        """
        logger.info(f"Parsing match stats from {match_url}")
        
        response = self._make_request(match_url)
        if not response:
            logger.error(f"Failed to fetch match page")
            return []
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        all_player_stats = []
        
        # Get both home and away team stats
        for team_name in [match_info['home_team'], match_info['away_team']]:
            team_stats = self._parse_team_player_stats(soup, team_name, match_info)
            all_player_stats.extend(team_stats)
        
        logger.info(f"Extracted stats for {len(all_player_stats)} players")
        return all_player_stats
    
    def _parse_team_player_stats(self, soup: BeautifulSoup, team_name: str, 
                                  match_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse player statistics for a specific team from the match page.
        
        Args:
            soup: BeautifulSoup object of the match page
            team_name: Name of the team
            match_info: Match information dictionary
            
        Returns:
            List of player statistics dictionaries
        """
        player_stats_list = []
        
        # Find all player stat tables (there are multiple per match)
        # Common table IDs: stats_{team_id}_summary, stats_{team_id}_passing, stats_{team_id}_defense, etc.
        
        # First, find the summary stats table which contains basic info
        summary_tables = soup.find_all('table', {'id': re.compile(r'stats_.*_summary')})
        
        for table in summary_tables:
            # Check if this table is for the current team
            caption = table.find('caption')
            if not caption or team_name not in caption.text:
                continue
            
            # Parse the summary table
            try:
                df = pd.read_html(StringIO(str(table)))[0]
            except Exception as e:
                logger.warning(f"Failed to parse table for {team_name}: {e}")
                continue
            
            # Handle multi-level columns
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join(col).strip() if col[1] else col[0] for col in df.columns.values]
            
            # Clean column names
            df.columns = [str(col).strip() for col in df.columns]
            
            # Process each player row
            for idx, row in df.iterrows():
                # Skip non-player rows (subtotals, headers, summary rows like "16 Players", etc.)
                player_name = self._get_column_value(row, ['Player', 'Unnamed: 0_level_0_Player'], '')
                
                # Skip invalid rows: empty, 'Player' header, or summary rows like "16 Players"
                if not player_name or pd.isna(player_name) or player_name == 'Player':
                    continue
                
                # Skip summary rows that match pattern like "16 Players", "11 Players", etc.
                if re.match(r'^\d+\s+Players?$', str(player_name).strip(), re.IGNORECASE):
                    logger.debug(f"Skipping summary row: {player_name}")
                    continue
                
                # Extract basic stats using flexible column matching
                player_stat = {
                    'player_name': str(player_name).strip(),
                    'team': team_name,
                    'match_info': match_info,
                    'minutes_played': self._parse_int(self._get_column_value(row, ['Min', '_Min'], 0)),
                    'goals': self._parse_int(self._get_column_value(row, ['Gls', '_Gls', 'Performance_Gls'], 0)),
                    'assists': self._parse_int(self._get_column_value(row, ['Ast', '_Ast', 'Performance_Ast'], 0)),
                    'yellow_cards': self._parse_int(self._get_column_value(row, ['CrdY', '_CrdY', 'Performance_CrdY'], 0)),
                    'red_cards': self._parse_int(self._get_column_value(row, ['CrdR', '_CrdR', 'Performance_CrdR'], 0)),
                    'saves': 0,  # Will be updated from goalkeeper table
                    'own_goals': 0,  # Will be extracted separately if available
                    'penalties_missed': 0,  # Will be extracted from penalty tables
                    'penalties_saved': 0,  # For goalkeepers
                    'clean_sheet': False  # Will be calculated based on team performance
                }
                
                player_stats_list.append(player_stat)
        
        # Now try to find goalkeeper-specific stats
        self._add_goalkeeper_stats(soup, team_name, player_stats_list)
        
        # Add penalty stats
        self._add_penalty_stats(soup, team_name, player_stats_list)
        
        # Calculate clean sheets
        self._calculate_clean_sheets(player_stats_list, match_info, team_name)
        
        return player_stats_list
    
    def _add_goalkeeper_stats(self, soup: BeautifulSoup, team_name: str, 
                             player_stats_list: List[Dict[str, Any]]):
        """
        Add goalkeeper-specific statistics (saves, penalties saved).
        
        Args:
            soup: BeautifulSoup object of the match page
            team_name: Name of the team
            player_stats_list: List of player stats to update
        """
        # Look for goalkeeper stats table
        gk_tables = soup.find_all('table', {'id': re.compile(r'keeper_stats_.*')})
        
        for table in gk_tables:
            caption = table.find('caption')
            if not caption or team_name not in caption.text:
                continue
            
            try:
                df = pd.read_html(StringIO(str(table)))[0]
                
                # Handle multi-level columns
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = ['_'.join(col).strip() if col[1] else col[0] for col in df.columns.values]
                
                df.columns = [str(col).strip() for col in df.columns]
                
                for idx, row in df.iterrows():
                    player_name = self._get_column_value(row, ['Player', 'Unnamed: 0_level_0_Player'], '')
                    
                    if not player_name or pd.isna(player_name) or player_name == 'Player':
                        continue
                    
                    # Skip summary rows like "16 Players"
                    if re.match(r'^\d+\s+Players?$', str(player_name).strip(), re.IGNORECASE):
                        continue
                    
                    player_name = str(player_name).strip()
                    
                    # Find this player in our stats list and update saves
                    for player_stat in player_stats_list:
                        if player_stat['player_name'] == player_name:
                            # Try multiple column names for saves
                            saves_value = self._get_column_value(row, ['Saves', 'SoTA', '_Saves'], 0)
                            player_stat['saves'] = self._parse_int(saves_value)
                            # Penalties saved
                            player_stat['penalties_saved'] = self._parse_int(self._get_column_value(row, ['PKsv', 'PSxG', '_PKsv'], 0))
                            break
            
            except Exception as e:
                logger.warning(f"Failed to parse goalkeeper table for {team_name}: {e}")
    
    def _add_penalty_stats(self, soup: BeautifulSoup, team_name: str, 
                          player_stats_list: List[Dict[str, Any]]):
        """
        Add penalty statistics (penalties missed).
        
        Args:
            soup: BeautifulSoup object of the match page
            team_name: Name of the team
            player_stats_list: List of player stats to update
        """
        # Look for shooting or penalty tables
        shooting_tables = soup.find_all('table', {'id': re.compile(r'stats_.*_shooting')})
        
        for table in shooting_tables:
            caption = table.find('caption')
            if not caption or team_name not in caption.text:
                continue
            
            try:
                df = pd.read_html(StringIO(str(table)))[0]
                
                # Handle multi-level columns
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = ['_'.join(col).strip() if col[1] else col[0] for col in df.columns.values]
                
                df.columns = [str(col).strip() for col in df.columns]
                
                for idx, row in df.iterrows():
                    player_name = self._get_column_value(row, ['Player', 'Unnamed: 0_level_0_Player'], '')
                    
                    if not player_name or pd.isna(player_name) or player_name == 'Player':
                        continue
                    
                    # Skip summary rows like "16 Players"
                    if re.match(r'^\d+\s+Players?$', str(player_name).strip(), re.IGNORECASE):
                        continue
                    
                    player_name = str(player_name).strip()
                    
                    # Check for penalty attempts and made
                    pk_att = self._parse_int(self._get_column_value(row, ['PKatt', 'PK_Standard', '_PKatt'], 0))
                    pk_made = self._parse_int(self._get_column_value(row, ['PK', '_PK', 'Performance_PK'], 0))
                    
                    if pk_att and pk_att > pk_made:
                        penalties_missed = pk_att - pk_made
                        
                        # Update player stats
                        for player_stat in player_stats_list:
                            if player_stat['player_name'] == player_name:
                                player_stat['penalties_missed'] = penalties_missed
                                break
            
            except Exception as e:
                logger.warning(f"Failed to parse shooting table for {team_name}: {e}")
    
    def _calculate_clean_sheets(self, player_stats_list: List[Dict[str, Any]], 
                               match_info: Dict[str, Any], team_name: str):
        """
        Calculate which players earned a clean sheet.
        
        Clean sheet rules:
        - Team must not concede any goals
        - Player must play 60+ minutes
        - Only applies to GK and DEF positions
        
        Args:
            player_stats_list: List of player stats to update
            match_info: Match information including scores
            team_name: Name of the team
        """
        # Determine goals conceded
        if team_name == match_info['home_team']:
            goals_conceded = match_info.get('away_score', 0) or 0
        else:
            goals_conceded = match_info.get('home_score', 0) or 0
        
        # Clean sheet only if no goals conceded
        if goals_conceded == 0:
            for player_stat in player_stats_list:
                # Player must have played 60+ minutes
                if player_stat['minutes_played'] >= 60:
                    player_stat['clean_sheet'] = True
    
    @staticmethod
    def _parse_int(value: Any) -> int:
        """
        Safely parse integer from various input types.
        
        Args:
            value: Value to parse
            
        Returns:
            Integer value or 0 if parsing fails
        """
        if pd.isna(value):
            return 0
        
        try:
            # Remove any non-numeric characters except minus sign
            if isinstance(value, str):
                value = re.sub(r'[^\d-]', '', value)
            return int(float(value))
        except (ValueError, TypeError):
            return 0
    
    @staticmethod
    def _get_column_value(row: pd.Series, column_patterns: List[str], default: Any = 0) -> Any:
        """
        Get value from a row by trying multiple column name patterns.
        Useful for handling multi-level column names that get flattened.
        
        Args:
            row: Pandas Series (row of dataframe)
            column_patterns: List of possible column names to try
            default: Default value if no column found
            
        Returns:
            Value from first matching column, or default
        """
        for pattern in column_patterns:
            # Try exact match first
            if pattern in row.index:
                return row[pattern]
            
            # Try partial match (for flattened multi-level columns)
            matching_cols = [col for col in row.index if pattern in str(col)]
            if matching_cols:
                return row[matching_cols[0]]
        
        return default
    
    def scrape_matchday(self, matchday: int) -> List[Dict[str, Any]]:
        """
        Scrape all player statistics for a complete matchday.
        
        This is the main method you'll use to fetch data.
        
        Args:
            matchday: Matchday/gameweek number (1-38)
            
        Returns:
            List of all player statistics for the matchday
        """
        logger.info(f"Starting scrape for matchday {matchday}")
        
        # Get all matches for this matchday
        matches = self.get_matches_for_matchday(matchday)
        
        if not matches:
            logger.warning(f"No matches found for matchday {matchday}")
            return []
        
        all_player_stats = []
        
        # Scrape each match
        for match in matches:
            logger.info(f"Processing: {match['home_team']} vs {match['away_team']}")
            
            player_stats = self.parse_match_stats(match['match_report_url'], match)
            all_player_stats.extend(player_stats)
        
        logger.info(f"Completed scrape for matchday {matchday}: {len(all_player_stats)} player records")
        return all_player_stats
