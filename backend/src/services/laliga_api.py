import requests
import logging
import os
from typing import List, Dict, Optional
from datetime import datetime
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LaLigaAPIService:
    """
    Service to fetch LaLiga data from TheSportsDB API
    Premium API key provides access to player data and detailed statistics
    """
    
    def __init__(self):
        self.api_key = os.getenv("THESPORTSDB_API_KEY")
        self.base_url = os.getenv("THESPORTSDB_BASE_URL", "https://www.thesportsdb.com/api/v1/json")
        
        if not self.api_key:
            logger.error("THESPORTSDB_API_KEY environment variable not set!")
            raise ValueError("THESPORTSDB_API_KEY is required")
        
        # LaLiga league ID in TheSportsDB
        self.laliga_league_id = "4335"  # Spanish La Liga
        self.current_season = "2025-2026"
        
        logger.info(f"Initialized LaLiga API service with key: {self.api_key}")
        
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make HTTP request to TheSportsDB API with rate limiting and error handling.
        """
        url = f"{self.base_url}/{self.api_key}/{endpoint}"
        
        try:
            # Rate limiting for API calls
            time.sleep(0.2)
            
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Successfully fetched data from: {endpoint}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {url}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text[:200]}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching data from {url}: {e}")
            return None
    
    def get_laliga_teams(self) -> List[Dict]:
        """
        Fetch all LaLiga teams using the league teams endpoint.
        """
        logger.info("Fetching LaLiga teams...")
        
        endpoint = f"search_all_teams.php?l=Spanish%20La%20Liga"
        data = self._make_request(endpoint)
        
        if data and 'teams' in data:
            teams = self._process_teams_data(data['teams'])
            logger.info(f"Successfully fetched {len(teams)} LaLiga teams")
            return teams
        
        logger.warning("Could not fetch LaLiga teams")
        return []
    
    def get_team_players(self, team_name: str) -> List[Dict]:
        """
        Fetch players for a specific LaLiga team.
        """
        logger.info(f"Fetching players for team: {team_name}")
        
        # Search for team first to get exact name
        endpoint = f"searchteams.php?t={team_name.replace(' ', '%20')}"
        data = self._make_request(endpoint)
        
        if not data or 'teams' not in data or not data['teams']:
            logger.warning(f"Team not found: {team_name}")
            return []
        
        team = data['teams'][0]
        team_id = team.get('idTeam')
        
        if not team_id:
            logger.warning(f"No team ID found for: {team_name}")
            return []
        
        # Get players for this team
        players_endpoint = f"lookup_all_players.php?id={team_id}"
        players_data = self._make_request(players_endpoint)
        
        if players_data and 'player' in players_data:
            players = self._process_players_data(players_data['player'], team_name)
            logger.info(f"Successfully fetched {len(players)} players for {team_name}")
            return players
        
        logger.warning(f"Could not fetch players for team: {team_name}")
        return []
    
    def get_season_fixtures(self, season: str = None) -> List[Dict]:
        """
        Fetch LaLiga fixtures for the current season.
        """
        if not season:
            season = self.current_season
            
        logger.info(f"Fetching LaLiga fixtures for season: {season}")
        
        endpoint = f"eventsseason.php?id={self.laliga_league_id}&s={season}"
        data = self._make_request(endpoint)
        
        if data and 'events' in data:
            fixtures = self._process_fixtures_data(data['events'])
            logger.info(f"Successfully fetched {len(fixtures)} fixtures")
            return fixtures
        
        logger.warning("Could not fetch LaLiga fixtures")
        return []
    
    def get_league_table(self, season: str = None) -> List[Dict]:
        """
        Fetch LaLiga league table/standings.
        """
        if not season:
            season = self.current_season
            
        logger.info(f"Fetching LaLiga table for season: {season}")
        
        endpoint = f"lookuptable.php?l={self.laliga_league_id}&s={season}"
        data = self._make_request(endpoint)
        
        if data and 'table' in data:
            table = self._process_table_data(data['table'])
            logger.info(f"Successfully fetched league table with {len(table)} teams")
            return table
        
        logger.warning("Could not fetch LaLiga table")
        return []
    
    def search_player(self, player_name: str) -> List[Dict]:
        """
        Search for a specific player by name.
        """
        logger.info(f"Searching for player: {player_name}")
        
        endpoint = f"searchplayers.php?p={player_name.replace(' ', '%20')}"
        data = self._make_request(endpoint)
        
        if data and 'player' in data:
            players = self._process_players_data(data['player'])
            logger.info(f"Found {len(players)} players matching: {player_name}")
            return players
        
        logger.warning(f"No players found for: {player_name}")
        return []
    
    def _process_teams_data(self, teams_data: List[Dict]) -> List[Dict]:
        """Process teams data from API response."""
        processed_teams = []
        
        for team in teams_data:
            if team.get('strLeague') == 'Spanish La Liga':  # Filter for LaLiga only
                processed_team = {
                    'id': team.get('idTeam'),
                    'name': team.get('strTeam'),
                    'short_name': team.get('strTeamShort'),
                    'country': team.get('strCountry'),
                    'city': team.get('strLocation'),
                    'founded': team.get('intFormedYear'),
                    'stadium': team.get('strStadium'),
                    'capacity': team.get('intStadiumCapacity'),
                    'logo_url': team.get('strTeamBadge'),
                    'website': team.get('strWebsite'),
                    'league': 'LaLiga'
                }
                processed_teams.append(processed_team)
        
        return processed_teams
    
    def _process_players_data(self, players_data: List[Dict], team_name: str = None) -> List[Dict]:
        """Process players data from API response."""
        processed_players = []
        
        for player in players_data:
            # Skip if not a LaLiga player (check team or nationality)
            player_team = player.get('strTeam', team_name)
            
            processed_player = {
                'id': player.get('idPlayer'),
                'name': player.get('strPlayer'),
                'team': player_team,
                'position': self._normalize_position(player.get('strPosition')),
                'jersey_number': player.get('strNumber'),
                'nationality': player.get('strNationality'),
                'birth_date': player.get('dateBorn'),
                'height': player.get('strHeight'),
                'weight': player.get('strWeight'),
                'photo_url': player.get('strThumb'),
                'description': player.get('strDescriptionEN'),
                'wage': player.get('strWage'),
                'is_active': True
            }
            processed_players.append(processed_player)
        
        return processed_players
    
    def _process_fixtures_data(self, fixtures_data: List[Dict]) -> List[Dict]:
        """Process fixtures data from API response."""
        processed_fixtures = []
        
        for fixture in fixtures_data:
            processed_fixture = {
                'id': fixture.get('idEvent'),
                'date': fixture.get('dateEvent'),
                'time': fixture.get('strTime'),
                'round': fixture.get('intRound'),
                'home_team': fixture.get('strHomeTeam'),
                'away_team': fixture.get('strAwayTeam'),
                'home_score': fixture.get('intHomeScore'),
                'away_score': fixture.get('intAwayScore'),
                'status': self._get_match_status(fixture),
                'venue': fixture.get('strVenue'),
                'season': fixture.get('strSeason'),
                'league': 'LaLiga'
            }
            processed_fixtures.append(processed_fixture)
        
        return processed_fixtures
    
    def _process_table_data(self, table_data: List[Dict]) -> List[Dict]:
        """Process league table data from API response."""
        processed_table = []
        
        for entry in table_data:
            processed_entry = {
                'position': entry.get('intRank'),
                'team': entry.get('strTeam'),
                'played': entry.get('intPlayed'),
                'won': entry.get('intWin'),
                'drawn': entry.get('intDraw'),
                'lost': entry.get('intLoss'),
                'goals_for': entry.get('intGoalsFor'),
                'goals_against': entry.get('intGoalsAgainst'),
                'goal_difference': entry.get('intGoalDifference'),
                'points': entry.get('intPoints'),
                'form': entry.get('strForm')
            }
            processed_table.append(processed_entry)
        
        return processed_table
    
    def _normalize_position(self, position: str) -> str:
        """Normalize player positions to our standard format."""
        if not position:
            return "MID"
        
        position = position.upper()
        
        if any(pos in position for pos in ['GOALKEEPER', 'GK', 'KEEPER', 'PORTERO']):
            return "GK"
        elif any(pos in position for pos in ['DEFENDER', 'DEF', 'DEFENCE', 'BACK', 'DEFENSA']):
            return "DEF"
        elif any(pos in position for pos in ['FORWARD', 'FWD', 'STRIKER', 'ATTACKER', 'DELANTERO']):
            return "FWD"
        else:
            return "MID"  # Default to midfielder
    
    def _get_match_status(self, fixture: Dict) -> str:
        """Determine match status from fixture data."""
        if fixture.get('intHomeScore') is not None and fixture.get('intAwayScore') is not None:
            return "finished"
        elif fixture.get('strStatus') == 'Match Finished':
            return "finished"
        else:
            return "scheduled"


# Global instance
laliga_api = LaLigaAPIService()


def test_laliga_api():
    """Test the LaLiga API connection and data fetching."""
    logger.info("Testing LaLiga API connection...")
    
try:
    # Test getting teams
    logger.info("Testing LaLiga teams endpoint...")
    teams = laliga_api.get_laliga_teams()
    
    if teams:
        logger.info(f"Successfully fetched {len(teams)} LaLiga teams")
        logger.info(f"Sample team: {teams[0] if teams else 'None'}")
        
        # Test getting players for first team
        if teams:
            first_team = teams[0]['name']
            logger.info(f"Testing players for {first_team}...")
            players = laliga_api.get_team_players(first_team)
            
            if players:
                logger.info(f"Successfully fetched {len(players)} players for {first_team}")
                logger.info(f"Sample player: {players[0] if players else 'None'}")
            else:
                logger.warning(f"No players found for {first_team}")
    
    # Test fixtures
    logger.info("Testing LaLiga fixtures...")
    fixtures = laliga_api.get_season_fixtures()
    
    if fixtures:
        logger.info(f"Successfully fetched {len(fixtures)} fixtures")
    else:
        logger.warning("No fixtures found")
    
    # Test league table
    logger.info("Testing LaLiga table...")
    table = laliga_api.get_league_table()
    
    if table:
        logger.info(f"Successfully fetched league table with {len(table)} teams")
    else:
        logger.warning("No league table found")
except Exception as e:
    logger.error(f"An error occurred during LaLiga API testing: {e}")