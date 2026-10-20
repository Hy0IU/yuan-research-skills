"""Verify file preservation and numbering without running research tasks."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).with_name("idea_files.py")


class IdeaFilesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="yuan-idea-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "研究项目 with spaces"
        self.ideas = self.root / "ideas"
        self.ideas.mkdir(parents=True)
        self.index = self.ideas / "INDEX.md"
        self.index.write_text("# My index\n", encoding="utf-8")

    def run_command(self, *args):
        process = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)
        data = json.loads(process.stdout)
        self.assertEqual(process.returncode == 0, data["ok"])
        return data

    def new_idea(self, title="方向A"):
        data = self.run_command("create", self.root, "--title", title)
        self.assertTrue(data["ok"])
        return Path(data["idea_dir"])

    def test_creates_skeleton_without_index_or_research_edits(self):
        original = self.index.read_bytes()
        folder = self.new_idea("复杂方向 A")
        self.assertEqual(folder.name, "IDEA-001-复杂方向 A")
        self.assertTrue((folder / "experiments").is_dir())
        self.assertEqual((folder / "decisions.md").read_text(), "# Decision History\n")
        self.assertEqual(self.index.read_bytes(), original)
        self.assertNotIn("{{", (folder / "idea.md").read_text())
        self.assertFalse((folder / "versions").exists())

    def test_numbering_considers_folders_and_index(self):
        self.new_idea("方向A")
        self.index.write_text("reserved: IDEA-009\n")
        folder = self.new_idea("方向B")
        self.assertEqual(folder.name, "IDEA-010-方向B")

    def test_duplicate_title_preserves_existing_research(self):
        folder = self.new_idea()
        source = folder / "idea.md"
        source.write_text("研究者原话\n当前架构\n")
        self.assertFalse(self.run_command("create", self.root, "--title", "方向A")["ok"])
        self.assertEqual(source.read_text(), "研究者原话\n当前架构\n")
        self.assertFalse((self.ideas / ".yuan-create.lock").exists())

    def test_title_cannot_create_nested_paths(self):
        folder = self.new_idea("../方向/A:B")
        self.assertEqual(folder.parent, self.ideas.resolve())
        self.assertNotIn("/", folder.name)
        self.assertNotIn(":", folder.name)

    def test_snapshot_preserves_exact_bytes_and_never_overwrites(self):
        folder = self.new_idea()
        source = folder / "idea.md"
        first = "研究者意见\r\n旧架构\n".encode()
        source.write_bytes(first)
        old = self.run_command("snapshot", folder)
        source.write_text("新的架构与原始意见\n")
        second = source.read_bytes()
        new = self.run_command("snapshot", folder)
        self.assertEqual(Path(old["snapshot"]).read_bytes(), first)
        self.assertEqual(Path(new["snapshot"]).read_bytes(), second)
        self.assertEqual(source.read_bytes(), second)
        self.assertNotEqual(old["snapshot"], new["snapshot"])

    def test_conflicting_versions_path_preserves_source(self):
        folder = self.new_idea()
        source = (folder / "idea.md").read_bytes()
        (folder / "versions").write_text("user file")
        self.assertFalse(self.run_command("snapshot", folder)["ok"])
        self.assertEqual((folder / "idea.md").read_bytes(), source)
        self.assertEqual((folder / "versions").read_text(), "user file")

    def test_symlinked_versions_does_not_write_elsewhere(self):
        folder = self.new_idea()
        external = Path(self.temp.name) / "external"
        external.mkdir()
        (folder / "versions").symlink_to(external)
        self.assertFalse(self.run_command("snapshot", folder)["ok"])
        self.assertEqual(list(external.iterdir()), [])

    def test_uninitialized_project_not_modified(self):
        target = Path(self.temp.name) / "not initialized"
        self.assertFalse(self.run_command("create", target, "--title", "方向")["ok"])
        self.assertFalse(target.exists())

    def test_existing_lock_is_preserved(self):
        lock = self.ideas / ".yuan-create.lock"
        lock.write_text("another operation")
        self.assertFalse(self.run_command("create", self.root, "--title", "方向")["ok"])
        self.assertEqual(lock.read_text(), "another operation")


if __name__ == "__main__":
    unittest.main()
