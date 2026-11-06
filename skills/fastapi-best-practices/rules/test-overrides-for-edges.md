# test-overrides-for-edges

**MEDIUM-HIGH, agent-owned.** Use `dependency_overrides` for auth, the test session, and third parties. Don't override your own use cases in integration tests, and clear overrides after each test.

Avoid:
```python
app.dependency_overrides[get_create_post] = lambda: FakeCreatePost()
```

Do:
```python
@pytest.fixture
async def client(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    app.dependency_overrides[get_session] = lambda: session
    app.dependency_overrides[get_current_user] = lambda: test_user
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://t") as client:
        yield client
    app.dependency_overrides.clear()
```

Source: https://fastapi.tiangolo.com/advanced/testing-dependencies/
