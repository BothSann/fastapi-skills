# arch-domain-packages

**CRITICAL.** Package by business module, not by file type. Layer names are fixed. Each layer starts as one file and becomes a package when it grows. Omit `domain` for pure CRUD.

Avoid:
```text
app/routers/posts.py
app/services/posts.py
app/models/posts.py
```

Do:
```text
app/modules/posts/api.py
app/modules/posts/application.py
app/modules/posts/domain.py
app/modules/posts/infrastructure.py
app/modules/posts/contracts.py
```

Source: https://www.cosmicpython.com/book/chapter_02_repository.html
