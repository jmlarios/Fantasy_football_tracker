"""Fantasy scoring system for LaLiga Fantasy Football Tracker."""
import logging
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class FantasyScoring:
    """Calculate fantasy points based on player performance."""
    
    def __init__(self):
        # Scoring rules configuration
        self.scoring_rules = {
            'match_played': {
                '60_or_more': 1,
                'less_than_60': 0.5
            },
            'goals': {
                'GK': 6,
                'DEF': 6,
                'MID': 5,
                'FWD': 4
            },
            'assists': {
                'goal_assist': 3,
                'assist_without_goal': 1
            },
            'clean_sheet': {
                'GK': 4,
                'DEF': 4,
                'MID': 1,
                'FWD': 0
            },
            'cards': {
                'yellow': -1,
                'red': -3
            },
            'goals_conceded': {
                'threshold': 2,  # Every 2 goals conceded
                'GK': -1,
                'DEF': -1
            },
            'own_goal': -2,
            'penalty_missed': -2,
            'penalty_saved': 5,
            'saves': {
                'threshold': 3,
                'points': 1
            },
            'penalties': {
                'won': 2,
                'committed': -1,
                'saved': 5,
                'missed': -2
            },
            'defensive_bonus': {
                'balls_recovered': {
                    'threshold': 5,
                    'points': 1
                },
                'clearances': {
                    'threshold': 3,
                    'points': 1
                }
            },
            'attack_bonus': {
                'shots_on_target': {
                    'threshold': 2,
                    'points': 1
                },
                'successful_dribbles': {
                    'threshold': 2,
                    'points': 1
                },
                'entries_into_box': {
                    'threshold': 2,
                    'points': 1
                }
            },
            'captain_multiplier': 2.0
        }
    
    @staticmethod
    def _calculate_threshold_points(value: int, threshold: int, points_per_group: float) -> float:
        """
        Helper to calculate points based on threshold groups.
        
        Args:
            value: The stat value (e.g., number of saves)
            threshold: How many units needed for points (e.g., 3 saves)
            points_per_group: Points awarded per threshold group
            
        Returns:
            Total points from threshold groups
        """
        if value >= threshold:
            groups = value // threshold
            return groups * points_per_group
        return 0.0
    
    def calculate_player_points(self, player_stats: Dict, player_position: str, 
                              match_result: Optional[str] = None, goals_conceded: int = 0) -> Dict[str, float]:
        """
        Calculate fantasy points for a player based on LaLiga Fantasy rules.
        
        Args:
            player_stats: Dictionary containing player's match statistics
            player_position: Player position (GK, DEF, MID, FWD)
            match_result: Team's match result ('win', 'draw', 'loss')
            goals_conceded: Number of goals conceded by player's team
            
        Returns:
            Dictionary with point breakdown and total points
        """
        points_breakdown = {
            'match_played': 0.0,
            'goals': 0.0,
            'goal_assists': 0.0,
            'assist_without_goal': 0.0,
            'clean_sheet': 0.0,
            'yellow_cards': 0.0,
            'red_cards': 0.0,
            'goals_conceded': 0.0,
            'saves': 0.0,
            'penalty_saved': 0.0,
            'penalty_missed': 0.0,
            'penalty_won': 0.0,
            'penalty_committed': 0.0,
            'balls_recovered': 0.0,
            'clearances': 0.0,
            'shots_on_target': 0.0,
            'successful_dribbles': 0.0,
            'entries_into_box': 0.0,
            'total': 0.0
        }
        
        # Match played points
        minutes = player_stats.get('minutes_played', 0)
        if minutes > 0:
            if minutes >= 60:
                points_breakdown['match_played'] = self.scoring_rules['match_played']['60_or_more']
            else:
                points_breakdown['match_played'] = self.scoring_rules['match_played']['less_than_60']
        
        # Goals points (position-dependent)
        goals = player_stats.get('goals', 0)
        if goals > 0:
            points_breakdown['goals'] = goals * self.scoring_rules['goals'][player_position]
        
        # Goal assists
        goal_assists = player_stats.get('goal_assists', player_stats.get('assists', 0))
        if goal_assists > 0:
            points_breakdown['goal_assists'] = goal_assists * self.scoring_rules['assists']['goal_assist']
        
        # Assists without goal (clear goal-scoring chances)
        assist_without_goal = player_stats.get('assist_without_goal', 0)
        if assist_without_goal > 0:
            points_breakdown['assist_without_goal'] = assist_without_goal * self.scoring_rules['assists']['assist_without_goal']
        
        # Clean sheet points (only if played >60 min and no goals conceded)
        if (player_stats.get('clean_sheet', False) and goals_conceded == 0 and minutes >= 60):
            points_breakdown['clean_sheet'] = self.scoring_rules['clean_sheet'][player_position]
        
        # Goals conceded penalty (for GK and DEF only, every 2 goals)
        if goals_conceded > 0 and player_position in ['GK', 'DEF']:
            conceded_groups = goals_conceded // self.scoring_rules['goals_conceded']['threshold']
            if conceded_groups > 0:
                points_breakdown['goals_conceded'] = conceded_groups * self.scoring_rules['goals_conceded'][player_position]
        
        # Cards (negative points)
        yellow_cards = player_stats.get('yellow_cards', 0)
        if yellow_cards > 0:
            points_breakdown['yellow_cards'] = yellow_cards * self.scoring_rules['cards']['yellow']
        
        red_cards = player_stats.get('red_cards', 0)
        if red_cards > 0:
            points_breakdown['red_cards'] = red_cards * self.scoring_rules['cards']['red']
        
        # Goalkeeper-specific scoring
        if player_position == 'GK':
            # Saves (every 3 saves = 1 point)
            saves = player_stats.get('saves', 0)
            points_breakdown['saves'] = self._calculate_threshold_points(
                saves, 
                self.scoring_rules['saves']['threshold'],
                self.scoring_rules['saves']['points']
            )
            
            # Penalty saves
            penalty_saves = player_stats.get('penalties_saved', 0)
            if penalty_saves > 0:
                points_breakdown['penalty_saved'] = penalty_saves * self.scoring_rules['penalties']['saved']
        
        # Penalty actions (all positions)
        penalty_misses = player_stats.get('penalties_missed', 0)
        if penalty_misses > 0:
            points_breakdown['penalty_missed'] = penalty_misses * self.scoring_rules['penalties']['missed']
        
        penalties_won = player_stats.get('penalties_won', 0)
        if penalties_won > 0:
            points_breakdown['penalty_won'] = penalties_won * self.scoring_rules['penalties']['won']
        
        penalties_committed = player_stats.get('penalties_committed', 0)
        if penalties_committed > 0:
            points_breakdown['penalty_committed'] = penalties_committed * self.scoring_rules['penalties']['committed']
        
        # Defensive bonus stats (every 5 balls recovered = 1 point)
        balls_recovered = player_stats.get('balls_recovered', 0)
        points_breakdown['balls_recovered'] = self._calculate_threshold_points(
            balls_recovered,
            self.scoring_rules['defensive_bonus']['balls_recovered']['threshold'],
            self.scoring_rules['defensive_bonus']['balls_recovered']['points']
        )
        
        # Clearances (every 3 clearances = 1 point)
        clearances = player_stats.get('clearances', 0)
        points_breakdown['clearances'] = self._calculate_threshold_points(
            clearances,
            self.scoring_rules['defensive_bonus']['clearances']['threshold'],
            self.scoring_rules['defensive_bonus']['clearances']['points']
        )
        
        # Attack bonus stats (every 2 shots on target = 1 point)
        shots_on_target = player_stats.get('shots_on_target', 0)
        points_breakdown['shots_on_target'] = self._calculate_threshold_points(
            shots_on_target,
            self.scoring_rules['attack_bonus']['shots_on_target']['threshold'],
            self.scoring_rules['attack_bonus']['shots_on_target']['points']
        )
        
        # Successful dribbles (every 2 = 1 point)
        successful_dribbles = player_stats.get('successful_dribbles', 0)
        points_breakdown['successful_dribbles'] = self._calculate_threshold_points(
            successful_dribbles,
            self.scoring_rules['attack_bonus']['successful_dribbles']['threshold'],
            self.scoring_rules['attack_bonus']['successful_dribbles']['points']
        )
        
        # Entries into the box (every 2 = 1 point)
        entries_into_box = player_stats.get('entries_into_box', 0)
        points_breakdown['entries_into_box'] = self._calculate_threshold_points(
            entries_into_box,
            self.scoring_rules['attack_bonus']['entries_into_box']['threshold'],
            self.scoring_rules['attack_bonus']['entries_into_box']['points']
        )
        
        # Calculate total points
        points_breakdown['total'] = sum(points_breakdown.values())
        
        logger.debug(f"Calculated LaLiga Fantasy points for {player_position}: {points_breakdown['total']}")
        return points_breakdown
    
    def calculate_team_points(self, team_players: List[Dict], captain_id: Optional[int] = None) -> Dict:
        """
        Calculate total fantasy points for a LaLiga fantasy team.
        
        Args:
            team_players: List of player dictionaries with stats and positions
            captain_id: ID of the captain (gets 2x points)
            
        Returns:
            Dictionary with team point breakdown and total
        """
        team_points = {
            'players': [],
            'captain_bonus': 0.0,
            'total_points': 0.0,
            'players_played': 0,
            'formation_valid': True
        }
        
        # Count players by position for formation validation
        position_counts = {'GK': 0, 'DEF': 0, 'MID': 0, 'FWD': 0}
        
        for player in team_players:
            player_id = player.get('id')
            player_position = player.get('position')
            player_stats = player.get('stats', {})
            match_result = player.get('match_result')
            goals_conceded = player.get('goals_conceded', 0)
            
            # Calculate base points for this player
            player_points = self.calculate_player_points(
                player_stats, player_position, match_result, goals_conceded
            )
            
            # Check if player actually played
            minutes_played = player_stats.get('minutes_played', 0)
            if minutes_played > 0:
                team_points['players_played'] += 1
                position_counts[player_position] += 1
                
                # Apply captain multiplier
                final_points = player_points['total']
                multiplier = 1.0
                
                if player_id == captain_id:
                    multiplier = self.scoring_rules['captain_multiplier']
                    team_points['captain_bonus'] = final_points * (multiplier - 1)
                
                final_points *= multiplier
                
                team_points['players'].append({
                    'player_id': player_id,
                    'position': player_position,
                    'points': final_points,
                    'multiplier': multiplier,
                    'breakdown': player_points
                })
                
                team_points['total_points'] += final_points
        
        # LaLiga formation validation (11 players with minimum requirements)
        # Must have at least 1 GK, 3 DEF, 2 MID, 1 FWD
        if (position_counts['GK'] < 1 or position_counts['DEF'] < 3 or 
            position_counts['MID'] < 2 or position_counts['FWD'] < 1):
            team_points['formation_valid'] = False
            logger.warning(f"Invalid LaLiga formation: {position_counts}")
        
        logger.info(f"LaLiga team total points: {team_points['total_points']:.1f} ({team_points['players_played']} players)")
        return team_points
    
    def get_scoring_rules(self) -> Dict:
        """
        Return the current scoring rules configuration.
        """
        return self.scoring_rules
    
    def validate_team_formation(self, team_players: List[Dict]) -> Dict:
        """
        Validate team formation according to UEFA rules.
        
        Returns:
            Dictionary with validation results and requirements
        """
        position_counts = {'GK': 0, 'DEF': 0, 'MID': 0, 'FWD': 0}
        
        for player in team_players:
            position = player.get('position')
            if position in position_counts:
                position_counts[position] += 1
        
        # UEFA formation requirements
        requirements = {
            'GK': {'min': 1, 'max': 1},    # Exactly 1 goalkeeper
            'DEF': {'min': 3, 'max': 5},   # 3-5 defenders
            'MID': {'min': 2, 'max': 5},   # 2-5 midfielders  
            'FWD': {'min': 1, 'max': 3}    # 1-3 forwards
        }
        
        validation_result = {
            'is_valid': True,
            'errors': [],
            'position_counts': position_counts,
            'requirements': requirements,
            'total_players': sum(position_counts.values())
        }
        
        # Check total players (should be exactly 11)
        if validation_result['total_players'] != 11:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Team must have exactly 11 players, found {validation_result['total_players']}")
        
        # Check position requirements
        for position, req in requirements.items():
            count = position_counts[position]
            if count < req['min']:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f"Need at least {req['min']} {position}, found {count}")
            elif count > req['max']:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f"Maximum {req['max']} {position} allowed, found {count}")
        
        return validation_result

# Global scoring instance
fantasy_scoring = FantasyScoring()


def calculate_matchday_points(db: Session, matchday: int) -> Dict:
    """
    Calculate fantasy points for all teams in a specific matchday.
    
    Args:
        db: Database session
        matchday: Matchday number to process
        
    Returns:
        Dictionary with results for all fantasy teams
    """
    from config import SessionLocal
    from src.models import FantasyTeam, FantasyTeamPlayer, Player, MatchPlayerStats, Match 
    
    results = {
        'matchday': matchday,
        'teams_processed': 0,
        'teams': []
    }
    
    try:
        # Get all fantasy teams
        fantasy_teams = db.query(FantasyTeam).all()
        
        for team in fantasy_teams:
            team_result = process_team_matchday(db, team, matchday)
            results['teams'].append(team_result)
            results['teams_processed'] += 1
        
        logger.info(f"Processed {results['teams_processed']} teams for matchday {matchday}")
        
    except Exception as e:
        logger.error(f"Error calculating matchday points: {e}")
    
    return results


def process_team_matchday(db: Session, fantasy_team, matchday: int) -> Dict:
    """
    Process a single fantasy team's points for a matchday.
    Updated to include new scoring stats.
    """
    from src.models import FantasyTeamPlayer, Player, MatchPlayerStats, Match 
    
    # Get team players
    team_players = db.query(FantasyTeamPlayer).filter(
        FantasyTeamPlayer.fantasy_team_id == fantasy_team.id
    ).all()
    
    # Find captain
    captain_id = None
    for tp in team_players:
        if tp.is_captain:
            captain_id = tp.player_id
            break
    
    # Collect player stats for this matchday
    players_with_stats = []
    
    for team_player in team_players:
        player = db.query(Player).filter(Player.id == team_player.player_id).first()
        
        # Get player's match stats for this matchday
        match_stats = db.query(MatchPlayerStats).join(Match).filter(
            MatchPlayerStats.player_id == team_player.player_id,
            Match.matchday == matchday
        ).first()
        
        # Get match info for team result and goals conceded
        match = db.query(Match).filter(Match.matchday == matchday).first()
        match_result = 'draw'  # Default
        goals_conceded = 0
        
        if match and match.is_finished:
            if player.team == match.home_team:
                goals_conceded = match.away_score or 0
                if (match.home_score or 0) > (match.away_score or 0):
                    match_result = 'win'
                elif (match.home_score or 0) < (match.away_score or 0):
                    match_result = 'loss'
            elif player.team == match.away_team:
                goals_conceded = match.home_score or 0
                if (match.away_score or 0) > (match.home_score or 0):
                    match_result = 'win'
                elif (match.away_score or 0) < (match.home_score or 0):
                    match_result = 'loss'
        
        if match_stats:
            players_with_stats.append({
                'id': player.id,
                'name': player.name,
                'position': player.position,
                'match_result': match_result,
                'goals_conceded': goals_conceded,
                'stats': {
                    'minutes_played': match_stats.minutes_played,
                    'goals': match_stats.goals,
                    'assists': match_stats.assists,
                    'yellow_cards': match_stats.yellow_cards,
                    'red_cards': match_stats.red_cards,
                    'clean_sheet': match_stats.clean_sheet,
                    'saves': match_stats.saves,
                    'own_goals': match_stats.own_goals,
                    'penalties_missed': match_stats.penalties_missed,
                    'penalties_saved': match_stats.penalties_saved,
                    # New stats for updated scoring
                    'balls_recovered': getattr(match_stats, 'ball_recoveries', 0),
                    'penalties_won': getattr(match_stats, 'penalties_won', 0),
                    'penalties_conceded': getattr(match_stats, 'penalties_conceded', 0),
                    'player_of_match': getattr(match_stats, 'player_of_match', False),
                    # Attack bonus stats
                    'shots_on_target': getattr(match_stats, 'shots_on_target', 0),
                    'successful_dribbles': getattr(match_stats, 'successful_dribbles', 0),
                    'entries_into_box': getattr(match_stats, 'entries_into_box', 0)
                }
            })
    
    # Calculate team points with updated scoring
    team_points = fantasy_scoring.calculate_team_points(players_with_stats, captain_id)
    
    return {
        'team_id': fantasy_team.id,
        'team_name': fantasy_team.name,
        'points': team_points,
        'matchday': matchday
    }

if __name__ == "__main__":
    # Test the scoring system
    logger.info("Testing Fantasy Scoring System...")
    
    # Example player stats
    test_player_stats = {
        'minutes_played': 90,
        'goals': 2,
        'assists': 1,
        'yellow_cards': 1,
        'clean_sheet': False
    }
    
    # Test scoring for different positions
    for position in ['GK', 'DEF', 'MID', 'FWD']:
        points = fantasy_scoring.calculate_player_points(test_player_stats, position)
        print(f"{position}: {points['total']} points")
        print(f"Breakdown: {points}")
        print()
