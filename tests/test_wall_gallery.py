import json
import tempfile
import unittest
from pathlib import Path

from tools import wall_gallery as gallery


def catalog():
    entries = [{"id": "wall_clock_oak", "template": "wall_clock", "material": "oak"}]
    for family, template in (("masonry", "wall_test_brick"), ("wood", "wall_test_slats")):
        for palette in gallery.PALETTES:
            identifier = f"{template}_{palette}"
            entries.append({"id": identifier, "template": template, "material": palette,
                            "wall_family": family, "placement": "any", "connect": False,
                            "parts": [{"id": identifier, "offset": [0, 0, 0]}]})
    return {"schema_version": 1, "entries": entries}


class WallGalleryTests(unittest.TestCase):
    def setUp(self):
        self.files = gallery.render(json.dumps(catalog()).encode())
        self.manifest = json.loads(self.files["gallery_manifest.json"])

    def test_only_new_walls_selected_and_every_palette_present(self):
        self.assertEqual(2, self.manifest["wall_templates"])
        self.assertEqual(16, self.manifest["palette_variants"])
        self.assertEqual(34, self.manifest["display_blocks"])
        self.assertNotIn("wall_clock_oak", "".join(self.files.values()))
        for bay in self.manifest["bays"]:
            self.assertEqual(list(gallery.PALETTES), [s["palette"] for s in bay["palette_samples"]])
            x = bay["patch"]["min"][0]
            self.assertEqual([x + 3, x + 2, x + 1, x],
                             [s["position"][0] for s in bay["palette_samples"][:4]])
            self.assertEqual(2, bay["patch"]["max"][0] - bay["patch"]["min"][0])
            self.assertEqual(2, bay["patch"]["max"][1] - bay["patch"]["min"][1])

    def test_verification_counts_every_display_block_and_logs_without_players(self):
        verify = self.files["data/rhd_walls/function/verify.mcfunction"]
        self.assertEqual(34, verify.count("run say RHD_WALL_GALLERY_MISSING "))
        self.assertNotIn("tellraw", verify)
        self.assertIn("expected_blocks=34", verify)

    def test_bounded_fill_under_default_limit_and_no_auto_functions(self):
        clear = self.files["data/rhd_walls/function/internal/clear.mcfunction"]
        self.assertIn("fill ~ ~-1 ~ ~63 ~6 ~47 minecraft:air", clear)
        self.assertLessEqual(64 * 48 * 8, 32768)
        self.assertFalse(any("/tags/" in name for name in self.files))
        self.assertFalse(any("/functions/" in name for name in self.files))
        self.assertEqual([94, 1], json.loads(self.files["pack.mcmeta"])["pack"]["min_format"])
        self.assertIn("execute if loaded", self.files["data/rhd_walls/function/build.mcfunction"])

    def test_repeatable_output_and_unrelated_files_protected(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            gallery.save(output, self.files)
            gallery.save(output, self.files, check=True)
            before = (output / "gallery_manifest.json").read_bytes()
            gallery.save(output, self.files)
            self.assertEqual(before, (output / "gallery_manifest.json").read_bytes())
            (output / "user.txt").write_text("preserve")
            with self.assertRaisesRegex(ValueError, "Unexpected"):
                gallery.save(output, self.files)
            self.assertEqual("preserve", (output / "user.txt").read_text())

    def test_unknown_directory_and_corrupt_output_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            (output / "world.txt").write_text("preserve")
            with self.assertRaisesRegex(ValueError, "nonempty"):
                gallery.save(output, self.files)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            gallery.save(output, self.files)
            (output / "pack.mcmeta").write_text("{}")
            with self.assertRaisesRegex(ValueError, "differs"):
                gallery.save(output, self.files, check=True)

    def test_incomplete_palette_matrix_and_support_dependent_wall_rejected(self):
        data = catalog()
        data["entries"].pop()
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            gallery.render(json.dumps(data).encode())
        data = catalog()
        data["entries"][1]["placement"] = "wall"
        with self.assertRaisesRegex(ValueError, "stackable"):
            gallery.render(json.dumps(data).encode())


if __name__ == "__main__":
    unittest.main()
