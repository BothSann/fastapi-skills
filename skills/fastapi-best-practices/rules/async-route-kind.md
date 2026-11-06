# async-route-kind

**CRITICAL.** `async def` runs on the event loop, and `def` runs in a threadpool. Use `async def` when everything inside awaits. Use `def` for a route that must call a sync-only library. Never run a sync database driver inside `async def`.

Avoid:
```python
@router.get("/report")
async def report() -> Report:
    return sync_only_sdk.fetch()
```

Do:
```python
@router.get("/report")
def report() -> Report:
    return sync_only_sdk.fetch()
```

Source: https://fastapi.tiangolo.com/async/
