# security-cors-docs

**HIGH.** List CORS origins explicitly, and never combine `"*"` with credentials. Hide docs per environment. `app.openapi()` still works with `openapi_url=None`, so frontend types can be generated at build time.

Avoid:
```python
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True)
```

Do:
```python
docs = "/openapi.json" if settings.expose_docs else None
app = FastAPI(openapi_url=docs, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True
)
```

Source: https://fastapi.tiangolo.com/tutorial/cors/
