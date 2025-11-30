# Monitoring

This directory contains a minimal Prometheus configuration for scraping the backend metrics endpoint that now exposes request count, latency, and error totals at `/metrics`.

## Usage

1. Ensure the backend is running (locally with `uvicorn`/Docker Compose or in Azure).
2. Install Prometheus locally and run:
   ```bash
   prometheus --config.file=monitoring/prometheus.yml
   ```
3. By default the config scrapes the `backend` service on port `5000` every 15 seconds. Adjust the `targets` list in `prometheus.yml` to match your environment (e.g., replace with the public App Service URL and HTTPS scheme).

Once Prometheus is running you can visit `http://localhost:9090/graph` and query metrics such as:

- `http_requests_total`
- `http_request_latency_seconds_bucket`
- `http_request_errors_total`

These metrics are emitted by the FastAPI middleware added in `backend/app.py`.
