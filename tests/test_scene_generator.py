"""Exercise generated scene counts, support placement, safety, and repeatability."""

import json
import tempfile
import unittest
from pathlib import Path

from tools import scene_generator as scene


def fixture():
    return [
        {"id": "wide_table", "category": "kitchen", "placement": "floor", "parts": [
            {"id": "wide_table", "offset": [0, 0, 0]},
            {"id": "wide_table_part_1", "offset": [1, 0, 0]},
        ]},
        {"id": "wall_clock", "category": "decorations", "placement": "wall", "parts": [
            {"id": "wall_clock", "offset": [0, 0, 0]},
            {"id": "wall_clock_part_1", "offset": [0, 1, 0]},
        ]},
        {"id": "pendant", "category": "lighting", "placement": "ceiling", "parts": [
            {"id": "pendant", "offset": [0, 0, 0]},
        ]},
    ]


class SceneGeneratorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = scene.render(fixture(), b"fixture")
        cls.manifest = json.loads(cls.files["scene_manifest.json"])

    def test_exact_item_counts_and_complete_disjoint_parts(self):
        for count in (0, 100, 500, 1000):
            with self.subTest(count=count):
                manifest = self.manifest["scenes"][str(count)]
                self.assertEqual(count, manifest["primary_items"])
                self.assertEqual(count, len(manifest["placements"]))
                positions = [tuple(part["position"]) for placement in manifest["placements"]
                             for part in placement["parts"]]
                self.assertEqual(len(positions), len(set(positions)))
                self.assertEqual(len(positions), manifest["furniture_cells"])
                body = self.files[f"data/rhd_test/function/internal/scene_{count}.mcfunction"]
                self.assertEqual(len(positions), body.count(" realistic_home_decor:"))
                for placement in manifest["placements"]:
                    primary = placement["parts"][0]
                    self.assertEqual(placement["id"], primary["id"])
                    self.assertEqual(placement["position"], primary["position"])
                    for part in placement["parts"]:
                        command = (f"setblock {scene.coordinates(part['position'])} "
                                   f"realistic_home_decor:{part['id']}[facing=north]")
                        self.assertIn(command + "\n", body)

    def test_support_direction_and_ceiling_height_match_north_runtime(self):
        floor, wall, ceiling = fixture()
        self.assertEqual({(0, -1, 0), (1, -1, 0)}, scene.support_positions(floor))
        self.assertEqual({(0, 0, 1), (0, 1, 1)}, scene.support_positions(wall))
        self.assertEqual({(0, 1, 0)}, scene.support_positions(ceiling))
        ceiling["parts"].append({"id": "pendant_part_1", "offset": [0, 2, 0]})
        self.assertEqual({(0, 3, 0)}, scene.support_positions(ceiling))

    def test_wall_support_cannot_replace_furniture(self):
        entry = fixture()[1]
        entry["parts"].append({"id": "bad_part", "offset": [0, 0, 1]})
        with self.assertRaisesRegex(ValueError, "Support overlaps"):
            scene.support_positions(entry)

    def test_official_pack_format_and_no_automatic_world_function(self):
        pack = json.loads(self.files["pack.mcmeta"])["pack"]
        self.assertEqual([94, 1], pack["min_format"])
        self.assertEqual([94, 1], pack["max_format"])
        self.assertFalse(any("/tags/" in path for path in self.files))
        self.assertTrue(all("/functions/" not in path for path in self.files))

    def test_all_fills_fit_default_limit_and_clear_entire_documented_bounds(self):
        text = self.files["data/rhd_test/function/internal/clear.mcfunction"]
        bounds = self.manifest["bounds_relative"]
        cleared = set()
        for line in text.splitlines():
            if not line.startswith("fill "):
                continue
            tokens = line.split()
            values = [int(value[1:] or "0") for value in tokens[1:7]]
            x1, y1, z1, x2, y2, z2 = values
            volume = (x2 - x1 + 1) * (y2 - y1 + 1) * (z2 - z1 + 1)
            self.assertLessEqual(volume, 32768)
            if tokens[7] == "minecraft:air":
                for x in range(x1, x2 + 1):
                    for y in range(y1, y2 + 1):
                        for z in range(z1, z2 + 1):
                            self.assertNotIn((x, y, z), cleared)
                            cleared.add((x, y, z))
        first, last = bounds["min"], bounds["max"]
        expected = (last[0] - first[0] + 1) * (last[1] - first[1] + 1) * (last[2] - first[2] + 1)
        self.assertEqual(expected, len(cleared))
        self.assertIn(tuple(first), cleared)
        self.assertIn(tuple(last), cleared)

    def test_unloaded_region_never_invokes_clear_directly(self):
        for count in (0, 100, 500, 1000):
            wrapper = self.files[f"data/rhd_test/function/scene_{count}.mcfunction"]
            self.assertNotIn("function rhd_test:internal/clear", wrapper)
            self.assertIn("execute if loaded ", wrapper)
            self.assertIn(f"run function rhd_test:internal/scene_{count}\n", wrapper)

    def test_verification_logs_missing_cells_even_without_connected_players(self):
        for count in (100, 500, 1000):
            verify = self.files[f"data/rhd_test/function/verify_{count}.mcfunction"]
            cells = self.manifest["scenes"][str(count)]["furniture_cells"]
            self.assertEqual(cells, verify.count(" run say RHD MISSING "))
            self.assertIn(f"say RHD VERIFY_{count} FINISHED expected_cells={cells}", verify)
            self.assertNotIn("tellraw @a", verify)

    def test_output_is_repeatable_and_changed_file_is_detected(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary).resolve()
            scene.save(output, self.files, False)
            before = {p.relative_to(output): p.read_bytes() for p in output.rglob("*") if p.is_file()}
            scene.save(output, self.files, False)
            self.assertEqual(before, {p.relative_to(output): p.read_bytes()
                                      for p in output.rglob("*") if p.is_file()})
            scene.save(output, self.files, True)
            (output / "pack.mcmeta").write_text("{}")
            with self.assertRaisesRegex(ValueError, "differ"):
                scene.save(output, self.files, True)

    def test_unknown_output_and_path_escape_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary).resolve()
            user_file = output / "user.txt"
            user_file.write_text("keep")
            with self.assertRaisesRegex(ValueError, "nonempty"):
                scene.save(output, self.files, False)
            self.assertEqual("keep", user_file.read_text())
            with self.assertRaisesRegex(ValueError, "escapes"):
                scene.safe_path(output, "../escape")

    def test_corrupt_catalog_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            catalog = Path(temporary) / "catalog.json"
            for entries in ([], [fixture()[0], fixture()[0]],
                            [{"id": "../bad", "parts": []}]):
                with self.subTest(entries=entries):
                    catalog.write_text(json.dumps({"schema_version": 1, "entries": entries}))
                    with self.assertRaises(ValueError):
                        scene.load_catalog(catalog)

    def test_oversized_footprint_rejected_before_forceload(self):
        entries = fixture()
        entries[0]["parts"][1]["offset"][0] = 100
        with self.assertRaisesRegex(ValueError, "256-chunk"):
            scene.render(entries, b"fixture")


if __name__ == "__main__":
    unittest.main()
