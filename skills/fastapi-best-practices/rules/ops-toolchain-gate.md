# ops-toolchain-gate

**MEDIUM.** Commit `uv.lock`, pin `requires-python`, and run the same gates locally and in CI. Run one uvicorn process per container and let the platform scale it. Ruff selects: `E,F,I,B,UP,ASYNC,FAST,DTZ,BLE,PLC0415,TID252`.

Run:
```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy
uv run lint-imports
uv run pytest
```

Source: https://docs.astral.sh/uv/concepts/projects/
