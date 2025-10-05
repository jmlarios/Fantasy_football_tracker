"""
Unit tests for model properties and methods.

Consolidated test suite focusing on comprehensive coverage with fewer tests.
Each test validates multiple related scenarios for better efficiency.
"""

import pytest
from datetime import datetime, timedelta, timezone
from src.models import FantasyTeam, FantasyTeamPlayer, Matchday, TransferOffer, LeagueTeam, LeagueTeamPlayer


class TestTeamBudgetManagement:
    """Comprehensive tests for FantasyTeam and LeagueTeam budget calculations."""
    
    def test_fantasy_team_budget_calculations(self, test_db, test_team, test_players):
        """Test all FantasyTeam budget scenarios in one comprehensive test."""
        # Empty team has 0 budget used
        assert test_team.current_budget_used == 0.0
        
        # Set up test budget
        test_team.total_budget = 100.0
        assert test_team.remaining_budget == 100.0
        
        # Add players with different prices
        test_players[0].price = 10.5
        test_players[1].price = 15.0
        test_players[2].price = 8.75
        
        for i in range(3):
            team_player = FantasyTeamPlayer(
                fantasy_team_id=test_team.id,
                player_id=test_players[i].id,
                position_in_team='FWD' if i % 2 == 0 else 'MID',
                is_captain=(i == 0),
                is_vice_captain=False
            )
            test_db.add(team_player)
        
        test_db.commit()
        test_db.refresh(test_team)
        
        # Budget used should sum all player prices
        assert test_team.current_budget_used == 34.25  # 10.5 + 15.0 + 8.75
        assert test_team.remaining_budget == 65.75  # 100 - 34.25
        
        # Test transfer affordability scenarios
        assert test_team.can_afford_transfer(10.0, 5.0) is True  # Net 5: affordable
        assert test_team.can_afford_transfer(70.0, 0.0) is False  # Need 70, have 65.75
        assert test_team.can_afford_transfer(65.75, 0.0) is True  # Exactly enough
        assert test_team.can_afford_transfer(20.0, 30.0) is True  # Selling expensive (gain)
    
    def test_league_team_budget_calculations(self, test_db, test_team, test_league, test_players):
        """Test all LeagueTeam budget scenarios in one comprehensive test."""
        league_team = LeagueTeam(
            fantasy_team_id=test_team.id,
            league_id=test_league.id,
            total_budget=100.0
        )
        test_db.add(league_team)
        test_db.commit()
        
        # Empty league team has 0 budget used
        assert league_team.current_budget_used == 0.0
        assert league_team.remaining_budget == 100.0
        
        # Add players
        test_players[0].price = 12.5
        test_players[1].price = 18.0
        
        for i in range(2):
            league_player = LeagueTeamPlayer(
                league_team_id=league_team.id,
                player_id=test_players[i].id,
                league_id=test_league.id,
                position_in_team='FWD',
                is_captain=(i == 0),
                is_vice_captain=False
            )
            test_db.add(league_player)
        
        test_db.commit()
        test_db.refresh(league_team)
        
        # Verify budget calculations
        assert league_team.current_budget_used == 30.5
        assert league_team.remaining_budget == 69.5


class TestMatchdayTransferLock:
    """Comprehensive tests for Matchday transfer deadline properties."""
    
    def test_matchday_transfer_lock_states(self, test_db):
        """Test all matchday transfer lock scenarios in one comprehensive test."""
        now = datetime.now(timezone.utc)
        
        # Future deadline - not locked
        future_matchday = Matchday(
            matchday_number=99,
            season="2025-2026",
            deadline=now + timedelta(days=2, hours=3),
            start_date=now,
            end_date=now + timedelta(days=3)
        )
        test_db.add(future_matchday)
        test_db.commit()
        
        assert future_matchday.is_transfer_locked is False
        assert "days" in future_matchday.time_until_deadline
        assert "hours" in future_matchday.time_until_deadline
        
        # Past deadline - locked
        past_matchday = Matchday(
            matchday_number=100,
            season="2025-2026",
            deadline=now - timedelta(hours=1),
            start_date=now - timedelta(days=2),
            end_date=now + timedelta(days=1)
        )
        test_db.add(past_matchday)
        test_db.commit()
        
        assert past_matchday.is_transfer_locked is True
        assert past_matchday.time_until_deadline == "Transfer deadline passed"
        
        # Hours remaining - not locked
        hours_matchday = Matchday(
            matchday_number=101,
            season="2025-2026",
            deadline=now + timedelta(hours=5, minutes=30),
            start_date=now,
            end_date=now + timedelta(days=1)
        )
        test_db.add(hours_matchday)
        test_db.commit()
        
        assert hours_matchday.is_transfer_locked is False
        assert "hours" in hours_matchday.time_until_deadline
        assert "minutes" in hours_matchday.time_until_deadline
        assert "days" not in hours_matchday.time_until_deadline


class TestTransferOfferExpiry:
    """Comprehensive tests for TransferOffer expiry properties."""
    
    def test_transfer_offer_expiry_states(self, test_db, test_league, test_team, test_players):
        """Test all transfer offer expiry scenarios in one comprehensive test."""
        now = datetime.now(timezone.utc)
        
        # Future expiry - not expired
        future_offer = TransferOffer(
            league_id=test_league.id,
            from_team_id=test_team.id,
            to_team_id=test_team.id,
            player_id=test_players[0].id,
            offer_type='money',
            money_offered=10000000.0,
            status='pending',
            expires_at=now + timedelta(days=3, hours=2)
        )
        test_db.add(future_offer)
        test_db.commit()
        
        assert future_offer.is_expired is False
        assert "days" in future_offer.time_until_expiry
        assert "hours" in future_offer.time_until_expiry
        
        # Past expiry - expired
        expired_offer = TransferOffer(
            league_id=test_league.id,
            from_team_id=test_team.id,
            to_team_id=test_team.id,
            player_id=test_players[0].id,
            offer_type='money',
            money_offered=8000000.0,
            status='pending',
            expires_at=now - timedelta(hours=1)
        )
        test_db.add(expired_offer)
        test_db.commit()
        
        assert expired_offer.is_expired is True
        assert expired_offer.time_until_expiry == "Expired"
        
        # Accepted offer - not expired (status overrides time)
        accepted_offer = TransferOffer(
            league_id=test_league.id,
            from_team_id=test_team.id,
            to_team_id=test_team.id,
            player_id=test_players[0].id,
            offer_type='money',
            money_offered=5000000.0,
            status='accepted',
            expires_at=now - timedelta(hours=1)
        )
        test_db.add(accepted_offer)
        test_db.commit()
        
        assert accepted_offer.is_expired is False
        assert "Status: accepted" in accepted_offer.time_until_expiry
        
        # Hours remaining
        hours_offer = TransferOffer(
            league_id=test_league.id,
            from_team_id=test_team.id,
            to_team_id=test_team.id,
            player_id=test_players[0].id,
            offer_type='money',
            money_offered=7000000.0,
            status='pending',
            expires_at=now + timedelta(hours=6, minutes=15)
        )
        test_db.add(hours_offer)
        test_db.commit()
        
        assert hours_offer.is_expired is False
        assert "hours" in hours_offer.time_until_expiry
        assert "minutes" in hours_offer.time_until_expiry
        assert "days" not in hours_offer.time_until_expiry

