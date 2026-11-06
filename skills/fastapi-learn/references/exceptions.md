# When the agent writes in the app

Only these cases, each limited to its scope.

## Tests
The agent writes all tests in the worktree. They're copied in at lesson start, per write.md. If a test must change later, explain why, because the owner reads them and doesn't write them. Follow the `test-*` rules.

## Docstrings
Only when `standingExceptions` includes `docstrings`, and only after the owner's code works. Add docstrings only and change nothing else. State what each function does and what it raises. Then list them in a short `Function | Docstring says` table. Route `summary` and `responses` stay the owner's to type.

## "you write it: <item>"
Write that item only, not the one next to it. If it's unclear, ask which. Then explain it like a lesson step: What, Why, When, and How.

## Fixes
Only after "check and fix", or when the owner asks for a specific fix.

## Not exceptions
Models, migrations, dependency changes, and route wiring stay with the owner unless named in "you write it". Even then, the owner runs migrations.
