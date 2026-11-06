# security-response-filtering

**HIGH.** Use separate In and Out schemas and never return ORM rows. A return type filters fields, so new columns such as `password_hash` can't leak by default.

Avoid:
```python
@router.get("/users/{user_id}")
async def get_user(user_id: int, session: SessionDep) -> User:
    return await session.get_one(User, user_id)
```

Do:
```python
class UserOut(BaseModel):
    id: int
    name: str

@router.get("/users/{user_id}")
async def get_user(user_id: int, use_case: GetUserDep) -> UserOut:
    return UserOut.from_result(await use_case.execute(user_id))
```

Source: https://fastapi.tiangolo.com/tutorial/response-model/
