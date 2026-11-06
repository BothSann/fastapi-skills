# ops-structlog-context

**MEDIUM.** Add `merge_contextvars` to the structlog processors, then clear and bind per request in middleware, so request data can't leak between requests.

Avoid:
```python
logger.info("post created", request_id=request_id)
```

Do:
```python
async def bind_request_id(request: Request, call_next: CallNext) -> Response:
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=uuid4().hex)
    return await call_next(request)
```

Source: https://www.structlog.org/en/stable/contextvars.html
