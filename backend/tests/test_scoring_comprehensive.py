"""
Comprehensive tests for untested parts of FantasyScoring instance methods.

This file focuses on covering the untested features including:
- Penalty won/committed
- Defensive bonus (balls recovered, clearances)
- Attack bonus (shots on target, dribbles, box entries)
- Team points calculation
- Formation validation
- Captain multiplier in team context
"""

import pytest
from src.services.scoring import FantasyScoring


class TestPenaltyActions:
    """Comprehensive tests for penalty-related scoring."""
    
    def test_penalty_scoring_comprehensive(self):
        """Test all penalty scenarios: won (single/multiple) and committed (single/multiple)."""
        scoring = FantasyScoring()
        
        # Penalty won: 2 points each
        won_single = scoring.calculate_player_points({'minutes_played': 90, 'penalties_won': 1}, 'FWD')
        assert won_single['penalty_won'] == 2.0
        
        won_multiple = scoring.calculate_player_points({'minutes_played': 90, 'penalties_won': 3}, 'FWD')
        assert won_multiple['penalty_won'] == 6.0
        
        # Penalty committed: -1 point each
        committed_single = scoring.calculate_player_points({'minutes_played': 90, 'penalties_committed': 1}, 'DEF')
        assert committed_single['penalty_committed'] == -1.0
        
        committed_multiple = scoring.calculate_player_points({'minutes_played': 90, 'penalties_committed': 2}, 'DEF')
        assert committed_multiple['penalty_committed'] == -2.0


class TestDefensiveBonus:
    """Comprehensive tests for defensive bonus stats."""
    
    def test_balls_recovered_all_scenarios(self):
        """Test balls recovered: threshold (5), multiple (10), under threshold (4)."""
        scoring = FantasyScoring()
        
        # Threshold: every 5 = 1 point
        threshold = scoring.calculate_player_points({'minutes_played': 90, 'balls_recovered': 5}, 'DEF')
        assert threshold['balls_recovered'] == 1.0
        
        # Multiple groups: 10 = 2 points
        multiple = scoring.calculate_player_points({'minutes_played': 90, 'balls_recovered': 10}, 'MID')
        assert multiple['balls_recovered'] == 2.0
        
        # Under threshold: 4 = 0 points
        under = scoring.calculate_player_points({'minutes_played': 90, 'balls_recovered': 4}, 'DEF')
        assert under['balls_recovered'] == 0.0
    
    def test_clearances_and_combined_defensive(self):
        """Test clearances (every 3 = 1 point) and combined defensive bonuses."""
        scoring = FantasyScoring()
        
        # Clearances threshold: 3 = 1 point
        threshold = scoring.calculate_player_points({'minutes_played': 90, 'clearances': 3}, 'DEF')
        assert threshold['clearances'] == 1.0
        
        # Multiple clearances: 9 = 3 points
        multiple = scoring.calculate_player_points({'minutes_played': 90, 'clearances': 9}, 'DEF')
        assert multiple['clearances'] == 3.0
        
        # Under threshold: 2 = 0 points
        under = scoring.calculate_player_points({'minutes_played': 90, 'clearances': 2}, 'DEF')
        assert under['clearances'] == 0.0
        
        # Combined: both stats stack
        combined = scoring.calculate_player_points({
            'minutes_played': 90,
            'balls_recovered': 10,  # 2 points
            'clearances': 6         # 2 points
        }, 'DEF')
        assert combined['balls_recovered'] == 2.0
        assert combined['clearances'] == 2.0


class TestAttackBonus:
    """Comprehensive tests for attack bonus stats."""
    
    def test_shots_and_dribbles_comprehensive(self):
        """Test shots on target and successful dribbles (every 2 = 1 point)."""
        scoring = FantasyScoring()
        
        # Shots on target: threshold/multiple/under
        shots_threshold = scoring.calculate_player_points({'minutes_played': 90, 'shots_on_target': 2}, 'FWD')
        assert shots_threshold['shots_on_target'] == 1.0
        
        shots_multiple = scoring.calculate_player_points({'minutes_played': 90, 'shots_on_target': 6}, 'FWD')
        assert shots_multiple['shots_on_target'] == 3.0
        
        shots_under = scoring.calculate_player_points({'minutes_played': 90, 'shots_on_target': 1}, 'FWD')
        assert shots_under['shots_on_target'] == 0.0
        
        # Successful dribbles: threshold/multiple
        dribbles_threshold = scoring.calculate_player_points({'minutes_played': 90, 'successful_dribbles': 2}, 'MID')
        assert dribbles_threshold['successful_dribbles'] == 1.0
        
        dribbles_multiple = scoring.calculate_player_points({'minutes_played': 90, 'successful_dribbles': 8}, 'MID')
        assert dribbles_multiple['successful_dribbles'] == 4.0
    
    def test_box_entries_and_combined_attack(self):
        """Test entries into box and combined attack bonuses."""
        scoring = FantasyScoring()
        
        # Entries into box: threshold/multiple
        box_threshold = scoring.calculate_player_points({'minutes_played': 90, 'entries_into_box': 2}, 'FWD')
        assert box_threshold['entries_into_box'] == 1.0
        
        box_multiple = scoring.calculate_player_points({'minutes_played': 90, 'entries_into_box': 5}, 'FWD')
        assert box_multiple['entries_into_box'] == 2.0
        
        # Combined: all attack bonuses stack
        combined = scoring.calculate_player_points({
            'minutes_played': 90,
            'shots_on_target': 4,      # 2 points
            'successful_dribbles': 6,  # 3 points
            'entries_into_box': 4      # 2 points
        }, 'FWD')
        assert combined['shots_on_target'] == 2.0
        assert combined['successful_dribbles'] == 3.0
        assert combined['entries_into_box'] == 2.0


class TestAssistWithoutGoal:
    """Comprehensive tests for assist_without_goal scoring."""
    
    def test_assist_without_goal_comprehensive(self):
        """Test assist without goal: single (1pt), multiple (3pts), combined with goal assists."""
        scoring = FantasyScoring()
        
        # Single assist without goal: 1 point
        single = scoring.calculate_player_points({'minutes_played': 90, 'assist_without_goal': 1}, 'MID')
        assert single['assist_without_goal'] == 1.0
        
        # Multiple assists without goal: 3 points
        multiple = scoring.calculate_player_points({'minutes_played': 90, 'assist_without_goal': 3}, 'MID')
        assert multiple['assist_without_goal'] == 3.0
        
        # Combined with goal assists
        combined = scoring.calculate_player_points({
            'minutes_played': 90,
            'assists': 2,              # Goal assists = 6 points
            'assist_without_goal': 1   # 1 point
        }, 'FWD')
        assert combined['goal_assists'] == 6.0
        assert combined['assist_without_goal'] == 1.0


class TestTeamPointsCalculation:
    """Tests for calculate_team_points method."""
    
    def test_basic_team_points(self):
        """Team points sum all player points."""
        scoring = FantasyScoring()
        team_players = [
            {
                'id': 1,
                'position': 'GK',
                'stats': {'minutes_played': 90},
                'goals_conceded': 0
            },
            {
                'id': 2,
                'position': 'DEF',
                'stats': {'minutes_played': 90},
                'goals_conceded': 0
            }
        ]
        result = scoring.calculate_team_points(team_players)
        assert result['players_played'] == 2
        assert result['total_points'] == 2.0  # Each player 1 point
    
    def test_captain_multiplier(self):
        """Captain gets 2x points."""
        scoring = FantasyScoring()
        team_players = [
            {
                'id': 1,
                'position': 'FWD',
                'stats': {
                    'minutes_played': 90,
                    'goals': 2
                },
                'goals_conceded': 0
            }
        ]
        result = scoring.calculate_team_points(team_players, captain_id=1)
        
        # Player points: 1 (appearance) + 8 (2 goals * 4) = 9
        # Captain bonus: 9 * (2 - 1) = 9
        # Total: 9 * 2 = 18
        assert result['captain_bonus'] == 9.0
        assert result['total_points'] == 18.0
    
    def test_non_captain_player(self):
        """Non-captain player has 1x multiplier."""
        scoring = FantasyScoring()
        team_players = [
            {
                'id': 1,
                'position': 'MID',
                'stats': {'minutes_played': 90, 'goals': 1},
                'goals_conceded': 0
            },
            {
                'id': 2,
                'position': 'FWD',
                'stats': {'minutes_played': 90},
                'goals_conceded': 0
            }
        ]
        result = scoring.calculate_team_points(team_players, captain_id=1)
        
        # Find non-captain player
        non_captain = [p for p in result['players'] if p['player_id'] == 2][0]
        assert non_captain['multiplier'] == 1.0
    
    def test_players_not_played_excluded(self):
        """Players with 0 minutes don't count."""
        scoring = FantasyScoring()
        team_players = [
            {
                'id': 1,
                'position': 'GK',
                'stats': {'minutes_played': 90},
                'goals_conceded': 0
            },
            {
                'id': 2,
                'position': 'DEF',
                'stats': {'minutes_played': 0},  # Didn't play
                'goals_conceded': 0
            }
        ]
        result = scoring.calculate_team_points(team_players)
        assert result['players_played'] == 1
        assert len(result['players']) == 1
    
    def test_formation_valid(self):
        """Valid formation detected."""
        scoring = FantasyScoring()
        team_players = [
            {'id': 1, 'position': 'GK', 'stats': {'minutes_played': 90}, 'goals_conceded': 0},
            {'id': 2, 'position': 'DEF', 'stats': {'minutes_played': 90}, 'goals_conceded': 0},
            {'id': 3, 'position': 'DEF', 'stats': {'minutes_played': 90}, 'goals_conceded': 0},
            {'id': 4, 'position': 'DEF', 'stats': {'minutes_played': 90}, 'goals_conceded': 0},
            {'id': 5, 'position': 'MID', 'stats': {'minutes_played': 90}, 'goals_conceded': 0},
            {'id': 6, 'position': 'MID', 'stats': {'minutes_played': 90}, 'goals_conceded': 0},
            {'id': 7, 'position': 'FWD', 'stats': {'minutes_played': 90}, 'goals_conceded': 0},
        ]
        result = scoring.calculate_team_points(team_players)
        assert result['formation_valid'] is True
    
    def test_formation_invalid_no_gk(self):
        """Formation invalid without goalkeeper."""
        scoring = FantasyScoring()
        team_players = [
            {'id': 2, 'position': 'DEF', 'stats': {'minutes_played': 90}, 'goals_conceded': 0},
            {'id': 3, 'position': 'DEF', 'stats': {'minutes_played': 90}, 'goals_conceded': 0},
            {'id': 4, 'position': 'DEF', 'stats': {'minutes_played': 90}, 'goals_conceded': 0},
            {'id': 5, 'position': 'MID', 'stats': {'minutes_played': 90}, 'goals_conceded': 0},
            {'id': 6, 'position': 'MID', 'stats': {'minutes_played': 90}, 'goals_conceded': 0},
            {'id': 7, 'position': 'FWD', 'stats': {'minutes_played': 90}, 'goals_conceded': 0},
        ]
        result = scoring.calculate_team_points(team_players)
        assert result['formation_valid'] is False
    
    def test_formation_invalid_not_enough_defenders(self):
        """Formation invalid with <3 defenders."""
        scoring = FantasyScoring()
        team_players = [
            {'id': 1, 'position': 'GK', 'stats': {'minutes_played': 90}, 'goals_conceded': 0},
            {'id': 2, 'position': 'DEF', 'stats': {'minutes_played': 90}, 'goals_conceded': 0},
            {'id': 3, 'position': 'DEF', 'stats': {'minutes_played': 90}, 'goals_conceded': 0},
            {'id': 5, 'position': 'MID', 'stats': {'minutes_played': 90}, 'goals_conceded': 0},
            {'id': 6, 'position': 'MID', 'stats': {'minutes_played': 90}, 'goals_conceded': 0},
            {'id': 7, 'position': 'FWD', 'stats': {'minutes_played': 90}, 'goals_conceded': 0},
        ]
        result = scoring.calculate_team_points(team_players)
        assert result['formation_valid'] is False


class TestGetScoringRules:
    """Comprehensive test for get_scoring_rules method."""
    
    def test_get_scoring_rules_comprehensive(self):
        """Test get_scoring_rules returns dict with all required keys and correct captain multiplier."""
        scoring = FantasyScoring()
        rules = scoring.get_scoring_rules()
        
        # Returns dictionary
        assert isinstance(rules, dict)
        
        # Contains all required sections
        assert 'match_played' in rules
        assert 'goals' in rules
        assert 'assists' in rules
        assert 'clean_sheet' in rules
        assert 'cards' in rules
        assert 'defensive_bonus' in rules
        assert 'attack_bonus' in rules
        assert 'captain_multiplier' in rules
        
        # Captain multiplier is 2.0
        assert rules['captain_multiplier'] == 2.0


class TestComplexScenarios:
    """Tests for complex real-world scenarios."""
    
    def test_complete_midfielder_performance(self):
        """Midfielder with all stats."""
        scoring = FantasyScoring()
        stats = {
            'minutes_played': 90,
            'goals': 1,                    # 5
            'assists': 1,                  # 3
            'clean_sheet': True,           # 1
            'balls_recovered': 10,         # 2
            'successful_dribbles': 4,      # 2
            'shots_on_target': 2           # 1
        }
        result = scoring.calculate_player_points(stats, 'MID', goals_conceded=0)
        
        # 1 + 5 + 3 + 1 + 2 + 2 + 1 = 15
        assert result['total'] == 15.0
    
    def test_goalkeeper_exceptional_game(self):
        """Goalkeeper with saves and clean sheet."""
        scoring = FantasyScoring()
        stats = {
            'minutes_played': 90,
            'saves': 9,                    # 3 (9//3)
            'penalties_saved': 1,          # 5
            'clean_sheet': True            # 4
        }
        result = scoring.calculate_player_points(stats, 'GK', goals_conceded=0)
        
        # 1 + 3 + 5 + 4 = 13
        assert result['total'] == 13.0
    
    def test_defender_dirty_game(self):
        """Defender with yellow card, red card, penalties."""
        scoring = FantasyScoring()
        stats = {
            'minutes_played': 90,
            'yellow_cards': 1,             # -1
            'red_cards': 1,                # -3
            'penalties_committed': 1       # -1
        }
        result = scoring.calculate_player_points(stats, 'DEF', goals_conceded=0)
        
        # 1 - 1 - 3 - 1 = -4
        assert result['total'] == -4.0
    
    def test_forward_hat_trick_with_bonuses(self):
        """Forward with hat-trick and attack bonuses."""
        scoring = FantasyScoring()
        stats = {
            'minutes_played': 90,
            'goals': 3,                    # 12 (3*4)
            'assists': 1,                  # 3
            'shots_on_target': 6,          # 3 (6//2)
            'entries_into_box': 4,         # 2 (4//2)
            'penalties_won': 1             # 2
        }
        result = scoring.calculate_player_points(stats, 'FWD')
        
        # 1 + 12 + 3 + 3 + 2 + 2 = 23
        assert result['total'] == 23.0


class TestValidateTeamFormation:
    """Comprehensive tests for validate_team_formation method."""
    
    def test_valid_formations(self):
        """Test 4-4-2, 4-3-3, and 3-5-2 formations are all valid."""
        scoring = FantasyScoring()
        
        # 4-4-2 formation
        team_442 = [
            {'position': 'GK'},
            {'position': 'DEF'}, {'position': 'DEF'}, {'position': 'DEF'}, {'position': 'DEF'},
            {'position': 'MID'}, {'position': 'MID'}, {'position': 'MID'}, {'position': 'MID'},
            {'position': 'FWD'}, {'position': 'FWD'}
        ]
        result_442 = scoring.validate_team_formation(team_442)
        assert result_442['is_valid'] is True
        assert result_442['position_counts'] == {'GK': 1, 'DEF': 4, 'MID': 4, 'FWD': 2}
        assert result_442['total_players'] == 11
        assert len(result_442['errors']) == 0
        
        # 4-3-3 formation
        team_433 = [
            {'position': 'GK'},
            {'position': 'DEF'}, {'position': 'DEF'}, {'position': 'DEF'}, {'position': 'DEF'},
            {'position': 'MID'}, {'position': 'MID'}, {'position': 'MID'},
            {'position': 'FWD'}, {'position': 'FWD'}, {'position': 'FWD'}
        ]
        result_433 = scoring.validate_team_formation(team_433)
        assert result_433['is_valid'] is True
        
        # 3-5-2 formation
        team_352 = [
            {'position': 'GK'},
            {'position': 'DEF'}, {'position': 'DEF'}, {'position': 'DEF'},
            {'position': 'MID'}, {'position': 'MID'}, {'position': 'MID'}, {'position': 'MID'}, {'position': 'MID'},
            {'position': 'FWD'}, {'position': 'FWD'}
        ]
        result_352 = scoring.validate_team_formation(team_352)
        assert result_352['is_valid'] is True
    
    def test_invalid_goalkeeper_violations(self):
        """Test invalid formations: no GK, two GKs."""
        scoring = FantasyScoring()
        
        # No goalkeeper
        no_gk = [
            {'position': 'DEF'}, {'position': 'DEF'}, {'position': 'DEF'}, {'position': 'DEF'},
            {'position': 'MID'}, {'position': 'MID'}, {'position': 'MID'}, {'position': 'MID'},
            {'position': 'FWD'}, {'position': 'FWD'}, {'position': 'FWD'}
        ]
        result_no_gk = scoring.validate_team_formation(no_gk)
        assert result_no_gk['is_valid'] is False
        assert any('GK' in error for error in result_no_gk['errors'])
        
        # Two goalkeepers
        two_gk = [
            {'position': 'GK'}, {'position': 'GK'},
            {'position': 'DEF'}, {'position': 'DEF'}, {'position': 'DEF'},
            {'position': 'MID'}, {'position': 'MID'}, {'position': 'MID'},
            {'position': 'FWD'}, {'position': 'FWD'}, {'position': 'FWD'}
        ]
        result_two_gk = scoring.validate_team_formation(two_gk)
        assert result_two_gk['is_valid'] is False
        assert any('GK' in error and 'Maximum' in error for error in result_two_gk['errors'])
    
    def test_invalid_position_violations(self):
        """Test invalid formations: wrong number of DEF/MID/FWD."""
        scoring = FantasyScoring()
        
        # Only 2 defenders (need 3+)
        few_def = [
            {'position': 'GK'},
            {'position': 'DEF'}, {'position': 'DEF'},
            {'position': 'MID'}, {'position': 'MID'}, {'position': 'MID'}, {'position': 'MID'},
            {'position': 'FWD'}, {'position': 'FWD'}, {'position': 'FWD'}, {'position': 'FWD'}
        ]
        result_few_def = scoring.validate_team_formation(few_def)
        assert result_few_def['is_valid'] is False
        assert any('DEF' in error and 'least' in error for error in result_few_def['errors'])
        
        # 6 defenders (max 5)
        many_def = [
            {'position': 'GK'},
            {'position': 'DEF'}, {'position': 'DEF'}, {'position': 'DEF'}, 
            {'position': 'DEF'}, {'position': 'DEF'}, {'position': 'DEF'},
            {'position': 'MID'}, {'position': 'MID'},
            {'position': 'FWD'}, {'position': 'FWD'}
        ]
        result_many_def = scoring.validate_team_formation(many_def)
        assert result_many_def['is_valid'] is False
        assert any('DEF' in error and 'Maximum' in error for error in result_many_def['errors'])
        
        # Only 1 midfielder (need 2+)
        few_mid = [
            {'position': 'GK'},
            {'position': 'DEF'}, {'position': 'DEF'}, {'position': 'DEF'}, {'position': 'DEF'},
            {'position': 'MID'},
            {'position': 'FWD'}, {'position': 'FWD'}, {'position': 'FWD'}, 
            {'position': 'FWD'}, {'position': 'FWD'}
        ]
        result_few_mid = scoring.validate_team_formation(few_mid)
        assert result_few_mid['is_valid'] is False
        assert any('MID' in error for error in result_few_mid['errors'])
        
        # No forwards (need 1+)
        no_fwd = [
            {'position': 'GK'},
            {'position': 'DEF'}, {'position': 'DEF'}, {'position': 'DEF'}, {'position': 'DEF'},
            {'position': 'MID'}, {'position': 'MID'}, {'position': 'MID'}, 
            {'position': 'MID'}, {'position': 'MID'}, {'position': 'MID'}
        ]
        result_no_fwd = scoring.validate_team_formation(no_fwd)
        assert result_no_fwd['is_valid'] is False
        assert any('FWD' in error for error in result_no_fwd['errors'])
        
        # 4 forwards (max 3)
        many_fwd = [
            {'position': 'GK'},
            {'position': 'DEF'}, {'position': 'DEF'}, {'position': 'DEF'},
            {'position': 'MID'}, {'position': 'MID'}, {'position': 'MID'},
            {'position': 'FWD'}, {'position': 'FWD'}, {'position': 'FWD'}, {'position': 'FWD'}
        ]
        result_many_fwd = scoring.validate_team_formation(many_fwd)
        assert result_many_fwd['is_valid'] is False
        assert any('FWD' in error and 'Maximum' in error for error in result_many_fwd['errors'])
    
    def test_invalid_player_count(self):
        """Test invalid formations: wrong total player count."""
        scoring = FantasyScoring()
        
        # Too many players (12)
        too_many = [
            {'position': 'GK'},
            {'position': 'DEF'}, {'position': 'DEF'}, {'position': 'DEF'}, {'position': 'DEF'},
            {'position': 'MID'}, {'position': 'MID'}, {'position': 'MID'}, {'position': 'MID'},
            {'position': 'FWD'}, {'position': 'FWD'}, {'position': 'FWD'}
        ]
        result_many = scoring.validate_team_formation(too_many)
        assert result_many['is_valid'] is False
        assert result_many['total_players'] == 12
        assert any('11 players' in error for error in result_many['errors'])
        
        # Too few players (8)
        too_few = [
            {'position': 'GK'},
            {'position': 'DEF'}, {'position': 'DEF'}, {'position': 'DEF'},
            {'position': 'MID'}, {'position': 'MID'},
            {'position': 'FWD'}, {'position': 'FWD'}
        ]
        result_few = scoring.validate_team_formation(too_few)
        assert result_few['is_valid'] is False
        assert result_few['total_players'] == 8
        assert any('11 players' in error for error in result_few['errors'])
    
    def test_validation_result_structure(self):
        """Validation result and requirements have correct structure."""
        scoring = FantasyScoring()
        team = [{'position': 'GK'} for _ in range(11)]
        result = scoring.validate_team_formation(team)
        
        # Result structure
        assert 'is_valid' in result
        assert 'errors' in result
        assert 'position_counts' in result
        assert 'requirements' in result
        assert 'total_players' in result
        assert isinstance(result['errors'], list)
        assert isinstance(result['position_counts'], dict)
        
        # Requirements structure
        req = result['requirements']
        assert 'GK' in req
        assert 'DEF' in req
        assert 'MID' in req
        assert 'FWD' in req
        
        for pos_req in req.values():
            assert 'min' in pos_req
            assert 'max' in pos_req
