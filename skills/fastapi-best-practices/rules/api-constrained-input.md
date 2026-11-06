# api-constrained-input

**MEDIUM-HIGH.** Constrain every input and reject unknown fields. Use `StrEnum` for closed sets. Pydantic coerces by default, so use strict types where coercion is wrong.

Avoid:
```python
class PostIn(BaseModel):
    body: str
    visibility: str
```

Do:
```python
class Visibility(StrEnum):
    PUBLIC = "public"
    FOLLOWERS = "followers"

class PostIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    body: str = Field(min_length=1, max_length=2200)
    visibility: Visibility
```

Source: https://docs.pydantic.dev/latest/concepts/fields/
