"""Regression tests that corrupt otherwise valid Minecraft asset fixtures."""
from __future__ import annotations

import copy
import json
import shutil
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

from tools.validate_resources import CATEGORIES, FACINGS, NAMESPACE, read_json, validate, validate_png

PROJECT = Path(__file__).resolve().parents[1]


def write_json(path: Path, document: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")


def png_bytes() -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    header = struct.pack(">IIBBBBB", 32, 32, 8, 2, 0, 0, 0)
    rows = (b"\x00" + bytes((110, 90, 60)) * 32) * 32
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header)
            + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b""))


class ResourceFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="rhd-assets-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.resources = self.root / "src/main/resources"
        self.assets = self.resources / "assets" / NAMESPACE
        self.data = self.resources / "data" / NAMESPACE
        self.catalog = {
            "schema_version": 1,
            "entries": [{
                "id": "chair_oak", "template": "chair", "category": "living_room",
                "names": {"en_us": "Oak chair", "ru_ru": "Дубовый стул"},
                "placement": "floor", "luminance": 0, "connect": False,
                "parts": [{"id": "chair_oak", "offset": [0, 0, 0],
                           "boxes": [[2, 0, 2, 4, 8, 4], [1, 8, 1, 15, 10, 15]]}],
            }],
        }
        self.model = {
            "textures": {"wood": f"{NAMESPACE}:block/oak", "particle": "#wood"},
            "elements": [{"from": [1, 8, 1], "to": [15, 10, 15],
                          "faces": {face: {"texture": "#wood", "uv": [0, 0, 16, 16]}
                                    for face in ("north", "south", "west", "east", "up", "down")}}],
        }
        self.save_catalog()
        write_json(self.assets / "models/block/chair_oak.json", self.model)
        write_json(self.assets / "models/item/chair_oak.json", {"parent": f"{NAMESPACE}:block/chair_oak"})
        write_json(self.assets / "items/chair_oak.json", {
            "model": {"type": "minecraft:model", "model": f"{NAMESPACE}:item/chair_oak"},
        })
        self.write_part("chair_oak", True)
        for language, name in self.catalog["entries"][0]["names"].items():
            translations = {f"itemGroup.{NAMESPACE}.{category}": category for category in CATEGORIES}
            translations[f"block.{NAMESPACE}.chair_oak"] = name
            write_json(self.assets / "lang" / f"{language}.json", translations)
        texture = self.assets / "textures/block/oak.png"
        texture.parent.mkdir(parents=True)
        texture.write_bytes(png_bytes())

    def save_catalog(self) -> None:
        write_json(self.data / "catalog.json", self.catalog)

    def write_part(self, identifier: str, primary: bool) -> None:
        write_json(self.assets / "blockstates" / f"{identifier}.json", {
            "variants": {f"facing={direction}": {"model": f"{NAMESPACE}:block/chair_oak", "y": angle}
                         for direction, angle in FACINGS.items()},
        })
        pools = [{"rolls": 1, "entries": [{"type": "minecraft:item", "name": f"{NAMESPACE}:chair_oak"}],
                  "conditions": [{"condition": "minecraft:survives_explosion"}]}] if primary else []
        write_json(self.data / "loot_table/blocks" / f"{identifier}.json", {
            "type": "minecraft:block", "pools": pools,
        })

    def assert_invalid(self, message: str) -> None:
        report = validate(self.root)
        self.assertFalse(report.ok)
        self.assertTrue(any(message in error for error in report.errors), report.errors)

    def test_complete_fixture_passes(self) -> None:
        report = validate(self.root)
        self.assertEqual([], report.errors)
        self.assertEqual(1, report.counts["items"])
        self.assertEqual(1, report.counts["textures"])
        self.assertEqual(2, report.counts["models"])

    def test_duplicate_json_keys_fail(self) -> None:
        path = self.assets / "lang/en_us.json"
        path.write_text('{"name": "first", "name": "second"}', encoding="utf-8")
        self.assert_invalid("duplicate JSON key")

    def test_nan_json_numbers_fail(self) -> None:
        path = self.assets / "models/block/chair_oak.json"
        path.write_text('{"elements": [NaN]}', encoding="utf-8")
        self.assert_invalid("non-finite JSON number")

    def test_missing_catalog_fails(self) -> None:
        (self.data / "catalog.json").unlink()
        self.assert_invalid("catalog.json")

    def test_empty_catalog_fails(self) -> None:
        self.catalog["entries"] = []
        self.save_catalog()
        self.assert_invalid("nonempty array")

    def test_invalid_identifier_fails(self) -> None:
        self.catalog["entries"][0]["id"] = "../bad"
        self.save_catalog()
        self.assert_invalid("invalid identifier")

    def test_duplicate_registration_fails(self) -> None:
        self.catalog["entries"].append(copy.deepcopy(self.catalog["entries"][0]))
        self.save_catalog()
        self.assert_invalid("duplicate item registration")
        self.assert_invalid("duplicate block registration")

    def test_unknown_category_fails(self) -> None:
        self.catalog["entries"][0]["category"] = "invented_room"
        self.save_catalog()
        self.assert_invalid("unknown category")

    def test_missing_localization_fails(self) -> None:
        write_json(self.assets / "lang/ru_ru.json", {})
        self.assert_invalid("missing translation")

    def test_localization_must_match_catalog(self) -> None:
        path = self.assets / "lang/en_us.json"
        translations = read_json(path)
        translations[f"block.{NAMESPACE}.chair_oak"] = "Wrong chair"
        write_json(path, translations)
        self.assert_invalid("name differs")

    def test_legacy_item_format_fails(self) -> None:
        write_json(self.assets / "items/chair_oak.json", {"parent": f"{NAMESPACE}:block/chair_oak"})
        self.assert_invalid("1.21.11")

    def test_missing_item_model_fails(self) -> None:
        (self.assets / "models/item/chair_oak.json").unlink()
        self.assert_invalid("models/item/chair_oak.json")

    def test_parent_cycle_fails(self) -> None:
        write_json(self.assets / "models/block/chair_oak.json", {"parent": f"{NAMESPACE}:item/chair_oak"})
        self.assert_invalid("cyclic model parent")

    def test_missing_texture_fails(self) -> None:
        (self.assets / "textures/block/oak.png").unlink()
        self.assert_invalid("missing texture")

    def test_unresolved_texture_alias_fails(self) -> None:
        self.model["elements"][0]["faces"]["north"]["texture"] = "#missing"
        write_json(self.assets / "models/block/chair_oak.json", self.model)
        self.assert_invalid("unresolved texture alias")

    def test_texture_alias_cycle_fails(self) -> None:
        self.model["textures"]["wood"] = "#particle"
        write_json(self.assets / "models/block/chair_oak.json", self.model)
        self.assert_invalid("cyclic texture alias")

    def test_inherited_geometry_resolves_child_materials(self) -> None:
        shape = {"elements": self.model["elements"]}
        write_json(self.assets / "models/block/chair_shape.json", shape)
        write_json(self.assets / "models/block/chair_oak.json", {
            "parent": f"{NAMESPACE}:block/chair_shape", "textures": self.model["textures"],
        })
        self.assertEqual([], validate(self.root).errors)

    def test_bad_png_checksum_fails(self) -> None:
        path = self.assets / "textures/block/oak.png"
        raw = bytearray(path.read_bytes())
        raw[20] ^= 1
        path.write_bytes(raw)
        self.assert_invalid("CRC mismatch")

    def test_bad_png_signature_fails(self) -> None:
        (self.assets / "textures/block/oak.png").write_bytes(b"not a png")
        self.assert_invalid("invalid PNG signature")

    def test_png_decodes_expected_dimensions(self) -> None:
        self.assertEqual((32, 32), validate_png(self.assets / "textures/block/oak.png"))

    def test_inverted_collision_fails(self) -> None:
        self.catalog["entries"][0]["parts"][0]["boxes"][0] = [4, 0, 2, 2, 8, 4]
        self.save_catalog()
        self.assert_invalid("invalid collision box")

    def test_collision_budget_excess_fails(self) -> None:
        self.catalog["entries"][0]["parts"][0]["boxes"] = [[1, 1, 1, 2, 2, 2]] * 13
        self.save_catalog()
        self.assert_invalid("collision budget")

    def test_collision_outside_cell_fails(self) -> None:
        self.catalog["entries"][0]["parts"][0]["boxes"][0] = [0, 0, 0, 17, 8, 4]
        self.save_catalog()
        self.assert_invalid("invalid collision box")

    def test_geometry_outside_cell_fails(self) -> None:
        self.model["elements"][0]["to"] = [17, 10, 15]
        write_json(self.assets / "models/block/chair_oak.json", self.model)
        self.assert_invalid("coordinate bounds")

    def test_invalid_uv_fails(self) -> None:
        self.model["elements"][0]["faces"]["north"]["uv"] = [0, 0, 32, 16]
        write_json(self.assets / "models/block/chair_oak.json", self.model)
        self.assert_invalid("UV outside")

    def test_invalid_rotation_fails(self) -> None:
        self.model["elements"][0]["rotation"] = {"axis": "y", "angle": 30, "origin": [8, 8, 8]}
        write_json(self.assets / "models/block/chair_oak.json", self.model)
        self.assert_invalid("model rotation")

    def test_wrong_facing_rotation_fails(self) -> None:
        path = self.assets / "blockstates/chair_oak.json"
        document = read_json(path)
        document["variants"]["facing=east"]["y"] = 270
        write_json(path, document)
        self.assert_invalid("incorrect facing rotation")

    def test_missing_blockstate_direction_fails(self) -> None:
        path = self.assets / "blockstates/chair_oak.json"
        document = read_json(path)
        del document["variants"]["facing=east"]
        write_json(path, document)
        self.assert_invalid("variants do not match")

    def test_orphan_item_fails(self) -> None:
        write_json(self.assets / "items/unregistered.json", {"model": {"type": "minecraft:model", "model": "minecraft:block/stone"}})
        self.assert_invalid("orphan resource")

    def test_extra_primary_loot_rolls_fail(self) -> None:
        path = self.data / "loot_table/blocks/chair_oak.json"
        document = read_json(path)
        document["pools"][0]["rolls"] = 2
        write_json(path, document)
        self.assert_invalid("primary loot")

    def test_missing_creative_group_localization_fails(self) -> None:
        path = self.assets / "lang/en_us.json"
        translations = read_json(path)
        del translations[f"itemGroup.{NAMESPACE}.garage"]
        write_json(path, translations)
        self.assert_invalid("creative tab translation")

    def test_missing_connection_collisions_fail(self) -> None:
        self.catalog["entries"][0]["connect"] = True
        self.save_catalog()
        self.assert_invalid("connection_boxes")

    def test_model_reference_cannot_escape_assets(self) -> None:
        self.model["parent"] = f"{NAMESPACE}:/tmp/outside"
        write_json(self.assets / "models/block/chair_oak.json", self.model)
        self.assert_invalid("invalid resource location")

    def test_wrong_primary_loot_fails(self) -> None:
        path = self.data / "loot_table/blocks/chair_oak.json"
        document = read_json(path)
        document["pools"][0]["entries"][0]["name"] = "minecraft:diamond"
        write_json(path, document)
        self.assert_invalid("primary loot")

    def test_multicell_fixture_passes(self) -> None:
        self.catalog["entries"][0]["parts"].append({
            "id": "chair_oak_part_1", "offset": [0, 1, 0], "boxes": [[2, 0, 12, 14, 8, 15]],
        })
        self.save_catalog()
        self.write_part("chair_oak_part_1", False)
        report = validate(self.root)
        self.assertEqual([], report.errors)
        self.assertEqual(2, report.counts["blocks"])

    def test_secondary_loot_would_duplicate_fails(self) -> None:
        self.catalog["entries"][0]["parts"].append({
            "id": "chair_oak_part_1", "offset": [0, 1, 0], "boxes": [],
        })
        self.save_catalog()
        self.write_part("chair_oak_part_1", True)
        self.assert_invalid("duplicate loot")

    def test_duplicate_multicell_offset_fails(self) -> None:
        self.catalog["entries"][0]["parts"].append({
            "id": "chair_oak_part_1", "offset": [0, 0, 0], "boxes": [],
        })
        self.save_catalog()
        self.write_part("chair_oak_part_1", False)
        self.assert_invalid("duplicate cell offset")

    def test_connection_variants_cover_all_runtime_states(self) -> None:
        self.catalog["entries"][0]["connect"] = True
        part = self.catalog["entries"][0]["parts"][0]
        part["connection_boxes"] = {f"{left}_{right}": copy.deepcopy(part["boxes"])
                                    for left in ("false", "true") for right in ("false", "true")}
        self.save_catalog()
        variants = {
            f"facing={direction},left={left},right={right}": {"model": f"{NAMESPACE}:block/chair_oak", "y": angle}
            for direction, angle in FACINGS.items()
            for left in ("false", "true") for right in ("false", "true")
        }
        write_json(self.assets / "blockstates/chair_oak.json", {"variants": variants})
        self.assertEqual([], validate(self.root).errors)

    def test_connection_without_variants_fails(self) -> None:
        self.catalog["entries"][0]["connect"] = True
        self.save_catalog()
        self.assert_invalid("variants do not match")

    def test_cli_preserves_failure_exit_status(self) -> None:
        (self.assets / "textures/block/oak.png").unlink()
        result = subprocess.run([sys.executable, str(PROJECT / "tools/validate_resources.py"),
                                 "--root", str(self.root)], text=True, capture_output=True)
        self.assertEqual(1, result.returncode)
        self.assertIn("missing texture", result.stderr)


class RuntimeGeometry(unittest.TestCase):
    def test_actual_java_shape_and_offset_rotations(self) -> None:
        source = PROJECT / "src/main/java/com/realistichomedecor/util/FurnitureGeometry.java"
        harness = PROJECT / "tests/java/FurnitureGeometryTest.java"
        with tempfile.TemporaryDirectory(prefix="rhd-geometry-") as directory:
            compiler = (["javac"] if shutil.which("javac") else
                        ["java", "--module", "jdk.compiler/com.sun.tools.javac.Main"])
            compiled = subprocess.run([*compiler, "-d", directory, str(source), str(harness)],
                                      text=True, capture_output=True)
            self.assertEqual(0, compiled.returncode, compiled.stderr)
            result = subprocess.run(["java", "-cp", directory, "FurnitureGeometryTest"],
                                    text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn("assertions passed", result.stdout)


class GeneratedProject(unittest.TestCase):
    def test_generated_project_resources(self) -> None:
        catalog = PROJECT / "src/main/resources/data" / NAMESPACE / "catalog.json"
        if not catalog.exists():
            self.skipTest("generator has not produced project resources yet")
        report = validate(PROJECT)
        self.assertEqual([], report.errors, "\n".join(report.errors[:30]))
        self.assertGreaterEqual(report.counts["items"], 20)
        self.assertGreaterEqual(report.counts["categories"], 6)
        if report.counts["items"] >= 300:
            self.assertEqual(11, report.counts["categories"])


if __name__ == "__main__":
    unittest.main()
