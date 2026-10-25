"""Exercise deterministic resource generation and its protection of local edits."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

PROJECT = Path(__file__).resolve().parents[1]
GENERATOR = PROJECT / "tools/furniture_generator/generate.py"
CATALOG = Path("src/main/resources/data/realistic_home_decor/catalog.json")
MANIFEST = Path("tools/furniture_generator/generated_manifest.json")


class GeneratorCli(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="rhd-generator-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def generate(self, *options: str, stage: str = "first-five") -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, str(GENERATOR), "--root", str(self.root),
                               "--stage", stage, *options], text=True, capture_output=True)

    def initial(self) -> None:
        result = self.generate()
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_generated_manifest_and_content_are_deterministic(self) -> None:
        self.initial()
        first_manifest = (self.root / MANIFEST).read_bytes()
        for relative, expected_digest in json.loads(first_manifest).items():
            self.assertEqual(expected_digest, hashlib.sha256((self.root / relative).read_bytes()).hexdigest(), relative)
        self.assertEqual(20, len(json.loads((self.root / CATALOG).read_text())["entries"]))
        result = self.generate()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(first_manifest, (self.root / MANIFEST).read_bytes())
        checked = self.generate("--check")
        self.assertEqual(0, checked.returncode, checked.stderr)

    def test_check_reports_stale_resources_without_rewriting_them(self) -> None:
        self.initial()
        path = self.root / CATALOG
        path.write_bytes(b"hand-edited catalog\n")
        result = self.generate("--check")
        self.assertEqual(1, result.returncode)
        self.assertIn("outdated/missing", result.stderr)
        self.assertEqual(b"hand-edited catalog\n", path.read_bytes())

    def test_regeneration_preserves_hand_edited_generated_files(self) -> None:
        self.initial()
        path = self.root / CATALOG
        path.write_bytes(b"hand-edited catalog\n")
        result = self.generate()
        self.assertEqual(1, result.returncode)
        self.assertIn("hand-edited", result.stderr)
        self.assertEqual(b"hand-edited catalog\n", path.read_bytes())

    def test_first_generation_preserves_preexisting_user_files(self) -> None:
        path = self.root / CATALOG
        path.parent.mkdir(parents=True)
        path.write_bytes(b"preexisting user catalog\n")
        result = self.generate()
        self.assertEqual(1, result.returncode)
        self.assertEqual(b"preexisting user catalog\n", path.read_bytes())

    def test_explicit_force_restores_generated_resources(self) -> None:
        self.initial()
        path = self.root / CATALOG
        original = path.read_bytes()
        path.write_bytes(b"hand-edited catalog\n")
        result = self.generate("--force")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(original, path.read_bytes())

    def test_reducing_stage_removes_only_unedited_stale_outputs(self) -> None:
        expanded = self.generate(stage="first-twenty")
        self.assertEqual(0, expanded.returncode, expanded.stderr)
        before = set(json.loads((self.root / MANIFEST).read_bytes()))
        reduced = self.generate()
        self.assertEqual(0, reduced.returncode, reduced.stderr)
        after = set(json.loads((self.root / MANIFEST).read_bytes()))
        stale = before - after
        self.assertTrue(stale)
        self.assertTrue(all(not (self.root / relative).exists() for relative in stale))
        self.assertEqual(20, len(json.loads((self.root / CATALOG).read_text())["entries"]))


if __name__ == "__main__":
    unittest.main()
