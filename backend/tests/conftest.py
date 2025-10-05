"""
Shared test fixtures and configuration for all tests.

This file is automatically discovered by pytest and provides
reusable fixtures for all test files.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from src.models import Base, User, Player, FantasyTeam, Matchday, FantasyLeague
from src.services.auth import AuthService
from faker import Faker

fake = Faker()
auth_service = AuthService()


# ============================================================================
# DATABASE FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def test_engine():
    """
    Create an in-memory SQLite database for testing.
    This is created once per test session.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_engine):
    """
    Create a fresh database session for each test.
    Automatically rolls back changes after each test.
    """
    TestSession = sessionmaker(bind=test_engine)
    session = TestSession()
    
    yield session
    
    # Cleanup: rollback any changes and close session
    session.rollback()
    session.close()


# ============================================================================
# USER FIXTURES
# ============================================================================

@pytest.fixture
def test_user(test_db: Session):
    """Create a test user in the database."""
    # Check if user already exists to prevent duplicates
    existing = test_db.query(User).filter(User.email == "test@example.com").first()
    if existing:
        return existing
    
    user = User(
        name="Test User",
        email="test@example.com",
        password_hash=auth_service.hash_password("testpassword123")
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture
def test_user_2(test_db: Session):
    """Create a second test user for multi-user tests."""
    user = User(
        name="Test User 2",
        email="test2@example.com",
        password_hash=auth_service.hash_password("testpassword123")
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


# ============================================================================
# PLAYER FIXTURES
# ============================================================================

@pytest.fixture
def test_players(test_db: Session):
    """Create a set of test players with different positions and prices."""
    players = [
        Player(
            name="Test Goalkeeper",
            team="Real Madrid",
            position="GK",
            price=5000000,
            is_active=True
        ),
        Player(
            name="Test Defender",
            team="Barcelona",
            position="DEF",
            price=10000000,
            is_active=True
        ),
        Player(
            name="Test Midfielder",
            team="Atletico Madrid",
            position="MID",
            price=15000000,
            is_active=True
        ),
        Player(
            name="Test Forward",
            team="Real Madrid",
            position="FWD",
            price=20000000,
            is_active=True
        ),
    ]
    
    for player in players:
        test_db.add(player)
    test_db.commit()
    
    for player in players:
        test_db.refresh(player)
    
    return players


@pytest.fixture
def expensive_player(test_db: Session):
    """Create an expensive test player."""
    player = Player(
        name="Expensive Star",
        team="Real Madrid",
        position="FWD",
        price=50000000,
        is_active=True
    )
    test_db.add(player)
    test_db.commit()
    test_db.refresh(player)
    return player


@pytest.fixture
def cheap_player(test_db: Session):
    """Create a cheap test player."""
    player = Player(
        name="Budget Player",
        team="Getafe",
        position="DEF",
        price=2000000,
        is_active=True
    )
    test_db.add(player)
    test_db.commit()
    test_db.refresh(player)
    return player


# ============================================================================
# FANTASY TEAM FIXTURES
# ============================================================================

@pytest.fixture
def test_team(test_db: Session, test_user):
    """Create a test fantasy team."""
    team = FantasyTeam(
        user_id=test_user.id,
        name="Test Fantasy Team",
        total_points=0,
        total_budget=150000000,  # 150M
        max_players=14
    )
    test_db.add(team)
    test_db.commit()
    test_db.refresh(team)
    return team


@pytest.fixture
def test_team_with_low_budget(test_db: Session, test_user):
    """Create a test team with low budget for testing budget limits."""
    team = FantasyTeam(
        user_id=test_user.id,
        name="Low Budget Team",
        total_points=0,
        total_budget=5000000,  # Only 5M
        max_players=14
    )
    test_db.add(team)
    test_db.commit()
    test_db.refresh(team)
    return team


# ============================================================================
# MATCHDAY FIXTURES
# ============================================================================

@pytest.fixture
def active_matchday(test_db: Session):
    """Create an active matchday."""
    from datetime import datetime, timedelta
    
    matchday = Matchday(
        matchday_number=1,
        season="2025-2026",
        free_transfers=2,
        start_date=datetime.now() - timedelta(days=1),
        end_date=datetime.now() + timedelta(days=6),
        deadline=datetime.now() + timedelta(days=2),
        is_active=True,
        is_finished=False,
        points_calculated=False
    )
    test_db.add(matchday)
    test_db.commit()
    test_db.refresh(matchday)
    return matchday


@pytest.fixture
def finished_matchday(test_db: Session):
    """Create a finished matchday."""
    from datetime import datetime, timedelta
    
    matchday = Matchday(
        matchday_number=2,
        season="2025-2026",
        free_transfers=2,
        start_date=datetime.now() - timedelta(days=14),
        end_date=datetime.now() - timedelta(days=7),
        deadline=datetime.now() - timedelta(days=9),
        is_active=False,
        is_finished=True,
        points_calculated=True
    )
    test_db.add(matchday)
    test_db.commit()
    test_db.refresh(matchday)
    return matchday


# ============================================================================
# LEAGUE FIXTURES
# ============================================================================

@pytest.fixture
def test_league(test_db: Session, test_user):
    """Create a test fantasy league."""
    from datetime import datetime, timedelta
    league = FantasyLeague(
        name="Test League",
        creator_id=test_user.id,
        max_participants=20,
        is_private=False,
        start_date=datetime.now(),
        end_date=datetime.now() + timedelta(days=365)
    )
    test_db.add(league)
    test_db.commit()
    test_db.refresh(league)
    return league


# ============================================================================
# MOCK FIXTURES
# ============================================================================

@pytest.fixture
def mock_scraper_response():
    """Mock HTML response from La Liga website."""
    return """
    <html>
        <body>
            <div class="player" data-name="Test Player">
                <span class="goals">2</span>
                <span class="assists">1</span>
                <span class="minutes">90</span>
            </div>
        </body>
    </html>
    """


# ============================================================================
# UTILITY FIXTURES
# ============================================================================

@pytest.fixture
def sample_player_stats():
    """Sample player statistics for testing scoring calculations."""
    return {
        'goals': 2,
        'assists': 1,
        'clean_sheets': 1,
        'yellow_cards': 1,
        'red_cards': 0,
        'minutes_played': 90,
        'saves': 0
    }
