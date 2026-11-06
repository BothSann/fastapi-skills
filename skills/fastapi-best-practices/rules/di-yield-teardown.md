# di-yield-teardown

**CRITICAL.** Yield teardown runs after the response is sent. In a check on FastAPI 0.162, a failing teardown still returned 200, so never commit there. Re-raise if you catch.

Avoid:
```python
async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.sessions() as session:
        yield session
        await session.commit()
```

Do:
```python
async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    async with request.app.state.sessions() as session:
        yield session
```

Source: https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/
