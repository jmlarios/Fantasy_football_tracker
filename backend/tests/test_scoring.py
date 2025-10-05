"""
Unit tests for the fantasy scoring system.

Consolidated test suite focusing on comprehensive coverage with fewer tests.
Each test validates multiple related scenarios for better efficiency.
"""

import pytest
from src.services.scoring import FantasyScoring, fantasy_scoring


class TestScoringRulesConfiguration:
    """Tests for scoring rules configuration and structure."""
    
    def test_scoring_rules_complete_structure(self):
        """Verify scoring rules have all required fields and correct values."""
        assert hasattr(fantasy_scoring, 'scoring_rules')
        rules = fantasy_scoring.scoring_rules
        
        # Verify structure
        assert isinstance(rules, dict)
        assert all(key in rules for key in ['goals', 'assists', 'cards', 'clean_sheet'])
        
        # Verify goal points by position
        assert rules['goals']['GK'] == 6
        assert rules['goals']['DEF'] == 6
        assert rules['goals']['MID'] == 5
        assert rules['goals']['FWD'] == 4
        
        # Verify other point values
        assert rules['assists']['goal_assist'] == 3
        assert rules['cards']['yellow'] == -1
        assert rules['cards']['red'] == -3


class TestBasicPointCalculation:
    """Comprehensive tests for appearance and basic point calculations."""
    
    def test_appearance_points_all_scenarios(self):
        """Test all appearance point scenarios in one test."""
        # 90 minutes = 1 point
        result_90 = fantasy_scoring.calculate_player_points({'minutes_played': 90}, 'FWD')
        assert result_90['match_played'] == 1.0
        
        # 60 minutes = 1 point
        result_60 = fantasy_scoring.calculate_player_points({'minutes_played': 60}, 'MID')
        assert result_60['match_played'] == 1.0
        
        # Less than 60 minutes = 0.5 points
        result_30 = fantasy_scoring.calculate_player_points({'minutes_played': 30}, 'DEF')
        assert result_30['match_played'] == 0.5
        
        # 0 minutes = 0 points
        result_0 = fantasy_scoring.calculate_player_points({'minutes_played': 0}, 'GK')
        assert result_0['match_played'] == 0.0
        
        # No stats = 0 points
        result_none = fantasy_scoring.calculate_player_points({}, 'FWD')
        assert result_none['total'] == 0.0


class TestGoalScoring:
    """Comprehensive tests for goal scoring by position."""
    
    def test_goals_by_position(self):
        """Test goal points for all positions in one comprehensive test."""
        base_stats = {'minutes_played': 90, 'goals': 1}
        
        # Forward: 4 points per goal
        fwd_result = fantasy_scoring.calculate_player_points(base_stats, 'FWD')
        assert fwd_result['goals'] == 4.0
        assert fwd_result['total'] == 5.0  # 1 appearance + 4 goal
        
        # Midfielder: 5 points per goal
        mid_result = fantasy_scoring.calculate_player_points(base_stats, 'MID')
        assert mid_result['goals'] == 5.0
        assert mid_result['total'] == 6.0  # 1 appearance + 5 goal
        
        # Defender: 6 points per goal
        def_result = fantasy_scoring.calculate_player_points(base_stats, 'DEF')
        assert def_result['goals'] == 6.0
        assert def_result['total'] == 7.0  # 1 appearance + 6 goal
        
        # Goalkeeper: 6 points per goal
        gk_result = fantasy_scoring.calculate_player_points(base_stats, 'GK')
        assert gk_result['goals'] == 6.0
        assert gk_result['total'] == 7.0  # 1 appearance + 6 goal
    
    def test_multiple_goals(self):
        """Test multiple goals scoring."""
        stats = {'minutes_played': 90, 'goals': 3}
        
        # Forward hat-trick: 3 goals × 4 points = 12 points
        result = fantasy_scoring.calculate_player_points(stats, 'FWD')
        assert result['goals'] == 12.0
        assert result['total'] == 13.0  # 1 appearance + 12 goals


class TestAssistsAndCleanSheets:
    """Comprehensive tests for assists and clean sheet bonuses."""
    
    def test_assists_all_types(self):
        """Test both goal assists and assists without goals."""
        # Goal assists: 3 points each
        goal_assist_stats = {'minutes_played': 90, 'goal_assists': 2}
        result1 = fantasy_scoring.calculate_player_points(goal_assist_stats, 'MID')
        assert result1['goal_assists'] == 6.0  # 2 × 3 points
        
        # Assist without goal: 1 point
        assist_no_goal_stats = {'minutes_played': 90, 'assist_without_goal': 1}
        result2 = fantasy_scoring.calculate_player_points(assist_no_goal_stats, 'MID')
        assert result2['assist_without_goal'] == 1.0
    
    def test_clean_sheet_by_position(self):
        """Test clean sheet points for all positions."""
        base_stats = {'minutes_played': 90, 'clean_sheet': True}
        
        # Goalkeeper: 4 points
        gk_result = fantasy_scoring.calculate_player_points(base_stats, 'GK', goals_conceded=0)
        assert gk_result['clean_sheet'] == 4.0
        
        # Defender: 4 points
        def_result = fantasy_scoring.calculate_player_points(base_stats, 'DEF', goals_conceded=0)
        assert def_result['clean_sheet'] == 4.0
        
        # Midfielder: 1 point
        mid_result = fantasy_scoring.calculate_player_points(base_stats, 'MID', goals_conceded=0)
        assert mid_result['clean_sheet'] == 1.0
        
        # Forward: 0 points
        fwd_result = fantasy_scoring.calculate_player_points(base_stats, 'FWD', goals_conceded=0)
        assert fwd_result.get('clean_sheet', 0.0) == 0.0


class TestCardsAndPenalties:
    """Comprehensive tests for cards and goalkeeper-specific scoring."""
    
    def test_card_penalties(self):
        """Test yellow and red card penalties."""
        # Yellow card: -1 point
        yellow_stats = {'minutes_played': 90, 'yellow_cards': 1}
        yellow_result = fantasy_scoring.calculate_player_points(yellow_stats, 'MID')
        assert yellow_result['yellow_cards'] == -1.0
        
        # Red card: -3 points
        red_stats = {'minutes_played': 90, 'red_cards': 1}
        red_result = fantasy_scoring.calculate_player_points(red_stats, 'MID')
        assert red_result['red_cards'] == -3.0
        
        # Multiple yellows
        multiple_stats = {'minutes_played': 90, 'yellow_cards': 2}
        multiple_result = fantasy_scoring.calculate_player_points(multiple_stats, 'DEF')
        assert multiple_result['yellow_cards'] == -2.0
    
    def test_goalkeeper_specific_scoring(self):
        """Test all goalkeeper-specific scoring categories."""
        # Saves: 1 point per 3 saves
        saves_stats = {'minutes_played': 90, 'saves': 6}
        saves_result = fantasy_scoring.calculate_player_points(saves_stats, 'GK')
        assert saves_result['saves'] == 2.0  # 6 / 3
        
        # Penalty save: 5 points
        penalty_stats = {'minutes_played': 90, 'penalties_saved': 1}
        penalty_result = fantasy_scoring.calculate_player_points(penalty_stats, 'GK')
        assert penalty_result['penalty_saved'] == 5.0
    
    def test_goals_conceded_by_position(self):
        """Test goals conceded penalties for defensive positions."""
        # Goalkeeper: -1 per 2 goals conceded
        gk_result = fantasy_scoring.calculate_player_points({'minutes_played': 90}, 'GK', goals_conceded=2)
        assert gk_result['goals_conceded'] == -1.0
        
        # Defender: -1 per 2 goals conceded
        def_result = fantasy_scoring.calculate_player_points({'minutes_played': 90}, 'DEF', goals_conceded=4)
        assert def_result['goals_conceded'] == -2.0  # 4 / 2
        
        # Midfielder: no penalty
        mid_result = fantasy_scoring.calculate_player_points({'minutes_played': 90}, 'MID', goals_conceded=4)
        assert mid_result['goals_conceded'] == 0.0


class TestComplexScenarios:
    """Comprehensive tests for complex multi-stat scenarios."""
    
    def test_striker_multiple_contributions(self):
        """Striker with hat-trick and assist."""
        stats = {'minutes_played': 90, 'goals': 3, 'goal_assists': 1}
        result = fantasy_scoring.calculate_player_points(stats, 'FWD')
        assert result['total'] == 16.0  # 1 appearance + 12 goals + 3 assist
    
    def test_defender_attacking_contribution(self):
        """Defender with goal and clean sheet."""
        stats = {'minutes_played': 90, 'goals': 1, 'clean_sheet': True}
        result = fantasy_scoring.calculate_player_points(stats, 'DEF', goals_conceded=0)
        assert result['total'] == 11.0  # 1 appearance + 6 goal + 4 clean sheet
    
    def test_goalkeeper_full_performance(self):
        """Goalkeeper with saves, clean sheet, and penalty save."""
        stats = {'minutes_played': 90, 'saves': 6, 'penalties_saved': 1, 'clean_sheet': True}
        result = fantasy_scoring.calculate_player_points(stats, 'GK', goals_conceded=0)
        assert result['total'] == 12.0  # 1 appearance + 4 clean sheet + 2 saves + 5 penalty
    
    def test_player_with_cards_and_goals(self):
        """Player scoring but also receiving cards."""
        stats = {'minutes_played': 90, 'goals': 2, 'yellow_cards': 1}
        result = fantasy_scoring.calculate_player_points(stats, 'FWD')
        assert result['total'] == 8.0  # 1 appearance + 8 goals - 1 yellow = 8 (not 9)


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_edge_cases_comprehensive(self):
        """Test various edge cases in one comprehensive test."""
        # Empty stats
        empty_result = fantasy_scoring.calculate_player_points({}, 'MID')
        assert empty_result['total'] == 0.0
        
        # Missing minutes defaults to 0 - no match points, only stat points
        no_minutes_result = fantasy_scoring.calculate_player_points({'goals': 1}, 'FWD')
        assert no_minutes_result['match_played'] == 0.0
        assert no_minutes_result['goals'] == 4.0
        
        # Total includes all categories
        multi_stat_result = fantasy_scoring.calculate_player_points(
            {'minutes_played': 90, 'goals': 1, 'goal_assists': 1, 'yellow_cards': 1},
            'FWD'
        )
        assert multi_stat_result['total'] == 7.0  # 1 + 4 + 3 - 1
