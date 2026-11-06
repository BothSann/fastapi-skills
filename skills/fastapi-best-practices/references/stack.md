# Proven stack

Checked together on 2026-11-06 on Windows 11. Use the project's installed versions when they differ, and verify version-sensitive APIs against them.

| Area | Packages |
|---|---|
| Runtime | Python 3.15.1, uv 0.12 |
| App | fastapi 0.162, uvicorn 0.54, pydantic-settings |
| Data | sqlalchemy 2.1, asyncpg 0.32, alembic 1.20 |
| Auth | PyJWT 2.15, pwdlib 0.3 with argon2 |
| Media | pillow 13, boto3 1.43 |
| Jobs | taskiq 0.13, taskiq-redis 1.2 |
| Gates | ruff 0.17, mypy 2.4 strict, import-linter 2.16, pytest 9.2 |
| Tests | anyio 4.16, httpx 0.28, testcontainers 4.15 |
| Local services | postgres:18, redis:8, rustfs (1.0 beta, development only) |

Limits:
- Not tested: real R2, real photos, load, or production.
- `fastapi[standard]` wasn't part of the suite. On Python 3.15 it needs PyYAML built from source, because no wheel exists; a wheels-only install silently selects FastAPI 0.110.
- taskiq is classified Alpha, and several packages don't yet declare Python 3.15 support, though the suite passes.
- Windows Smart App Control blocked a generated `lint-imports.exe` once, in a throwaway uv environment, and allowed it on later runs. If a tool is blocked, report it to the owner. Never disable the control or work around it.
