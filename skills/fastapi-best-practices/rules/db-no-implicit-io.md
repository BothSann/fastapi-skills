# db-no-implicit-io

**HIGH.** Async sessions can't lazy-load on attribute access. Set `lazy="raise"` so a missed load fails loudly, load explicitly, and use `expire_on_commit=False`.

Avoid:
```python
author = await session.get_one(Author, author_id)
titles = [book.title for book in author.books]
```

Do:
```python
books: Mapped[list[Book]] = relationship(lazy="raise")

author = await session.scalar(
    select(Author).options(selectinload(Author.books)).where(Author.id == author_id)
)
```

Source: https://docs.sqlalchemy.org/en/21/orm/extensions/asyncio.html
