# di-annotated-aliases

**CRITICAL, ruff `FAST002`.** Declare `SessionDep = Annotated[AsyncSession, Depends(get_session)]` once and reuse it, rather than writing `= Depends(...)` defaults.

Source: https://fastapi.tiangolo.com/tutorial/dependencies/
