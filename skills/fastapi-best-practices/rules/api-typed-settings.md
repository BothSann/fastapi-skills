# api-typed-settings

**MEDIUM-HIGH.** Use per-module `BaseSettings` behind a cached function, so tests can override it. A module-level instance reads the environment at import.

Avoid:
```python
settings = MediaSettings()
```

Do:
```python
class MediaSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MEDIA_")
    bucket: str

@lru_cache
def get_media_settings() -> MediaSettings:
    return MediaSettings()
```

Source: https://fastapi.tiangolo.com/advanced/settings/
