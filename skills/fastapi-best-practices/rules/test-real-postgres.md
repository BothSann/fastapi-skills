# test-real-postgres

**MEDIUM-HIGH, agent-owned.** Test against real Postgres, because mocks hide SQL. Build the schema with `alembic upgrade head`, not `create_all`, and add a test calling `command.check`, so a forgotten migration fails. Join each test to an outer transaction and roll it back. That hides a missing commit, so each write route also gets one test that runs the real `lifespan` and finds the row from another connection. Import from `testcontainers.community`, because the old paths are deprecated. Fakes are fine for pure `domain` and `application` tests.

Avoid:
```python
engine = create_async_engine("sqlite+aiosqlite://")
```

Do:
```python
@pytest.fixture
async def session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with engine.connect() as conn:
        outer = await conn.begin()
        s = AsyncSession(
            bind=conn,
            join_transaction_mode="create_savepoint",
            expire_on_commit=False,
        )
        yield s
        await s.close()
        await outer.rollback()
```

Source: https://docs.sqlalchemy.org/en/21/orm/session_transaction.html
