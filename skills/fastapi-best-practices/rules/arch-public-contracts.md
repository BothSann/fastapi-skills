# arch-public-contracts

**CRITICAL.** Other modules import only a module's `contracts`, and `import-linter` enforces this. Contracts hold plain data types and Protocols, never ORM rows.

Avoid:
```python
from app.modules.identity.infrastructure import UserRow
```

Do:
```python
from app.modules.identity.contracts import UserDirectory, UserSummary
```

Source: https://import-linter.readthedocs.io/en/stable/
