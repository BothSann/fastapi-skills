# db-explicit-driver

**HIGH.** Name the driver: `postgresql+asyncpg://`. A bare `postgresql://` selects psycopg in SQLAlchemy 2.1, whose async mode rejects Windows' default event loop. Dispose the engine at shutdown, as in `arch-lifespan-composition`.

Source: https://docs.sqlalchemy.org/en/21/changelog/migration_21.html
