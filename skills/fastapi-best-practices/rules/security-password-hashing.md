# security-password-hashing

**HIGH.** Use `pwdlib` with Argon2, off the event loop. Verify a dummy hash for unknown users so response time doesn't reveal which emails exist. Never use `passlib` in new code.

Avoid:
```python
user = await users.by_email(email)
if user is None or not hasher.verify(password, user.password_hash):
    raise InvalidCredentials
```

Do:
```python
hasher = PasswordHash.recommended()
DUMMY_HASH = hasher.hash("timing-defence")

user = await users.by_email(email)
stored = user.password_hash if user else DUMMY_HASH
ok = await asyncio.to_thread(hasher.verify, password, stored)
if user is None or not ok:
    raise InvalidCredentials
```

Source: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
