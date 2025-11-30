"""Tests covering matchday aggregation helpers in scoring service."""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.services import scoring
from src.services.scoring import process_team_matchday
from src.models import FantasyTeamPlayer, Player, MatchPlayerStats, Match


class _FakeQuery:
    """Minimal SQLAlchemy-like query helper for deterministic data."""

    def __init__(self, records):
        self._records = list(records)

    def filter(self, *args, **kwargs):
        return self

    def join(self, *args, **kwargs):
        return self

    def all(self):
        return list(self._records)

    def first(self):
        return self._records[0] if self._records else None


def test_calculate_matchday_points_aggregates_results(monkeypatch):
    """Verifies calculate_matchday_points pulls teams and aggregates per-team results."""
    db = MagicMock()
    fantasy_team = SimpleNamespace(id=1, name="Leaders FC")

    query_mock = MagicMock()
    query_mock.all.return_value = [fantasy_team]
    db.query.return_value = query_mock

    def fake_process(session, team, matchday):
        assert session is db
        assert team is fantasy_team
        assert matchday == 7
        return {"team_id": team.id, "points": {"total_points": 15.0}}

    monkeypatch.setattr(scoring, "process_team_matchday", fake_process)

    result = scoring.calculate_matchday_points(db, matchday=7)

    assert result["matchday"] == 7
    assert result["teams_processed"] == 1
    assert result["teams"][0]["team_id"] == 1
    assert result["teams"][0]["points"]["total_points"] == 15.0


def test_process_team_matchday_builds_player_payload(monkeypatch):
    """Ensures process_team_matchday assembles stats and delegates to FantasyScoring."""
    db = MagicMock()
    fantasy_team = SimpleNamespace(id=42, name="Test XI")

    team_player = SimpleNamespace(fantasy_team_id=42, player_id=10, is_captain=True)
    player = SimpleNamespace(id=10, name="Playmaker", position="MID", team="Team A")
    match_stats = SimpleNamespace(
        minutes_played=90,
        goals=1,
        assists=1,
        yellow_cards=0,
        red_cards=0,
        clean_sheet=True,
        saves=0,
        own_goals=0,
        penalties_missed=0,
        penalties_saved=0,
        ball_recoveries=10,
        penalties_won=1,
        penalties_conceded=0,
        player_of_match=False,
        shots_on_target=3,
        successful_dribbles=4,
        entries_into_box=4,
    )
    match = SimpleNamespace(
        matchday=1,
        home_team="Team A",
        away_team="Team B",
        home_score=2,
        away_score=0,
        is_finished=True,
    )

    def query_side_effect(model):
        if model is FantasyTeamPlayer:
            return _FakeQuery([team_player])
        if model is Player:
            return _FakeQuery([player])
        if model is MatchPlayerStats:
            return _FakeQuery([match_stats])
        if model is Match:
            return _FakeQuery([match])
        return _FakeQuery([])

    db.query.side_effect = query_side_effect

    result = process_team_matchday(db, fantasy_team, matchday=1)

    assert result["team_id"] == 42
    assert result["matchday"] == 1
    assert result["points"]["players_played"] == 1
    player_entry = result["points"]["players"][0]
    assert player_entry["player_id"] == 10
    assert player_entry["multiplier"] == 2.0  # captain gets double points
    breakdown = player_entry["breakdown"]
    assert breakdown["goal_assists"] == 3.0  # assist counted
    assert breakdown["balls_recovered"] == 2.0  # 10 recoveries => 2 points
    assert result["points"]["formation_valid"] is False  # only one active player
