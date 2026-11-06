# test-single-event-loop

**MEDIUM-HIGH, agent-owned.** Run tests and fixtures on one loop. Use the anyio plugin with `anyio_mode = "auto"` and a session-scoped backend. Create loop-bound objects inside fixtures, and use `httpx.ASGITransport`, not sync `TestClient`, with async fixtures.

Avoid:
```python
engine = create_async_engine(TEST_URL)

@pytest.mark.asyncio
async def test_create() -> None: ...
```

Do:
```python
@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"

@pytest.fixture(scope="session")
async def engine(pg_url: str) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(pg_url)
    yield engine
    await engine.dispose()
```

Source: https://anyio.readthedocs.io/en/stable/testing.html
