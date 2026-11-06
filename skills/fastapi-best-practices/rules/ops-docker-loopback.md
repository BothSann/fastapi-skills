# ops-docker-loopback

**MEDIUM.** If local Docker services take about 20 seconds per connection on Windows, use `127.0.0.1` instead of `localhost`. Measured: about 21s against 0.03s for Postgres and Redis, on both event loops. testcontainers returns `localhost`, so replace it in test URLs.

Source: Measured on Windows 11 with Docker Desktop 29.6.
