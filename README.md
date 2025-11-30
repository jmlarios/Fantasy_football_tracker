# Fantasy Football Tracker

A full-stack fantasy football application for managing LaLiga fantasy leagues, teams, and player statistics. Built with FastAPI, React, and PostgreSQL, designed to run seamlessly with Docker.

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start with Docker](#quick-start-with-docker)
- [Local Development](#local-development)
- [Testing](#testing)
- [CI/CD Pipeline](#cicd-pipeline)
- [Deployment](#deployment)
- [Health & Monitoring](#health--monitoring)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Fantasy Points System](#fantasy-points-system)

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
│   ├── db_init.py                  # Database bootstrap script
│   ├── requirements.txt            # Python dependencies
│   ├── pytest.ini / .coveragerc    # Test + coverage settings
│   ├── Dockerfile                  # Backend container build
│   ├── db_scripts/                 # One-off maintenance scripts
│   ├── scripts/
│   │   └── update_player_stats_from_matchdays.py
│   ├── src/
│   │   ├── models.py               # SQLAlchemy ORM models
│   │   ├── routes.py               # Router wiring
│   │   ├── middleware/
│   │   │   └── session.py          # Session handling
│   │   └── services/
│   │       ├── auth.py
│   │       ├── fantasy_team.py
│   │       ├── laliga_scraper.py
│   │       ├── league_service.py
│   │       ├── matchday_initializer.py
│   │       ├── scoring.py
│   │       └── transfer_service.py
│   └── tests/
│       ├── conftest.py
│       ├── test_auth.py
│       ├── test_models.py
│       ├── test_scoring.py
│       └── test_scoring_comprehensive.py
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json / vite.config.ts
│   └── src/
│       ├── App.tsx, main.tsx, index.css
│       ├── components/
│       │   ├── Dashboard.tsx, MyFantasyLeagues.tsx
│       │   ├── auth/ (LoginForm.tsx, RegisterForm.tsx)
│       │   └── fantasy/ (CreateTeamModal.tsx, FantasyTeamsList.tsx, PlayerBrowser.tsx, TeamDetailPage.tsx)
│       ├── contexts/ (AuthContext.tsx)
│       ├── services/ (api.ts, authService.ts, leagueService.ts)
│       └── types/ (auth.ts, fantasy.ts)
├── monitoring/
│   ├── README.md                   # Prometheus instructions
│   └── prometheus.yml              # Scrape config
├── deploy/
│   └── docker-compose.azure.yml    # App Service compose definition
├── reports/
│   └── testing/
│       ├── backend-coverage.xml
│       └── coverage-summary.md
├── .github/workflows/
│   ├── backend-build-push.yml
│   └── frontend-build-push.yml
├── docker-compose.yml              # Multi-container dev/prod parity
├── REPORT.md
└── README.md

```

## API Documentation

Interactive docs live at http://localhost:5000/docs during local runs. When the frontend proxies requests in production, prepend `/api` (e.g., `https://jmfantasyfootball-app.azurewebsites.net/api/health`).

### System & Monitoring

- `GET /` – Root service banner and version
- `GET /health` – Application + database health probe
- `GET /metrics` – Prometheus metrics (request count, latency, errors)

### Authentication Endpoints

- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `GET /auth/me` - Get current user

### Fantasy Team Endpoints

- `POST /fantasy-teams` - Create fantasy team
- `GET /fantasy-teams` - Get user's teams
- `GET /fantasy-teams/{team_id}` - Get team details
- `GET /fantasy-teams/{team_id}/leagues` - List leagues a team participates in
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
- `GET /players/search` - Filter players by query, team, or position
- `GET /players/{player_id}` - Get player details
- `GET /players/{player_id}/stats` - Get player statistics
- `GET /teams` - List distinct LaLiga clubs
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

## Local Development

You can run the services individually without Docker for faster iteration.

```powershell
# Backend
cd backend
python -m venv .venv
. .venv/Scripts/Activate.ps1
pip install -r requirements.txt
uvicorn app:app --reload --port 5000

# Frontend (new terminal)
cd frontend
npm install
npm run dev -- --host --port 3000
```

The frontend expects the API under `/api/*`. When running locally without Nginx, set `VITE_API_BASE=http://localhost:5000` or proxy the dev server.

## Testing

Automated tests run through `pytest` with coverage gates defined in `backend/pytest.ini`.

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest
```

- Coverage is enforced at **70% minimum** via `--cov-fail-under=70`.
- Latest local run: **66 tests, 88.46% line coverage** (see `reports/testing/coverage-summary.md`).
- The XML report uploaded by CI lives at `reports/testing/backend-coverage.xml`.

### Test Categories

- **Authentication** (22 tests) - Password hashing, user creation, login
- **Models** (4 tests) - Database models and relationships
- **Scoring** (38 tests) - Fantasy points calculation and team validation
- **Leagues/Transfers/API** - Scenario-level coverage for endpoints and services

## CI/CD Pipeline

GitHub Actions run on every push to `main`:

- `backend-build-push.yml` installs Python deps, runs pytest with coverage, uploads `coverage.xml`, then builds and pushes `jmfantasyfootball.azurecr.io/backend:v7`.
- `frontend-build-push.yml` installs Node deps, builds the Vite bundle, uploads the `dist` artifact, then builds and pushes `jmfantasyfootball.azurecr.io/frontend:v7`.
- Both jobs fail immediately if tests break or coverage dips below 70%, ensuring deploys never ship untested code.

Secrets (`ACR_USERNAME`, `ACR_PASSWORD`) gate image publishing and are only available on the `main` branch, satisfying the “deploy from main only” requirement.

## Deployment

Production runs on Azure App Service (Linux, multi-container). Deployment flow:

1. Merge to `main`; CI builds/pushes fresh backend/frontend images tagged `v7` in Azure Container Registry.
2. `docker-compose.yml` (or the App Service container settings) references those tags.
3. Restart the web app to pull the new images:
   ```powershell
   az webapp restart --resource-group BCSAI2025-DEVOPS-STUDENTS-A --name jmfantasyfootball-app
   ```
4. Verify `https://jmfantasyfootball-app.azurewebsites.net` serves the new frontend and `https://jmfantasyfootball-app.azurewebsites.net/api/health` reports `{"status":"healthy"}`.

For local Docker deployments run `docker-compose up --build` which mirrors the production topology (frontend + backend + Postgres + Nginx).

## Health & Monitoring

- **Health check:** `GET /health` verifies the FastAPI process and database connectivity. The App Service configuration maps this endpoint to `/api/health` for the public site.
- **Metrics:** `GET /metrics` (exposed publicly at `/api/metrics`) emits Prometheus-formatted counters/histograms for request totals, latency, and server errors.
- **Prometheus setup:** `monitoring/prometheus.yml` scrapes the backend every 15s by default. To point a local Prometheus instance at Azure set the target to `https://jmfantasyfootball-app.azurewebsites.net/api/metrics`.
- **Verification:** refer to the screenshot in the project issue tracker showing the live `/api/metrics` output from production.
