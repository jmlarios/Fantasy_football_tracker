# Project Improvements Summary

This report highlights the work completed for each assignment requirement and where to find supporting evidence in the repository.

## 1. Code Quality & Testing

- Refactored backend services (authentication, fantasy teams, scoring) to remove duplication and better follow SOLID boundaries (see `backend/src/services/*`).
- Reworked the transfer workflow into a strategy-style service to simplify future extensions (see `backend/src/services/transfer_service.py`).
- Test suite expanded to 66 tests covering auth, scoring, leagues, and API edge cases.
- `backend/pytest.ini` enforces verbosity, strict markers, and `--cov-fail-under=70`; `.coveragerc` keeps schema models out of coverage noise.
- Latest run (2025-11-30) achieved **88.46%** line coverage with artifacts stored under `reports/testing/` (`coverage-summary.md`, `backend-coverage.xml`).

## 2. Continuous Integration (CI)

- Added `backend-build-push.yml` workflow: installs dependencies, runs pytest with coverage, uploads artifacts, then builds/pushes the backend Docker image to ACR (`jmfantasyfootball.azurecr.io/backend:v7`).
- Added `frontend-build-push.yml` workflow: installs Node 20, performs `npm ci && npm run build`, publishes the `dist` artifact, and builds/pushes the frontend image (`jmfantasyfootball.azurecr.io/frontend:v7`).
- Both workflows execute on pushes to `main` and fail the pipeline if tests or coverage gates break, satisfying the CI requirement.

## 3. Deployment Automation (CD)

- Backend and frontend each have dedicated Dockerfiles plus a top-level `docker-compose.yml` that mirrors production (backend + frontend + Postgres + Nginx).
- GitHub Actions push images directly to Azure Container Registry using secrets scoped to the `main` branch so only main can deploy.
- Azure App Service (Linux multi-container) consumes those images; then the app service must restart with `az webapp restart --resource-group BCSAI2025-DEVOPS-STUDENTS-A --name jmfantasyfootball-app` to pull the latest tags.

## 4. Monitoring & Health Checks

- `/health` endpoint (publicly `/api/health`) returns the FastAPI status plus database connectivity.
- Middleware in `backend/app.py` records request count, latency, and errors using Prometheus metrics exposed at `/metrics` (`/api/metrics` in production).
- `monitoring/prometheus.yml` and `monitoring/README.md` document how to run Prometheus locally or point it to the Azure endpoint; screenshot evidence shows the live `/api/metrics` output.

## 5. Documentation

- `README.md` now includes step-by-step instructions for Docker/compose, local development, testing commands, CI/CD overview, deployment guidance, and health/monitoring verification.
- This `REPORT.md` provides the narrative summary expected by the assignment rubric.
