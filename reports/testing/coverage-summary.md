# Backend Test Coverage Summary

- **Run Date:** 2025-11-30
- **Command:** `cd backend && ..\.venv\Scripts\python.exe -m pytest`
- **Coverage Tooling:** pytest + pytest-cov (branch coverage enabled via `.coveragerc`)
- **Result:** 66 tests passed · 88.46% line coverage · coverage XML saved as `reports/testing/backend-coverage.xml`

## How to Reproduce

1. Activate the project virtual environment (`.venv`).
2. From the repository root run:
   ```powershell
   cd backend
   ..\.venv\Scripts\python.exe -m pytest
   ```
3. The command writes `coverage.xml` under `backend/`. Copy or archive the file if you need to persist a new artifact.

## Notes

- The test suite now includes matchday aggregation coverage via `tests/test_scoring_matchday.py`, closing the previous gap in `src/services/scoring.py`.
- The `pytest.ini` enforces a 70% minimum; current runs comfortably exceed the gate.
