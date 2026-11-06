# async-no-blocking-calls

**CRITICAL.** A blocking call in `async def` stalls every request on the event loop. Ruff `ASYNC` catches common calls, not every blocking library.

Avoid:
```python
@router.get("/rate")
async def rate() -> Rate:
    return Rate(**requests.get(URL, timeout=5).json())
```

Do:
```python
@router.get("/rate")
async def rate(http: HttpDep) -> Rate:
    response = await http.get(URL, timeout=5)
    return Rate(**response.json())
```

Source: https://fastapi.tiangolo.com/async/
