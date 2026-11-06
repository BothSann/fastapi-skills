# db-avoid-n-plus-one

**HIGH.** Don't run a query per row. Eager-load inside a module, batch by IDs across modules, and shape read-heavy queries in SQL.

Avoid:
```python
for post in posts:
    post.likes = await likes.count(post.id)
```

Do:
```python
counts = await likes.counts_for([post.id for post in posts])
```

Source: https://docs.sqlalchemy.org/en/21/orm/queryguide/relationships.html
