# security-jwt

**HIGH.** Use PyJWT, pin `algorithms`, and require expiry. Don't use `python-jose` in new code. `alg: none` and tokens without `exp` were both rejected when this was checked.

Avoid:
```python
claims = jwt.decode(token, options={"verify_signature": False})
```

Do:
```python
try:
    claims = jwt.decode(
        token, key, algorithms=["HS256"], options={"require": ["exp", "sub"]}
    )
except jwt.InvalidTokenError as err:
    raise InvalidToken from err
```

Source: https://pyjwt.readthedocs.io/en/stable/usage.html
