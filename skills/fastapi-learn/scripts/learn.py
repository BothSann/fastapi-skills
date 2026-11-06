#!/usr/bin/env python3
"""Read-only lesson tools for fastapi-learn. Standard library only.

scan REPO [--no-gh]        Compact project state for choosing a lesson.
step GUIDE N               Print one guide step, so the rest stays unread.
guide-size GUIDE           Fail when a guide exceeds the step or token limits.
cleanup REPO [--abandoned SLUG] [--dry-run]
                           Remove reference worktrees of merged or abandoned lessons.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

METHODS = ("get", "post", "put", "patch", "delete")
SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "learn",
    "migrations",
    "node_modules",
    "venv",
}
NOT_PACKAGES = {"migrations", "tests", "tools"}
GATE_TOOLS = ("ruff", "mypy", "import-linter", "pytest")
MAX_STEPS = 6
MAX_GUIDE_TOKENS = 4000
CHARS_PER_TOKEN = 3.5  # Conservative estimate; the standard library has no tokenizer.
DOC_ROUTE = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\b[`\s|]+`?(/[^\s`|]*)")
STEP = re.compile(r"^## Step (\d+)\b", re.M)


def read_text(path: Path) -> str:
    return path.read_bytes().decode("utf-8-sig", errors="replace")


def run(args: list[str], cwd: Path) -> tuple[int, str]:
    try:
        done = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    except OSError as err:
        return 127, str(err)
    return done.returncode, (done.stdout + done.stderr).strip()


def load_toml(path: Path) -> dict[str, object] | None:
    try:
        return tomllib.loads(read_text(path))
    except tomllib.TOMLDecodeError:
        return None


def dependency_names(data: dict[str, object]) -> set[str]:
    items: list[str] = []
    project = data.get("project")
    if isinstance(project, dict):
        items += [str(item) for item in project.get("dependencies", [])]
    groups = data.get("dependency-groups")
    if isinstance(groups, dict):
        for group in groups.values():
            items += [item for item in group if isinstance(item, str)]
    names = {re.split(r"[^A-Za-z0-9._-]", item, maxsplit=1)[0] for item in items}
    return {name.lower().replace("_", "-") for name in names}


def find_apps(repo: Path) -> list[Path]:
    apps = []
    for current, dirs, files in os.walk(repo):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        if len(Path(current).parts) - len(repo.parts) >= 4:
            dirs[:] = []
        if "pyproject.toml" in files:
            data = load_toml(Path(current) / "pyproject.toml")
            if data and "fastapi" in dependency_names(data):
                apps.append(Path(current))
    return apps


def find_package(app: Path) -> Path | None:
    for base in (app / "src", app):
        if not base.is_dir():
            continue
        packages = [
            child
            for child in sorted(base.iterdir())
            if child.name not in NOT_PACKAGES and (child / "__init__.py").is_file()
        ]
        with_modules = [child for child in packages if (child / "modules").is_dir()]
        chosen = with_modules or packages
        if len(chosen) == 1:
            return chosen[0]
    return None


def python_files(package: Path) -> list[Path]:
    found = []
    for current, dirs, files in os.walk(package):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        found += [Path(current) / name for name in files if name.endswith(".py")]
    return sorted(found)


@dataclass(frozen=True)
class Route:
    method: str
    path: str
    where: str
    stub: bool


def is_stub(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    body = list(function.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        body = body[1:]
    if not body:
        return True
    if len(body) > 1:
        return False
    only = body[0]
    if isinstance(only, ast.Pass):
        return True
    if isinstance(only, ast.Expr) and isinstance(only.value, ast.Constant):
        return only.value.value is Ellipsis
    if isinstance(only, ast.Raise) and only.exc is not None:
        target = only.exc.func if isinstance(only.exc, ast.Call) else only.exc
        return isinstance(target, ast.Name) and target.id == "NotImplementedError"
    return False


def string_arg(call: ast.Call, name: str) -> str | None:
    value: ast.expr | None = call.args[0] if call.args and name == "path" else None
    for keyword in call.keywords:
        if keyword.arg == name:
            value = keyword.value
    if isinstance(value, ast.Constant) and isinstance(value.value, str):
        return value.value
    return None


@dataclass
class CodeFacts:
    routes: list[Route]
    tables: list[str]
    hints: list[str]
    unparsed: list[str]
    include_prefixes: set[str]


def read_code(package: Path, app: Path) -> CodeFacts:
    facts = CodeFacts([], [], [], [], set())
    for path in python_files(package):
        rel = path.relative_to(app).as_posix()
        try:
            tree = ast.parse(read_text(path))
        except SyntaxError:
            facts.unparsed.append(rel)
            continue
        prefixes: dict[str, str] = {}
        for statement in tree.body:
            if isinstance(statement, ast.Assign) and isinstance(statement.value, ast.Call):
                called = statement.value.func
                name = called.id if isinstance(called, ast.Name) else ""
                if name == "APIRouter":
                    for target in statement.targets:
                        if isinstance(target, ast.Name):
                            prefixes[target.id] = string_arg(statement.value, "prefix") or ""
                if name == "create_async_engine":
                    facts.hints.append(
                        f"{rel}:{statement.lineno} engine created at import [arch-lifespan-composition]"
                    )
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if (
                        isinstance(item, ast.Assign)
                        and any(
                            isinstance(t, ast.Name) and t.id == "__tablename__"
                            for t in item.targets
                        )
                        and isinstance(item.value, ast.Constant)
                    ):
                        facts.tables.append(str(item.value.value))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == "include_router":
                    prefix = string_arg(node, "prefix")
                    if prefix:
                        facts.include_prefixes.add(prefix)
                if node.func.attr == "add_middleware":
                    for keyword in node.keywords:
                        if keyword.arg == "allow_origins" and "'*'" in ast.dump(keyword.value):
                            facts.hints.append(
                                f"{rel}:{node.lineno} CORS allows * [security-cors-docs]"
                            )
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            for decorator in node.decorator_list:
                if not (
                    isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute)
                ):
                    continue
                if decorator.func.attr not in METHODS or not isinstance(
                    decorator.func.value, ast.Name
                ):
                    continue
                path_arg = string_arg(decorator, "path")
                if path_arg is None:
                    continue
                full = prefixes.get(decorator.func.value.id, "") + path_arg
                facts.routes.append(
                    Route(
                        decorator.func.attr.upper(),
                        full or "/",
                        f"{rel}:{node.lineno}",
                        is_stub(node),
                    )
                )
    return facts


def normalise(path: str) -> str:
    path = re.sub(r"\{[^}]*\}|:[A-Za-z_]\w*", "{}", path)
    return path.rstrip("/") or "/"


def doc_routes(text: str) -> list[tuple[str, str]]:
    prose = re.sub(r"```.*?```", "", text, flags=re.S)
    found: list[tuple[str, str]] = []
    for method, path in DOC_ROUTE.findall(prose):
        if (method, path) not in found:
            found.append((method, path))
    return found


def plan_items(text: str) -> list[str]:
    prose = re.sub(r"```.*?```", "", text, flags=re.S)
    unchecked = re.findall(r"^\s*[-*] \[ \] (.+)$", prose, re.M)
    if unchecked:
        return unchecked
    match = re.search(r"^#+ .*build order.*$\n((?:.*\n?)*?)(?=^#|\Z)", prose, re.I | re.M)
    return re.findall(r"^\s*\d+[.)] (.+)$", match.group(1), re.M) if match else []


def frontmatter(path: Path) -> dict[str, str]:
    match = re.match(r"---\r?\n(.*?)\r?\n---", read_text(path), re.S)
    pairs = re.findall(r"^(\w+):\s*(.+?)\s*$", match.group(1), re.M) if match else []
    return dict(pairs)


def merged_pr(repo: Path, branch: str, use_gh: bool) -> str | None:
    """Return a PR number, "" when none is merged, or None when unknown."""
    if not use_gh or not branch:
        return None
    args = [
        "gh",
        "pr",
        "list",
        "--head",
        branch,
        "--state",
        "merged",
        "--json",
        "number",
        "--limit",
        "1",
    ]
    code, output = run(args, repo)
    if code != 0:
        return None
    try:
        rows = json.loads(output)
    except json.JSONDecodeError:
        return None
    return str(rows[0]["number"]) if rows else ""


def lesson_dirs(repo: Path) -> list[Path]:
    learn = repo / "learn"
    if not learn.is_dir():
        return []
    return sorted(
        child for child in learn.iterdir() if child.is_dir() and re.match(r"\d+-", child.name)
    )


def scan_lessons(repo: Path, use_gh: bool) -> None:
    lessons = lesson_dirs(repo)
    highest = 0
    finished = 0
    for lesson in lessons:
        highest = max(highest, int(lesson.name.split("-", 1)[0]))
        ticket = lesson / "TICKET.md"
        meta = frontmatter(ticket) if ticket.is_file() else {}
        status = meta.get("status", "unknown")
        if status in {"done", "dropped"}:
            finished += 1
            continue
        note = ""
        if status == "in-progress":
            pr = merged_pr(repo, meta.get("branch", ""), use_gh)
            if pr:
                note = f", merged PR #{pr}"
        print(f"lesson {lesson.name}: {status}, {meta.get('kind', '?')}{note}")
    print(f"lessons finished: {finished}")
    print(f"next lesson number: {highest + 1:02d}")


def scan_app(repo: Path, app: Path, config: dict[str, object]) -> None:
    data = load_toml(app / "pyproject.toml") or {}
    print(f"app: {app.relative_to(repo).as_posix() or '.'}")
    missing = [tool for tool in GATE_TOOLS if tool not in dependency_names(data)]
    print(f"missing gate tools: {', '.join(missing) or 'none'}")
    package = find_package(app)
    if package is None:
        print("package: none yet")
        return
    print(f"package: {package.relative_to(app).as_posix()}")
    modules = package / "modules"
    if modules.is_dir():
        for module in sorted(
            p for p in modules.iterdir() if p.is_dir() and p.name != "__pycache__"
        ):
            layers = sorted(
                p.stem for p in module.iterdir() if p.stem not in {"__init__", "__pycache__"}
            )
            print(f"module {module.name}: {', '.join(layers)}")
    facts = read_code(package, app)
    prefix = next(iter(facts.include_prefixes)) if len(facts.include_prefixes) == 1 else ""
    if len(facts.include_prefixes) > 1:
        print("note: several include_router prefixes, so route paths are partial")
    known = {(r.method, normalise(prefix + r.path)): r for r in facts.routes}
    for route in facts.routes:
        marker = " STUB" if route.stub else ""
        print(f"route {route.method} {prefix}{route.path} {route.where}{marker}")
    print(f"tables: {', '.join(sorted(facts.tables)) or 'none'}")
    print(f"migrations: {len(list((app / 'migrations' / 'versions').glob('*.py')))}")
    tests = list((app / "tests").rglob("test_*.py")) if (app / "tests").is_dir() else []
    print(f"test files: {len(tests)}")
    for name in facts.unparsed:
        print(f"unparsed (syntax error): {name}")
    hints = list(facts.hints)
    main = package / "main.py"
    if main.is_file() and "lifespan" not in read_text(main):
        hints.append(
            f"{main.relative_to(app).as_posix()} has no lifespan [arch-lifespan-composition]"
        )
    if not tests:
        hints.append("no tests [test-real-postgres]")
    for hint in hints:
        print(f"hint: {hint}")

    plan = config.get("planDoc")
    if not isinstance(plan, str):
        return
    plan_path = repo / plan
    if not plan_path.is_file():
        print(f"blocker: no_plan_doc {plan}")
        return
    text = read_text(plan_path)
    for item in plan_items(text)[:8]:
        print(f"plan: {item}")
    done = 0
    stub: list[str] = []
    missing_routes: list[str] = []
    for method, path in doc_routes(text):
        wanted = normalise(path)
        found = known.get((method, wanted))
        if found is None:
            found = next(
                (
                    r
                    for (m, p), r in known.items()
                    if m == method and p != "/" and wanted.endswith(p)
                ),
                None,
            )
        if found is None:
            missing_routes.append(f"{method} {path}")
        elif found.stub:
            stub.append(f"{method} {path}")
        else:
            done += 1
    print(f"endpoints: {done} done, {len(stub)} stub, {len(missing_routes)} missing (static match)")
    for row in stub[:8]:
        print(f"stub: {row}")
    for row in missing_routes[:8]:
        print(f"missing: {row}")


def scan(repo: Path, use_gh: bool) -> int:
    code, output = run(["git", "rev-parse", "--is-inside-work-tree"], repo)
    if code == 127:
        print(f"blocker: git_unavailable {output}")
    elif code != 0:
        print(
            "blocker: no_git"
            if "not a git" in output
            else f"blocker: git_unavailable {output[:200]}"
        )
    elif run(["git", "rev-parse", "--verify", "HEAD"], repo)[0] != 0:
        print("blocker: no_commits")
    config_path = repo / "learn" / "learn.config.json"
    config: dict[str, object] = {}
    if config_path.is_file():
        try:
            loaded = json.loads(read_text(config_path))
        except json.JSONDecodeError as err:
            print(f"error: {config_path}: {err}", file=sys.stderr)
            return 2
        if not isinstance(loaded, dict):
            print(f"error: {config_path}: must be a JSON object", file=sys.stderr)
            return 2
        config = loaded
    else:
        print("blocker: no_config")
    configured = config.get("appRoot")
    if isinstance(configured, str):
        apps = (
            [(repo / configured).resolve()]
            if (repo / configured / "pyproject.toml").is_file()
            else []
        )
    else:
        apps = find_apps(repo)
    if not apps:
        print("blocker: no_fastapi_app (empty repo: scaffold lesson; otherwise check appRoot)")
    elif len(apps) > 1:
        names = ", ".join(a.relative_to(repo).as_posix() or "." for a in apps)
        print(f"blocker: several_apps {names} (ask which, then set appRoot)")
    else:
        scan_app(repo, apps[0], config)
    scan_lessons(repo, use_gh)
    ledger = repo / "learn" / "python-concepts.md"
    count = len(re.findall(r"^## ", read_text(ledger), re.M)) if ledger.is_file() else 0
    print(f"python concepts seen: {count}")
    return 0


def split_steps(text: str) -> list[tuple[int, str]]:
    matches = list(STEP.finditer(text))
    steps = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        following = re.search(r"^## ", text[match.end() : end], re.M)
        stop = match.end() + following.start() if following else end
        steps.append((int(match.group(1)), text[match.start() : stop].rstrip()))
    return steps


def show_step(guide: Path, number: int) -> int:
    steps = split_steps(read_text(guide))
    for current, body in steps:
        if current == number:
            print(body)
            return 0
    last = max((current for current, _ in steps), default=0)
    print(f"no step {number}; the guide has steps up to {last}", file=sys.stderr)
    return 1


def guide_size(guide: Path) -> int:
    text = read_text(guide)
    count = len(split_steps(text))
    tokens = round(len(text) / CHARS_PER_TOKEN)
    print(f"steps: {count}/{MAX_STEPS}; estimated tokens: {tokens}/{MAX_GUIDE_TOKENS}")
    if count > MAX_STEPS or tokens > MAX_GUIDE_TOKENS:
        print("over limit: split the ticket or shorten the guide")
        return 1
    return 0


def recorded_worktree(lesson: Path) -> Path | None:
    readme = lesson / "README.md"
    if not readme.is_file():
        return None
    match = re.search(r"^- Worktree: (.+?)\s*$", read_text(readme), re.M)
    return Path(match.group(1)) if match else None


def same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(left.resolve()) == os.path.normcase(right.resolve())


def inside(child: Path, parent: Path) -> bool:
    return os.path.normcase(child.resolve()).startswith(os.path.normcase(parent.resolve()) + os.sep)


def registered_worktrees(repo: Path) -> list[Path]:
    code, output = run(["git", "worktree", "list", "--porcelain"], repo)
    if code != 0:
        return []
    return [Path(line[9:]) for line in output.splitlines() if line.startswith("worktree ")]


def cleanup(repo: Path, abandoned: str | None, dry_run: bool, use_gh: bool) -> int:
    worktrees = registered_worktrees(repo)
    failed = False
    if abandoned and abandoned not in {lesson.name for lesson in lesson_dirs(repo)}:
        print(f"error: no lesson named {abandoned}", file=sys.stderr)
        return 2
    for lesson in lesson_dirs(repo):
        path = recorded_worktree(lesson)
        if path is None:
            continue
        if not path.exists():
            continue
        if inside(path, repo) or same_path(path, repo):
            print(f"keep {lesson.name}: recorded path is inside the repo, not a lesson worktree")
            continue
        if not any(same_path(path, worktree) for worktree in worktrees[1:]):
            print(f"keep {lesson.name}: {path} is not a registered worktree of this repo")
            continue
        if lesson.name != abandoned:
            ticket = lesson / "TICKET.md"
            branch = frontmatter(ticket).get("branch", "") if ticket.is_file() else ""
            pr = merged_pr(repo, branch, use_gh)
            if pr is None:
                print(f"keep {lesson.name}: merge state unknown, ask the owner")
                continue
            if pr == "":
                print(f"keep {lesson.name}: no merged PR, ask the owner before removing")
                continue
        if dry_run:
            print(f"would remove {path}")
            continue
        code, output = run(["git", "worktree", "remove", "--force", str(path)], repo)
        if code != 0:
            print(f"failed to remove {path}: {output}")
            failed = True
            continue
        print(f"removed {path}")
        parent = path.parent
        if parent.name.endswith("-lessons") and not any(parent.iterdir()):
            parent.rmdir()
            print(f"removed empty {parent}")
    if not dry_run:
        run(["git", "worktree", "prune"], repo)
    return 1 if failed else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    scan_parser = commands.add_parser("scan")
    scan_parser.add_argument("repo", type=Path)
    scan_parser.add_argument("--no-gh", action="store_true")
    step_parser = commands.add_parser("step")
    step_parser.add_argument("guide", type=Path)
    step_parser.add_argument("number", type=int)
    size_parser = commands.add_parser("guide-size")
    size_parser.add_argument("guide", type=Path)
    clean_parser = commands.add_parser("cleanup")
    clean_parser.add_argument("repo", type=Path)
    clean_parser.add_argument("--abandoned")
    clean_parser.add_argument("--dry-run", action="store_true")
    clean_parser.add_argument("--no-gh", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "scan":
        if not args.repo.is_dir():
            print(f"error: {args.repo}: not a directory", file=sys.stderr)
            return 2
        return scan(args.repo.resolve(), not args.no_gh)
    if args.command in {"step", "guide-size"} and not args.guide.is_file():
        print(f"error: {args.guide}: no such file", file=sys.stderr)
        return 2
    if args.command == "step":
        return show_step(args.guide, args.number)
    if args.command == "guide-size":
        return guide_size(args.guide)
    return cleanup(args.repo.resolve(), args.abandoned, args.dry_run, not args.no_gh)


if __name__ == "__main__":
    raise SystemExit(main())
