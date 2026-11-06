# db-sqlalchemy-2-style

**HIGH.** Use typed `Mapped[]` columns and `select()`. `Column` attributes lose type information, and `AsyncSession` has no `query()`.

Avoid:
```python
class Post(Base):
    id = Column(Integer, primary_key=True)

rows = session.query(Post).all()
```

Do:
```python
class Post(Base):
    id: Mapped[int] = mapped_column(primary_key=True)

rows = (await session.scalars(select(Post))).all()
```

Source: https://docs.sqlalchemy.org/en/21/orm/quickstart.html
