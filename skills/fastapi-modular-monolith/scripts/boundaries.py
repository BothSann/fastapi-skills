#!/usr/bin/env python3
"""Modular-monolith boundaries for a FastAPI project. Standard library only.

Commands: inspect, add-module NAME, sync [--check], selftest.
The selftest needs import-linter, so run it with the project's Python: uv run python ...
"""

from __future__ import annotations

import argparse
import keyword
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path

BEGIN = "# BEGIN fastapi-modular-monolith (generated: boundaries.py sync)"
END = "# END fastapi-modular-monolith"
LAYERS = ("api", "infrastructure", "application", "domain", "contracts")
INTERNAL = ("infrastructure", "application", "domain")
NEW_MODULE_LAYERS = ("api", "infrastructure", "application", "contracts")
SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "migrations",
    "node_modules",
    "venv",
}
NOT_PACKAGES = {"migrations", "tests", "tools"}
RESERVED = {"shared", "modules", "main"}
NAME = re.compile(r"^[a-z][a-z0-9_]*$")
GATE_TOOLS = ("ruff", "mypy", "import-linter", "pytest")


class ToolError(Exception):
    """A problem the user can act on; printed without a traceback."""


@dataclass(frozen=True)
class Project:
    root: Path
    package: str
    source: Path

    @property
    def package_dir(self) -> Path:
        return self.source / self.package

    @property
    def modules_dir(self) -> Path:
        return self.package_dir / "modules"

    @property
    def config(self) -> Path:
        return self.root / "pyproject.toml"


def read_text(path: Path) -> str:
    return path.read_bytes().decode("utf-8-sig")


def load_toml(path: Path) -> dict[str, object]:
    try:
        return tomllib.loads(read_text(path))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as err:
        raise ToolError(f"{path}: cannot parse: {err}") from err


def requirements(data: dict[str, object]) -> list[str]:
    project = data.get("project")
    found: list[str] = []
    if isinstance(project, dict):
        found += [str(item) for item in project.get("dependencies", [])]
        for extra in project.get("optional-dependencies", {}).values():
            found += [str(item) for item in extra]
    groups = data.get("dependency-groups")
    if isinstance(groups, dict):
        for group in groups.values():
            found += [item for item in group if isinstance(item, str)]
    return found


def requirement_names(data: dict[str, object]) -> set[str]:
    names = {re.split(r"[^A-Za-z0-9._-]", item, maxsplit=1)[0] for item in requirements(data)}
    return {name.lower().replace("_", "-") for name in names}


def find_apps(start: Path, depth: int = 4) -> list[Path]:
    apps: list[Path] = []
    base = len(start.parts)
    for current, dirs, files in os.walk(start):
        here = Path(current)
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        if len(here.parts) - base >= depth:
            dirs[:] = []
        if "pyproject.toml" not in files:
            continue
        try:
            data = load_toml(here / "pyproject.toml")
        except ToolError:
            continue
        if "fastapi" in requirement_names(data):
            apps.append(here)
    return apps


def resolve_root(given: Path) -> Path:
    start = given.resolve()
    if not start.is_dir():
        raise ToolError(f"{given}: not a directory")
    apps = find_apps(start)
    if not apps:
        raise ToolError(f"{start}: no pyproject.toml depending on fastapi")
    if len(apps) > 1:
        listing = ", ".join(str(app.relative_to(start)) for app in apps)
        raise ToolError(f"several FastAPI apps found ({listing}); pass one path")
    return apps[0]


def locate_project(root: Path) -> Project:
    data = load_toml(root / "pyproject.toml")
    tool = data.get("tool")
    linter = tool.get("importlinter") if isinstance(tool, dict) else None
    declared = linter.get("root_package") if isinstance(linter, dict) else None
    bases = [root / "src", root]
    if isinstance(declared, str):
        for base in bases:
            if (base / declared / "__init__.py").is_file():
                return Project(root, declared, base)
    for base in bases:
        if not base.is_dir():
            continue
        packages = sorted(
            child.name
            for child in base.iterdir()
            if child.name not in NOT_PACKAGES and (child / "__init__.py").is_file()
        )
        with_modules = [name for name in packages if (base / name / "modules").is_dir()]
        chosen = with_modules or packages
        if len(chosen) == 1:
            return Project(root, chosen[0], base)
        if chosen:
            raise ToolError(f"several packages in {base}: {', '.join(chosen)}; set root_package")
    raise ToolError(f"{root}: no Python package found")


def module_names(project: Project) -> list[str]:
    if not project.modules_dir.is_dir():
        return []
    return sorted(
        child.name
        for child in project.modules_dir.iterdir()
        if child.is_dir() and not child.name.startswith("_") and child.name != "__pycache__"
    )


def has_layer(module_dir: Path, layer: str) -> bool:
    return (module_dir / f"{layer}.py").is_file() or (module_dir / layer / "__init__.py").is_file()


def layers_of(project: Project, module: str) -> list[str]:
    return [layer for layer in LAYERS if has_layer(project.modules_dir / module, layer)]


def toml_list(items: list[str]) -> str:
    return "[" + ", ".join(f'"{item}"' for item in items) + "]"


def strip_block(text: str) -> str:
    pattern = re.compile(rf"{re.escape(BEGIN)}.*?{re.escape(END)}\r?\n?", re.S)
    return pattern.sub("", text)


def generate_block(project: Project, outside: str) -> str:
    modules = module_names(project)
    prefix = f"{project.package}.modules"
    lines = [BEGIN]
    linter = tomllib.loads(outside).get("tool", {}).get("importlinter", {})
    if "root_package" not in linter:
        lines += ["[tool.importlinter]", f'root_package = "{project.package}"', ""]
    lines += [
        "[[tool.importlinter.contracts]]",
        'name = "module layers"',
        'type = "layers"',
        "layers = " + toml_list([f"({layer})" for layer in LAYERS]),
        "containers = " + toml_list([f"{prefix}.{name}" for name in modules]),
    ]
    has_main = (project.package_dir / "main.py").is_file()
    for name in modules:
        present = layers_of(project, name)
        internal = [f"{prefix}.{name}.{layer}" for layer in INTERNAL if layer in present]
        if internal:
            lines += [
                "",
                "[[tool.importlinter.contracts]]",
                f'name = "{name} internals are private"',
                'type = "protected"',
                "protected_modules = " + toml_list(internal),
                "allowed_importers = " + toml_list([f"{prefix}.{name}"]),
            ]
        if "api" in present:
            allowed = [f"{prefix}.{name}"]
            if has_main:
                allowed.append(f"{project.package}.main")
            lines += [
                "",
                "[[tool.importlinter.contracts]]",
                f'name = "{name} api is for the app entry only"',
                'type = "protected"',
                "protected_modules = " + toml_list([f"{prefix}.{name}.api"]),
                "allowed_importers = " + toml_list(allowed),
            ]
    if (project.package_dir / "shared").is_dir():
        lines += [
            "",
            "[[tool.importlinter.contracts]]",
            'name = "shared code stays independent of modules"',
            'type = "forbidden"',
            "source_modules = " + toml_list([f"{project.package}.shared"]),
            "forbidden_modules = " + toml_list([prefix]),
        ]
    lines.append(END)
    return "\n".join(lines) + "\n"


def current_block(text: str) -> str | None:
    match = re.search(rf"{re.escape(BEGIN)}.*?{re.escape(END)}\r?\n?", text, re.S)
    return match.group(0).replace("\r\n", "\n") if match else None


def merged_config(project: Project, text: str) -> str:
    newline = "\r\n" if "\r\n" in text else "\n"
    outside = strip_block(text).replace("\r\n", "\n")
    block = generate_block(project, outside)
    if current_block(text) is None:
        joined = outside.rstrip("\n") + "\n\n" + block
    else:
        before = text[: text.index(BEGIN)].replace("\r\n", "\n")
        after = outside[len(before) :]
        joined = before + block + after
    return joined.replace("\n", newline)


def sync(project: Project, check: bool = False) -> bool:
    """Return True when the config matches the modules on disk."""
    if not module_names(project):
        print("sync: no modules yet, nothing to generate")
        return True
    text = read_text(project.config)
    outside = strip_block(text).replace("\r\n", "\n")
    in_sync = current_block(text) == generate_block(project, outside)
    if check:
        print("sync: in sync" if in_sync else "sync: OUT OF SYNC, run sync")
        return in_sync
    if in_sync:
        print("sync: already in sync")
        return True
    updated = merged_config(project, text)
    tomllib.loads(updated)
    project.config.write_bytes(updated.encode("utf-8"))
    print(f"sync: updated {project.config.name}, {len(module_names(project))} module(s)")
    return True


def add_module(project: Project, name: str) -> None:
    if not NAME.match(name) or keyword.iskeyword(name) or name in RESERVED:
        raise ToolError(f"{name!r}: use a snake_case name that isn't reserved")
    target = project.modules_dir / name
    if target.exists():
        raise ToolError(f"{target}: already exists")
    if not (project.modules_dir / "__init__.py").is_file():
        raise ToolError(f"{project.modules_dir}: create the modules package first")
    target.mkdir()
    created = ["__init__.py", *(f"{layer}.py" for layer in NEW_MODULE_LAYERS)]
    for file_name in created:
        (target / file_name).touch()
    print(f"created {target.relative_to(project.root)}: {', '.join(created)}")
    sync(project)


def inspect(project: Project) -> None:
    print(f"root: {project.root}")
    layout = "src" if project.source.name == "src" else "flat"
    print(f"package: {project.package} ({layout} layout)")
    modules = module_names(project)
    if modules:
        for name in modules:
            print(f"module {name}: {', '.join(layers_of(project, name)) or 'no layers'}")
    else:
        print("modules: none")
    text = read_text(project.config)
    state = "missing"
    if current_block(text) is not None:
        outside = strip_block(text).replace("\r\n", "\n")
        state = "in sync" if current_block(text) == generate_block(project, outside) else "stale"
    print(f"boundaries: {state}")
    names = requirement_names(load_toml(project.config))
    missing = [tool for tool in GATE_TOOLS if tool not in names]
    print(f"missing gate tools: {', '.join(missing) or 'none'}")
    print(f"main.py: {'present' if (project.package_dir / 'main.py').is_file() else 'missing'}")


def linter_command() -> str:
    suffix = ".exe" if os.name == "nt" else ""
    beside = Path(sys.executable).parent / f"lint-imports{suffix}"
    found = str(beside) if beside.is_file() else shutil.which("lint-imports")
    if not found:
        raise ToolError("lint-imports not found: install import-linter, then use uv run python")
    return found


def add_fixture_module(modules: Path, name: str) -> None:
    target = modules / name
    target.mkdir()
    (target / "__init__.py").touch()
    for layer in LAYERS:
        (target / f"{layer}.py").touch()


# Each case: file to change, import to add, whether lint-imports should pass.
def selftest_cases(package: str) -> list[tuple[str, str, bool]]:
    a = f"{package}.modules.zz_a"
    return [
        ("modules/zz_a/domain.py", f"{a}.application", False),
        ("modules/zz_a/application/__init__.py", f"{a}.api", False),
        ("modules/zz_a/application/__init__.py", f"{a}.infrastructure", False),
        ("modules/zz_a/contracts.py", f"{a}.application", False),
        ("modules/zz_a/infrastructure.py", f"{a}.api", False),
        ("modules/zz_b/application.py", f"{a}.infrastructure", False),
        ("modules/zz_b/application.py", f"{a}.application.deep", False),
        ("modules/zz_b/contracts.py", f"{a}.domain", False),
        ("modules/zz_b/application.py", f"{a}.api", False),
        ("main.py", f"{a}.infrastructure", False),
        ("shared/__init__.py", f"{a}.contracts", False),
        ("modules/zz_b/application.py", f"{a}.contracts", True),
        ("modules/zz_a/api.py", f"{a}.infrastructure", True),
        ("modules/zz_a/infrastructure.py", f"{a}.application", True),
        ("main.py", f"{a}.api", True),
    ]


def selftest(project: Project) -> bool:
    command = linter_command()
    ok = True
    if module_names(project) and not sync(project, check=True):
        ok = False
    with tempfile.TemporaryDirectory(prefix="boundaries-selftest-") as tmp:
        source = Path(tmp) / "source"
        package_dir = source / project.package
        shutil.copytree(
            project.package_dir,
            package_dir,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        modules = package_dir / "modules"
        modules.mkdir(exist_ok=True)
        (modules / "__init__.py").touch()
        add_fixture_module(modules, "zz_a")
        add_fixture_module(modules, "zz_b")
        layer_file = modules / "zz_a" / "application.py"
        layer_file.unlink()
        (modules / "zz_a" / "application").mkdir()
        (modules / "zz_a" / "application" / "__init__.py").touch()
        (modules / "zz_a" / "application" / "deep.py").touch()
        (package_dir / "main.py").touch()
        (package_dir / "shared").mkdir(exist_ok=True)
        (package_dir / "shared" / "__init__.py").touch()

        fixture = Project(Path(tmp), project.package, source)
        config = Path(tmp) / "pyproject.toml"
        config.write_text(generate_block(fixture, ""), encoding="utf-8")
        env = {**os.environ, "PYTHONPATH": str(source)}

        def passes() -> tuple[bool, str]:
            try:
                result = subprocess.run(
                    [command, "--no-cache", "--config", str(config)],
                    cwd=tmp,
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False,
                )
            except OSError as err:
                raise ToolError(
                    f"could not start {command}: {err}. If Windows Smart App Control blocked it, "
                    "tell the owner; never disable it or work around it."
                ) from err
            return result.returncode == 0, result.stdout + result.stderr

        baseline, output = passes()
        if not baseline:
            print("selftest: FAILED before any bad import was added\n" + output[-1500:])
            return False
        cases = selftest_cases(project.package)
        wrong = []
        for rel, target, should_pass in cases:
            path = package_dir / rel
            original = path.read_bytes()
            path.write_bytes(original + f"\nimport {target}\n".encode())
            outcome, _ = passes()
            path.write_bytes(original)
            if outcome != should_pass:
                expected = "pass" if should_pass else "fail"
                wrong.append(f"{rel} importing {target} should {expected}")
    for line in wrong:
        print(f"selftest wrong: {line}")
    print(f"selftest: {len(cases) - len(wrong)}/{len(cases)} cases correct")
    return ok and not wrong


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="project or monorepo path")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("inspect")
    add = commands.add_parser("add-module")
    add.add_argument("name")
    sync_parser = commands.add_parser("sync")
    sync_parser.add_argument("--check", action="store_true")
    commands.add_parser("selftest")
    args = parser.parse_args(argv)
    try:
        project = locate_project(resolve_root(Path(args.root)))
        if args.command == "inspect":
            inspect(project)
        elif args.command == "add-module":
            add_module(project, args.name)
        elif args.command == "sync":
            return 0 if sync(project, check=args.check) else 1
        else:
            return 0 if selftest(project) else 1
    except ToolError as err:
        print(f"error: {err}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
