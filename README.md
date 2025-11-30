# Fantasy Football Tracker

A full-stack fantasy football application for managing LaLiga fantasy leagues, teams, and player statistics. Built with FastAPI, React, and PostgreSQL, designed to run seamlessly with Docker.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start with Docker](#quick-start-with-docker)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Fantasy Points System](#fantasy-points-system)
- [Testing](#testing)

## Features

### User Management

- User authentication and registration with secure password hashing (bcrypt)
- Session-based authentication

### Fantasy Teams

- Create and manage multiple fantasy teams
- Select players from LaLiga teams
- Set captains and vice-captains (2x points multiplier)
- Formation validation (GK: 1, DEF: 3-5, MID: 2-5, FWD: 1-3)
- Budget management system
- Real-time team points calculation after matchdays

### Leagues

- Create public and private leagues
- Join leagues via invite codes
- Compete against friends
- League leaderboards and standings
- League team management with custom team names

### Player Stats & Scoring

- Matchday player statistics scraped from FBref
- Comprehensive fantasy points system:
  - Match participation points
  - Goals (position-weighted: GK/DEF: 6, MID: 5, FWD: 4)
  - Assists (all types: 3 points)
  - Clean sheets (GK/DEF: 4 points)
  - Saves (GK: 1 point per 3 saves)
  - Cards and penalties (negative points)
  - Defensive bonuses (clearances, recoveries)
  - Attacking bonuses (shots, dribbles)
- Matchday processing and point updates
- Automatic cumulative stats updates

### Transfers

- Player transfer system
- Transfer penalties for exceeding limits
- Transfer lock during active matchdays
- Transfer history tracking
- Peer-to-peer transfer offers

## Tech Stack

### Backend

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Relational database
- **Pydantic** - Data validation
- **BeautifulSoup4** - Web scraping for player stats
- **bcrypt** - Password hashing
- **pytest** - Testing framework (66 tests, 88% coverage)

### Frontend

- **React 18** - UI library
- **TypeScript** - Type-safe JavaScript
- **React Router** - Client-side routing
- **Axios** - HTTP client
- **React Hook Form** - Form management
- **Vite** - Build tool and dev server

### Infrastructure

- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Frontend web server
- **PostgreSQL** - Database (containerized)

## Quick Start with Docker

**This application is designed to run with Docker. Follow these steps to get started quickly.**

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running
- Git

### Installation & Running

1. **Clone the repository**

   ```bash
   git clone https://github.com/jmlarios/Fantasy_football_tracker.git
   cd Fantasy_football_tracker
   ```
2. **Set up environment variables** (Optional - defaults are provided)

   Create a `.env` file in the `backend/` directory if you want to customize:

   ```env
   DATABASE_URL=postgresql://fantasy:football@db:5432/tracker
   SECRET_KEY=your-secret-key-here
   ```
3. **Build and run with Docker Compose**

   ```bash
   docker-compose up --build
   ```

   This single command will:

   - Build the backend (FastAPI) container
   - Build the frontend (React) container
   - Start a PostgreSQL database container
   - Create the database schema automatically
   - Connect all services together
4. **Access the application**

   - **Frontend**: http://localhost:3000
   - **Backend API**: http://localhost:5000
   - **API Documentation**: http://localhost:5000/docs (interactive Swagger UI)
   - **Database**: localhost:5432 (PostgreSQL)

## Project Structure

```
Fantasy_football_tracker/
├── backend/
│   ├── app.py                      # FastAPI application entry point
│   ├── config.py                   # Configuration management
│   ├── db_init.py                  # Database initialization
│   ├── requirements.txt            # Python dependencies
│   ├── pytest.ini                  # Test configuration
│   ├── Dockerfile                  # Backend container config
│   ├── src/
│   │   ├── models.py               # SQLAlchemy database models
│   │   ├── routes.py               # API endpoints
│   │   ├── middleware/
│   │   │   └── session.py          # Session management
│   │   └── services/
│   │       ├── auth.py             # Authentication service
│   │       ├── fantasy_team.py     # Team management
│   │       ├── league_service.py   # League operations
│   │       ├── scoring.py          # Points calculation
│   │       ├── laliga_scraper.py   # FBref web scraper
│   │       ├── matchday_processor.py # Matchday workflow
│   │       └── team_transfer_service.py # Transfer system
│   ├── tests/
│   │   ├── conftest.py             # Test fixtures
│   │   ├── test_auth.py            # Auth tests
│   │   ├── test_models.py          # Model tests
│   │   ├── test_scoring.py         # Scoring tests
│   │   └── test_scoring_comprehensive.py
│   └── scripts/
│       └── update_player_stats_from_matchdays.py
├── frontend/
│   ├── src/
│   │   ├── App.tsx                 # Main app component
│   │   ├── main.tsx                # Entry point
│   │   ├── components/
│   │   │   ├── Dashboard.tsx       # User dashboard
│   │   │   ├── MyFantasyLeagues.tsx # League list
│   │   │   ├── auth/
│   │   │   │   ├── LoginForm.tsx
│   │   │   │   └── RegisterForm.tsx
│   │   │   ├── fantasy/
│   │   │   │   ├── CreateTeamModal.tsx
│   │   │   │   ├── FantasyTeamsList.tsx
│   │   │   │   ├── PlayerBrowser.tsx
│   │   │   │   └── TeamDetailPage.tsx
│   │   │   ├── leagues/
│   │   │   │   ├── LeagueManager.tsx
│   │   │   │   └── LeagueTeamView.tsx
│   │   │   └── transfers/
│   │   │       ├── TransferPage.tsx
│   │   │       ├── UserTransferMarket.tsx
│   │   │       └── TransferOffers.tsx
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx     # Auth state management
│   │   ├── services/
│   │   │   ├── api.ts              # API client
│   │   │   ├── authService.ts      # Auth API calls
│   │   │   └── leagueService.ts    # League API calls
│   │   └── types/
│   │       ├── auth.ts             # Auth types
│   │       └── fantasy.ts          # Fantasy types
│   ├── package.json
│   ├── vite.config.ts
│   ├── nginx.conf                  # Nginx configuration
│   └── Dockerfile                  # Frontend container config
├── docker-compose.yml              # Multi-container setup
└── README.md

```

## API Documentation

The API documentation is automatically generated and available at http://localhost:5000/docs when running the application.

### Authentication Endpoints

- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `GET /auth/me` - Get current user

### Fantasy Team Endpoints

- `POST /fantasy-teams` - Create fantasy team
- `GET /fantasy-teams` - Get user's teams
- `GET /fantasy-teams/{team_id}` - Get team details
- `POST /fantasy-teams/{team_id}/players` - Add player to team
- `DELETE /fantasy-teams/{team_id}/players/{player_id}` - Remove player
- `PUT /fantasy-teams/{team_id}/captain` - Set captain

### League Endpoints

- `POST /leagues` - Create league
- `GET /leagues` - Get user's leagues
- `POST /leagues/join` - Join league by code
- `GET /leagues/{league_id}` - Get league details
- `POST /leagues/{league_id}/leave` - Leave league
- `PUT /leagues/{league_id}/team-name` - Update team name

### Player & Stats Endpoints

- `GET /players` - Get all players
- `GET /players/{player_id}` - Get player details
- `GET /players/{player_id}/stats` - Get player statistics
- `POST /matchdays/{matchday}/process` - Process matchday stats

### Transfer Endpoints

- `POST /transfers` - Execute transfer
- `GET /transfers/history` - Get transfer history
- `POST /transfers/offers` - Create transfer offer
- `GET /transfers/offers` - Get pending offers
- `PUT /transfers/offers/{offer_id}` - Accept/reject offer

## Fantasy Points System

### Scoring Rules

| Action                         | Points |
| ------------------------------ | ------ |
| **Match Played**         |        |
| 60+ minutes                    | 1      |
| < 60 minutes                   | 0.5    |
| **Goals**                |        |
| GK/DEF                         | 6      |
| MID                            | 5      |
| FWD                            | 4      |
| **Assists**              | 3      |
| **Clean Sheet** (GK/DEF) | 4      |
| **Saves** (GK, per 3)    | 1      |
| **Yellow Card**          | -1     |
| **Red Card**             | -3     |
| **Own Goal**             | -2     |
| **Penalty Missed**       | -2     |
| **Penalty Saved** (GK)   | 5      |
| **Captain Multiplier**   | 2x     |

### Formation Rules

- **Goalkeeper**: Exactly 1
- **Defenders**: 3-5 players
- **Midfielders**: 2-5 players
- **Forwards**: 1-3 players
- **Total**: Exactly 11 players

## Testing

### Running Tests in Docker

```bash
# Run all tests (inside project venv)
cd backend && ..\.venv\Scripts\python.exe -m pytest

# Run with verbose output
cd backend && ..\.venv\Scripts\python.exe -m pytest -v

# Run specific test file
cd backend && ..\.venv\Scripts\python.exe -m pytest tests/test_auth.py

# Run with coverage report
cd backend && ..\.venv\Scripts\python.exe -m pytest
```

**Current Test Coverage: 88.46%** (66 tests)

- Coverage XML artifact: `reports/testing/backend-coverage.xml`
- Summary notes: `reports/testing/coverage-summary.md`

### Test Categories

- **Authentication** (22 tests) - Password hashing, user creation, login
- **Models** (4 tests) - Database models and relationships
- **Scoring** (38 tests) - Fantasy points calculation and team validation
