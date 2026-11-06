# db-naming-convention

**HIGH.** Set a naming convention before the first migration, or constraints get database-generated names that later migrations can't target reliably.

Avoid:
```python
class Base(DeclarativeBase):
    pass
```

Do:
```python
class Base(DeclarativeBase):
    metadata = MetaData(naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    })
```

Source: https://docs.sqlalchemy.org/en/21/core/constraints.html#configuring-constraint-naming-conventions
