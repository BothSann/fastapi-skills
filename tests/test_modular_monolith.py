"""Behaviour of boundaries.py. Run: python -m unittest discover tests

The selftest cases run real import-linter through uv, so they need uv and network or cache access.
"""

import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

SKILL = Path(__file__).parents[1] / "skills" / "fastapi-modular-monolith"
SCRIPT = SKILL / "scripts" / "boundaries.py"
PYPROJECT = '[project]\nname = "demo"\nversion = "0"\ndependencies = ["fastapi[standard]>=0.1"]\n'


def run(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def make_app(root: Path, pyproject: str = PYPROJECT, package: str = "demo") -> Path:
    modules = root / "src" / package / "modules"
    modules.mkdir(parents=True)
    (root / "src" / package / "__init__.py").touch()
    (modules / "__init__.py").touch()
    (root / "pyproject.toml").write_bytes(pyproject.encode())
    return root


class Base(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.tmp = Path(self._dir.name)


class Detection(Base):
    def test_finds_app_inside_a_monorepo_and_ignores_the_frontend(self) -> None:
        make_app(self.tmp / "apps" / "api")
        web = self.tmp / "apps" / "web"
        web.mkdir(parents=True)
        (web / "package.json").write_text("{}", encoding="utf-8")
        result = run(self.tmp, "inspect")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("package: demo (src layout)", result.stdout)

    def test_several_apps_ask_instead_of_guessing(self) -> None:
        make_app(self.tmp / "apps" / "one")
        make_app(self.tmp / "apps" / "two")
        result = run(self.tmp, "inspect")
        self.assertEqual(result.returncode, 2)
        self.assertIn("several FastAPI apps", result.stderr)

    def test_no_fastapi_app_is_an_error(self) -> None:
        (self.tmp / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "0"\n', "utf-8")
        self.assertEqual(run(self.tmp, "inspect").returncode, 2)

    def test_flat_layout_and_utf8_bom_are_read(self) -> None:
        (self.tmp / "app").mkdir()
        (self.tmp / "app" / "__init__.py").touch()
        (self.tmp / "pyproject.toml").write_bytes(b"\xef\xbb\xbf" + PYPROJECT.encode())
        result = run(self.tmp, "inspect")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("package: app (flat layout)", result.stdout)

    def test_inspect_changes_nothing(self) -> None:
        make_app(self.tmp)
        before = (self.tmp / "pyproject.toml").read_bytes()
        run(self.tmp, "inspect")
        self.assertEqual((self.tmp / "pyproject.toml").read_bytes(), before)


class AddModule(Base):
    def test_creates_empty_layers_and_valid_contracts(self) -> None:
        make_app(self.tmp)
        result = run(self.tmp, "add-module", "posts")
        self.assertEqual(result.returncode, 0, result.stderr)
        module = self.tmp / "src" / "demo" / "modules" / "posts"
        for name in ("__init__", "api", "infrastructure", "application", "contracts"):
            self.assertEqual((module / f"{name}.py").read_bytes(), b"")
        self.assertFalse((module / "domain.py").exists())
        data = tomllib.loads((self.tmp / "pyproject.toml").read_text("utf-8"))
        linter = data["tool"]["importlinter"]
        self.assertEqual(linter["root_package"], "demo")
        self.assertEqual(linter["contracts"][0]["containers"], ["demo.modules.posts"])

    def test_rejects_unsafe_reserved_and_existing_names(self) -> None:
        make_app(self.tmp)
        for name in ("../evil", "Posts", "class", "shared", "a-b"):
            with self.subTest(name):
                self.assertEqual(run(self.tmp, "add-module", name).returncode, 2)
        self.assertEqual(run(self.tmp, "add-module", "posts").returncode, 0)
        self.assertEqual(run(self.tmp, "add-module", "posts").returncode, 2)

    def test_never_overwrites_owner_code(self) -> None:
        make_app(self.tmp)
        run(self.tmp, "add-module", "posts")
        api = self.tmp / "src" / "demo" / "modules" / "posts" / "api.py"
        api.write_text("ROUTES = 1\n", encoding="utf-8")
        run(self.tmp, "add-module", "posts")
        self.assertEqual(api.read_text(encoding="utf-8"), "ROUTES = 1\n")


class Sync(Base):
    def test_idempotent_and_keeps_owner_config_and_crlf(self) -> None:
        owner = PYPROJECT + "\n[tool.ruff]\nline-length = 100\n"
        make_app(self.tmp, owner.replace("\n", "\r\n"))
        run(self.tmp, "add-module", "posts")
        first = (self.tmp / "pyproject.toml").read_bytes()
        self.assertIn(b"line-length = 100\r\n", first)
        self.assertNotIn(b"\r\r", first)
        self.assertEqual(run(self.tmp, "sync").returncode, 0)
        self.assertEqual((self.tmp / "pyproject.toml").read_bytes(), first)
        self.assertEqual(run(self.tmp, "sync", "--check").returncode, 0)

    def test_owner_typed_root_package_is_not_duplicated(self) -> None:
        typed = PYPROJECT + '\n[tool.importlinter]\nroot_package = "demo"\n'
        make_app(self.tmp, typed)
        self.assertEqual(run(self.tmp, "add-module", "posts").returncode, 0)
        tomllib.loads((self.tmp / "pyproject.toml").read_text("utf-8"))

    def test_check_detects_new_layer_and_hand_edits(self) -> None:
        make_app(self.tmp)
        run(self.tmp, "add-module", "posts")
        domain = self.tmp / "src" / "demo" / "modules" / "posts" / "domain.py"
        domain.touch()
        self.assertEqual(run(self.tmp, "sync", "--check").returncode, 1)
        self.assertEqual(run(self.tmp, "sync").returncode, 0)
        config = self.tmp / "pyproject.toml"
        config.write_text(config.read_text("utf-8").replace("(domain)", "domain"), "utf-8")
        self.assertEqual(run(self.tmp, "sync", "--check").returncode, 1)


@unittest.skipUnless(shutil.which("uv"), "uv is required for real import-linter runs")
class SelfTest(Base):
    def uv(self, *args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["uv", "run", "--no-project", "--python", "3.15", "--with", "import-linter", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_selftest_proves_every_case_and_real_lint_passes(self) -> None:
        make_app(self.tmp)
        (self.tmp / "src" / "demo" / "main.py").touch()
        run(self.tmp, "add-module", "posts")
        run(self.tmp, "add-module", "media")
        result = self.uv("python", str(SCRIPT), "--root", str(self.tmp), "selftest", cwd=self.tmp)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("selftest: 15/15 cases correct", result.stdout)
        result = self.uv(
            "python", "-c",
            "import sys; sys.path.insert(0, 'src'); sys.argv = ['lint-imports', '--no-cache'];"
            "from importlinter.cli import lint_imports_command; lint_imports_command()",
            cwd=self.tmp,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_selftest_refuses_stale_contracts(self) -> None:
        make_app(self.tmp)
        run(self.tmp, "add-module", "posts")
        (self.tmp / "src" / "demo" / "modules" / "posts" / "domain.py").touch()
        result = self.uv("python", str(SCRIPT), "--root", str(self.tmp), "selftest", cwd=self.tmp)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("OUT OF SYNC", result.stdout)


if __name__ == "__main__":
    unittest.main()
