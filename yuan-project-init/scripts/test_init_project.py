"""Behavioral checks for workspace preservation and repeatable initialization."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("init_project.py")
SKILLS_ROOT = SCRIPT.resolve().parents[2]


class InitProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="yuan-init-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "研究项目 with spaces"

    def run_init(self, *extra, target=None):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "init", str(target or self.root), *extra],
            text=True, capture_output=True, check=False,
        )
        data = json.loads(result.stdout)
        self.assertEqual(result.returncode == 0, data["ok"])
        return data

    def test_initial_structure_and_links(self):
        self.assertTrue(self.run_init()["ok"])
        for name in ("references", "mechanisms", "ideas"):
            self.assertTrue((self.root / name).is_dir())
        for name in ("AGENTS.md", "research-context.md", "ideas/INDEX.md"):
            self.assertTrue((self.root / name).is_file())
        agents = (self.root / "AGENTS.md").read_text()
        for name in ("yuan-paper-explainer", "yuan-mechanism-builder", "yuan-idea-explorer"):
            self.assertIn(str(SKILLS_ROOT / name / "SKILL.md"), agents)
        self.assertEqual([p.name for p in (self.root / "ideas").iterdir()], ["INDEX.md"])
        self.assertFalse((self.root / "NOW.md").exists())
        self.assertFalse((self.root / ".git").exists())

    def test_repeat_preserves_user_changes_and_materials(self):
        self.run_init()
        for name in ("AGENTS.md", "research-context.md", "ideas/INDEX.md"):
            path = self.root / name
            path.write_text(path.read_text() + "\n研究者补充：保留这段内容。\n")
        material = self.root / "references/paper.pdf"
        material.write_bytes(b"existing user material")
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        result = self.run_init()
        self.assertTrue(all(item["action"] == "preserve" for item in result["items"]))
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_existing_agents_appended_once(self):
        self.root.mkdir()
        path = self.root / "AGENTS.md"
        original = "# Existing rules\nPreserve my project conventions."
        path.write_text(original)
        self.run_init()
        self.assertTrue(path.read_text().startswith(original))
        first = path.read_bytes()
        self.run_init()
        self.assertEqual(path.read_bytes(), first)

    def test_dry_run_has_no_side_effects(self):
        result = self.run_init("--dry-run")
        self.assertTrue(result["dry_run"])
        self.assertFalse(self.root.exists())

    def test_edited_instruction_block_is_preserved(self):
        self.run_init()
        path = self.root / "AGENTS.md"
        changed = path.read_text().replace("# 研究项目运行约定", "# 研究者定制的运行约定")
        path.write_text(changed)
        result = self.run_init()
        self.assertTrue(result["warnings"])
        self.assertEqual(path.read_text(), changed)

    def test_path_conflict_fails_before_writes(self):
        self.root.mkdir()
        conflict = self.root / "mechanisms"
        conflict.write_text("user file")
        self.assertFalse(self.run_init()["ok"])
        self.assertEqual(list(self.root.iterdir()), [conflict])
        self.assertEqual(conflict.read_text(), "user file")

    def test_symlink_never_changes_external_file(self):
        self.root.mkdir()
        external = Path(self.temp.name) / "external.md"
        external.write_text("external content")
        (self.root / "AGENTS.md").symlink_to(external)
        self.assertFalse(self.run_init()["ok"])
        self.assertEqual(external.read_text(), "external content")
        self.assertFalse((self.root / "references").exists())

    def test_invalid_markers_preserved(self):
        self.root.mkdir()
        path = self.root / "AGENTS.md"
        original = "Existing text\n<!-- yuan-research:begin -->\nunfinished block"
        path.write_text(original)
        self.assertFalse(self.run_init()["ok"])
        self.assertEqual(path.read_text(), original)
        self.assertFalse((self.root / "references").exists())

    def test_missing_skills_do_not_create_workspace(self):
        missing = Path(self.temp.name) / "missing-skills"
        self.assertFalse(self.run_init("--skills-root", str(missing))["ok"])
        self.assertFalse(self.root.exists())

    def test_skill_repository_is_not_initialized(self):
        self.assertFalse(self.run_init("--dry-run", target=SKILLS_ROOT)["ok"])


if __name__ == "__main__":
    unittest.main()
