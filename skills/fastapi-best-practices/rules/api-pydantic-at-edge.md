# api-pydantic-at-edge

**MEDIUM-HIGH.** Pydantic validates untrusted input at `api` and in settings. Use stdlib dataclasses in `application`, `domain`, and `contracts`, where data is already trusted and no framework should leak.

Avoid:
```python
class Post(BaseModel):
    author_id: int

    def publish(self) -> None: ...
```

Do:
```python
@dataclass
class Post:
    author_id: int

    def publish(self) -> None: ...
```

Source: https://hynek.me/articles/python-subclassing-redux/
