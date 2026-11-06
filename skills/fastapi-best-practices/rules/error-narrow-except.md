# error-narrow-except

**HIGH, ruff `BLE001` and `B904`.** Catch the exceptions you can handle, keep `try` blocks small, and use `raise New() from err` to keep the cause.

Source: https://google.github.io/styleguide/pyguide.html#24-exceptions
