# db-session-per-request

**HIGH.** Use one `AsyncSession` per request and never share it across tasks. SQLAlchemy documents it as unsafe for concurrent use, and misuse may not fail every time, so passing once proves nothing.

Avoid:
```python
await asyncio.gather(posts.count(session), users.count(session))
```

Do:
```python
posts_total = await posts.count(session)
users_total = await users.count(session)
```

Source: https://docs.sqlalchemy.org/en/21/orm/extensions/asyncio.html
