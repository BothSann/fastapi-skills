# arch-lifespan-composition

**CRITICAL.** Create engines and clients in `lifespan`, not at import. Import-time connections break tests and reloads, and nothing closes them.

Avoid:
```python
engine = create_async_engine(get_settings().database_url)
app = FastAPI()
```

Do:
```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    engine = create_async_engine(get_settings().database_url)
    app.state.sessions = async_sessionmaker(engine, expire_on_commit=False)
    yield
    await engine.dispose()

app = FastAPI(lifespan=lifespan)
```

Source: https://fastapi.tiangolo.com/advanced/events/
