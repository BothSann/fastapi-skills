"""Structure checks for fastapi-best-practices. Run: python -m unittest discover tests"""

import ast
import pathlib
import re
import unittest

SKILL = pathlib.Path(__file__).parents[1] / "skills" / "fastapi-best-practices"
RULES = SKILL / "rules"
ROW = re.compile(r"^\| .+ / [A-Z-]+[^|]* \| (\w+-) \| (.+) \|$", re.M)
PYTHON_BLOCK = re.compile(r"```python\n(.*?)```", re.S)


def indexed_rules() -> list[str]:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    return [
        prefix + name.strip()
        for prefix, names in ROW.findall(text)
        for name in names.split(",")
    ]


class RuleFiles(unittest.TestCase):
    def setUp(self) -> None:
        self.files = sorted(RULES.glob("*.md"))

    def test_index_matches_files_exactly(self) -> None:
        self.assertEqual(sorted(indexed_rules()), [f.stem for f in self.files])

    def test_stated_count_matches(self) -> None:
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(f"{len(self.files)} rules;", text)

    def test_each_rule_has_title_impact_and_source(self) -> None:
        for path in self.files:
            with self.subTest(path.name):
                text = path.read_text(encoding="utf-8")
                self.assertTrue(text.startswith(f"# {path.stem}\n"))
                self.assertRegex(text, r"\*\*(CRITICAL|HIGH|MEDIUM-HIGH|MEDIUM)[,.]")
                self.assertRegex(text, r"(?m)^Source: \S+")

    def test_python_examples_parse(self) -> None:
        for path in self.files:
            for block in PYTHON_BLOCK.findall(path.read_text(encoding="utf-8")):
                with self.subTest(path.name):
                    compile(block, path.name, "exec", ast.PyCF_ALLOW_TOP_LEVEL_AWAIT)

    def test_no_copied_source_repo_reference(self) -> None:
        for path in self.files:
            self.assertNotIn("zhanymkanov", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
