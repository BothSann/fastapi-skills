# arch-no-cycles

**CRITICAL.** A circular `from x import y` fails at import time. Move the shared type to `contracts`, or use an event. Hiding the import inside a function hides the design problem, and ruff `PLC0415` flags it. Type-only imports may use `if TYPE_CHECKING:`.

Source: https://docs.python.org/3/faq/programming.html#what-are-the-best-practices-for-using-import-in-a-module
