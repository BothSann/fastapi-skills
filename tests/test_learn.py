"""Behaviour of learn.py and the fastapi-learn docs. Run: python -m unittest discover tests"""

import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).parents[1] / "skills" / "fastapi-learn"
RULES = Path(__file__).parents[1] / "skills" / "fastapi-best-practices" / "rules"
SCRIPT = SKILL / "scripts" / "learn.py"
PYPROJECT = (
    '[project]\nname = "demo"\nversion = "0"\ndependencies = ["fastapi"]\n'
    '[dependency-groups]\ndev = ["ruff", "pytest"]\n'
)
ROUTES = '''
from fastapi import APIRouter

router = APIRouter(prefix="/posts")


@router.get("/{post_id}")
async def get_post(post_id: int) -> dict[str, int]:
    return {"id": post_id}


@router.post("")
async def create_post() -> None:
    """Not built yet."""
    raise NotImplementedError


@router.delete("/{post_id}")
async def delete_post(post_id: int) -> None: ...
'''
MAIN = '''
from fastapi import FastAPI

app = FastAPI()
app.include_router(router, prefix="/api/v1")
'''
PLAN = """# Plan

| Method | Path | Auth |
|---|---|---|
| GET | `/api/v1/posts/{id}` | user |
| POST | `/api/v1/posts` | user |
| GET | `/api/v1/feed` | user |

```text
GET /api/v1/ignored-example
```

## Build order
1. Identity
2. Posts
"""
GUIDE = """# Guide: x

## The big idea
Idea.

## Step 1: First
What: one.

## Step 2: Second
What: two.

## Finish
Gates.
"""


def learn(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True, check=False
    )


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
        cwd=repo,
        check=True,
        capture_output=True,
    )


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode())


class Base(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self._dir.cleanup)
        self.tmp = Path(self._dir.name).resolve()
        self.repo = self.tmp / "repo"
        self.repo.mkdir()

    def make_app(self, root: str = "apps/api") -> Path:
        app = self.repo / root
        write(app / "pyproject.toml", PYPROJECT)
        write(app / "src" / "demo" / "__init__.py", "")
        write(app / "src" / "demo" / "main.py", MAIN)
        write(app / "src" / "demo" / "modules" / "posts" / "api.py", ROUTES)
        write(app / "src" / "demo" / "modules" / "posts" / "__init__.py", "")
        return app

    def commit(self) -> None:
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-q", "-m", "init")

    def scan(self) -> str:
        result = learn("scan", str(self.repo), "--no-gh")
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout


class Scan(Base):
    def test_empty_folder_reports_blockers_for_scaffold(self) -> None:
        out = self.scan()
        self.assertIn("blocker: no_git", out)
        self.assertIn("blocker: no_config", out)
        self.assertIn("blocker: no_fastapi_app", out)
        self.assertIn("next lesson number: 01", out)

    def test_repo_without_commits_is_reported(self) -> None:
        git(self.repo, "init", "-q")
        self.assertIn("blocker: no_commits", self.scan())

    def test_monorepo_finds_api_and_ignores_frontend(self) -> None:
        self.make_app()
        write(self.repo / "apps" / "web" / "package.json", "{}")
        write(self.repo / "apps" / "web" / "x.py", "router.get('/web')\n")
        out = self.scan()
        self.assertIn("app: apps/api", out)
        self.assertNotIn("/web", out)

    def test_several_apps_ask(self) -> None:
        self.make_app("apps/one")
        self.make_app("apps/two")
        self.assertIn("blocker: several_apps apps/one, apps/two", self.scan())

    def test_configured_app_root_wins(self) -> None:
        self.make_app("apps/one")
        self.make_app("apps/two")
        write(self.repo / "learn" / "learn.config.json", json.dumps({"appRoot": "apps/two"}))
        out = self.scan()
        self.assertIn("app: apps/two", out)
        self.assertNotIn("several_apps", out)

    def test_routes_stubs_and_plan_coverage(self) -> None:
        self.make_app()
        write(self.repo / "docs" / "plan.md", PLAN)
        write(self.repo / "learn" / "learn.config.json", json.dumps({"planDoc": "docs/plan.md"}))
        out = self.scan()
        self.assertRegex(out, r"route GET /api/v1/posts/\{post_id\} \S+:\d+\n")
        self.assertRegex(out, r"route POST /api/v1/posts \S+ STUB")
        self.assertRegex(out, r"route DELETE /api/v1/posts/\{post_id\} \S+ STUB")
        self.assertIn("endpoints: 1 done, 1 stub, 1 missing", out)
        self.assertIn("missing: GET /api/v1/feed", out)
        self.assertNotIn("ignored-example", out)
        self.assertIn("plan: Identity", out)

    def test_syntax_error_in_owner_code_is_reported_not_fatal(self) -> None:
        app = self.make_app()
        write(app / "src" / "demo" / "broken.py", "def (:\n")
        self.assertIn("unparsed (syntax error): src/demo/broken.py", self.scan())

    def test_invalid_config_stops(self) -> None:
        write(self.repo / "learn" / "learn.config.json", "{nope")
        self.assertEqual(learn("scan", str(self.repo), "--no-gh").returncode, 2)

    def test_hints_name_a_rule(self) -> None:
        app = self.make_app()
        write(
            app / "src" / "demo" / "db.py",
            'from sqlalchemy.ext.asyncio import create_async_engine\nengine = create_async_engine("x")\n',
        )
        out = self.scan()
        self.assertIn("[arch-lifespan-composition]", out)
        for rule in re.findall(r"\[([a-z0-9-]+)\]", out):
            self.assertTrue((RULES / f"{rule}.md").is_file(), rule)

    def test_lessons_and_next_number(self) -> None:
        write(
            self.repo / "learn" / "03-posts" / "TICKET.md",
            "---\nstatus: in-progress\nkind: endpoint\nbranch: feat/posts\n---\n",
        )
        write(self.repo / "learn" / "python-concepts.md", "## With\n\n## Await\n")
        out = self.scan()
        self.assertIn("lesson 03-posts: in-progress, endpoint", out)
        self.assertIn("next lesson number: 04", out)
        self.assertIn("python concepts seen: 2", out)

    def test_scan_changes_nothing(self) -> None:
        self.make_app()
        self.commit()
        before = subprocess.run(
            ["git", "status", "--porcelain", "--ignored"], cwd=self.repo, capture_output=True, text=True
        ).stdout
        self.scan()
        after = subprocess.run(
            ["git", "status", "--porcelain", "--ignored"], cwd=self.repo, capture_output=True, text=True
        ).stdout
        self.assertEqual(before, after)


class Guide(Base):
    def test_step_prints_only_that_step(self) -> None:
        guide = self.tmp / "GUIDE.md"
        write(guide, GUIDE)
        out = learn("step", str(guide), "1").stdout
        self.assertIn("What: one.", out)
        self.assertNotIn("two", out)
        last = learn("step", str(guide), "2").stdout
        self.assertIn("What: two.", last)
        self.assertNotIn("Gates", last)

    def test_missing_step_says_how_many_exist(self) -> None:
        guide = self.tmp / "GUIDE.md"
        write(guide, GUIDE)
        result = learn("step", str(guide), "9")
        self.assertEqual(result.returncode, 1)
        self.assertIn("steps up to 2", result.stderr)

    def test_size_limits_fail(self) -> None:
        guide = self.tmp / "GUIDE.md"
        write(guide, GUIDE)
        self.assertEqual(learn("guide-size", str(guide)).returncode, 0)
        write(guide, "".join(f"## Step {n}: s\nx\n" for n in range(1, 8)))
        self.assertEqual(learn("guide-size", str(guide)).returncode, 1)
        write(guide, "## Step 1: s\n" + "x" * 15000)
        self.assertEqual(learn("guide-size", str(guide)).returncode, 1)


class Cleanup(Base):
    def lesson(self, slug: str, worktree: Path) -> None:
        write(
            self.repo / "learn" / slug / "TICKET.md",
            "---\nstatus: done\nkind: endpoint\nbranch: feat/x\n---\n",
        )
        write(self.repo / "learn" / slug / "README.md", f"# L\n\n- Worktree: {worktree}\n")

    def prepared(self) -> Path:
        write(self.repo / "a.txt", "a")
        write(self.repo / ".gitignore", "learn/\n")
        self.commit()
        path = self.tmp / "repo-lessons" / "01-x"
        git(self.repo, "worktree", "add", "-q", "--detach", str(path), "HEAD")
        self.lesson("01-x", path)
        return path

    def test_unknown_merge_state_keeps_the_worktree(self) -> None:
        path = self.prepared()
        out = learn("cleanup", str(self.repo), "--no-gh").stdout
        self.assertIn("merge state unknown", out)
        self.assertTrue(path.exists())

    def test_abandoned_removes_worktree_and_empty_parent_but_keeps_docs(self) -> None:
        path = self.prepared()
        write(path / ".venv" / "x.txt", "untracked")
        result = learn("cleanup", str(self.repo), "--no-gh", "--abandoned", "01-x")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertFalse(path.exists())
        self.assertFalse(path.parent.exists())
        self.assertTrue((self.repo / "learn" / "01-x" / "README.md").exists())
        self.assertTrue((self.repo / "a.txt").exists())

    def test_dry_run_removes_nothing(self) -> None:
        path = self.prepared()
        out = learn("cleanup", str(self.repo), "--no-gh", "--abandoned", "01-x", "--dry-run").stdout
        self.assertIn("would remove", out)
        self.assertTrue(path.exists())

    def test_never_removes_paths_that_are_not_its_worktree(self) -> None:
        self.prepared()
        stranger = self.tmp / "stranger"
        write(stranger / "keep.txt", "mine")
        self.lesson("02-y", stranger)
        self.lesson("03-z", self.repo)
        learn("cleanup", str(self.repo), "--no-gh", "--abandoned", "02-y")
        learn("cleanup", str(self.repo), "--no-gh", "--abandoned", "03-z")
        self.assertTrue((stranger / "keep.txt").exists())
        self.assertTrue((self.repo / "a.txt").exists())

    def test_unknown_abandoned_name_is_an_error(self) -> None:
        self.prepared()
        self.assertEqual(learn("cleanup", str(self.repo), "--no-gh", "--abandoned", "nope").returncode, 2)


class MergeState(Base):
    """The real gh isn't run here: these stub its output, shaped as gh 2.97 returns it."""

    def load(self):
        spec = importlib.util.spec_from_file_location("learn_under_test", SCRIPT)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        self.addCleanup(sys.modules.pop, spec.name, None)
        spec.loader.exec_module(module)
        return module

    def stub_gh(self, module, code: int, output: str) -> None:
        real_run = module.run

        def fake(args, cwd):
            return (code, output) if args[0] == "gh" else real_run(args, cwd)

        module.run = fake

    def prepared(self) -> Path:
        write(self.repo / "a.txt", "a")
        write(self.repo / ".gitignore", "learn/\n")
        self.commit()
        path = self.tmp / "repo-lessons" / "01-x"
        git(self.repo, "worktree", "add", "-q", "--detach", str(path), "HEAD")
        write(
            self.repo / "learn" / "01-x" / "TICKET.md",
            "---\nstatus: done\nkind: endpoint\nbranch: feat/x\n---\n",
        )
        write(self.repo / "learn" / "01-x" / "README.md", f"- Worktree: {path}\n")
        return path

    def test_merged_pr_removes_the_worktree(self) -> None:
        path = self.prepared()
        module = self.load()
        self.stub_gh(module, 0, '[{"number":12}]')
        self.assertEqual(module.cleanup(self.repo, None, False, True), 0)
        self.assertFalse(path.exists())

    def test_unmerged_pr_keeps_the_worktree(self) -> None:
        path = self.prepared()
        module = self.load()
        self.stub_gh(module, 0, "[]")
        self.assertEqual(module.cleanup(self.repo, None, False, True), 0)
        self.assertTrue(path.exists())

    def test_gh_failure_or_bad_output_keeps_the_worktree(self) -> None:
        path = self.prepared()
        for code, output in ((1, "not logged in"), (0, "not json"), (127, "no gh")):
            module = self.load()
            self.stub_gh(module, code, output)
            self.assertEqual(module.cleanup(self.repo, None, False, True), 0)
            self.assertTrue(path.exists())

    def test_finished_lessons_are_counted_not_listed(self) -> None:
        for number, status in (("01-a", "done"), ("02-b", "dropped"), ("03-c", "in-progress")):
            write(
                self.repo / "learn" / number / "TICKET.md",
                f"---\nstatus: {status}\nkind: endpoint\nbranch: feat/{number}\n---\n",
            )
        out = learn("scan", str(self.repo), "--no-gh").stdout
        self.assertIn("lessons finished: 2", out)
        self.assertIn("lesson 03-c: in-progress", out)
        self.assertNotIn("01-a", out)
        self.assertIn("next lesson number: 04", out)


class Docs(unittest.TestCase):
    def test_every_rule_named_in_check_exists(self) -> None:
        text = (SKILL / "references" / "check.md").read_text(encoding="utf-8")
        section = text.split("## Rule files")[1].split("## Checks that have no rule file")[0]
        rows = re.findall(r"^\| [^|]+ \| ([a-z0-9, -]+) \|$", section, re.M)
        names = [name.strip() for row in rows for name in row.split(",")]
        self.assertGreater(len(names), 30)
        for name in names:
            self.assertTrue((RULES / f"{name}.md").is_file(), name)

    def test_every_rule_is_reachable_from_check_except_operational(self) -> None:
        text = (SKILL / "references" / "check.md").read_text(encoding="utf-8")
        allowed = {"ops-toolchain-gate", "ops-docker-loopback"}
        for path in RULES.glob("*.md"):
            if path.stem not in allowed:
                self.assertIn(path.stem, text)

    def test_relative_links_resolve(self) -> None:
        for path in [SKILL / "SKILL.md", *(SKILL / "references").glob("*.md")]:
            text = path.read_text(encoding="utf-8")
            for target in re.findall(r"\]\(([^)#:]+\.md)\)", text):
                self.assertTrue((path.parent / target).is_file(), f"{path.name}: {target}")

    def test_stuck_cue_and_php_stay_out(self) -> None:
        for path in [SKILL / "SKILL.md", *(SKILL / "references").glob("*.md")]:
            text = path.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"\*\*stuck\*\*|\"stuck\"|\bPHP\b", path.name)


if __name__ == "__main__":
    unittest.main()
