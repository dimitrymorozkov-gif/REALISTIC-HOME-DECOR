"""Compatibility and rendered-asset checks for the eight-palette wall expansion.

The legacy ID fixture was extracted from the actual 320-item catalog at commit
499a9bd5d82bfcc6534722e018999f0a5729217e (catalog SHA256
c3b885bb5eeef9a816073771a0359f3e79054b3ebaa9c22c61a5adc606ccb1f1).
Geometry checks compare occupied solids, so subdividing a cube or hiding new
cuboids inside it cannot turn an alias into an additional wall design.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import unittest
import zlib

from tools.validate_resources import NAMESPACE, Validator

PROJECT = Path(__file__).resolve().parents[1]
GENERATOR_DIRECTORY = PROJECT / "tools/furniture_generator"
OLD_PALETTES = ("oak", "walnut", "ebony", "ivory")
NEW_PALETTES = ("sage", "terracotta", "sand", "slate")
PALETTES = OLD_PALETTES + NEW_PALETTES


def import_generator_module(name: str):
    """Load the real development source without invoking its writing CLI."""
    source = GENERATOR_DIRECTORY / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"rhd_test_{name}", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import generator module {source}")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(GENERATOR_DIRECTORY))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def solid_union(boxes):
    """Canonical exact union of axis-aligned cuboids, independent of partition."""
    # The resource compiler serializes coordinates to five decimal places.
    # Normalize before union/rotation to ignore floating-point evaluation noise.
    boxes = [tuple(round(float(v), 5) for v in box[:6]) for box in boxes]
    if not boxes:
        return ()
    xs = sorted({value for b in boxes for value in (b[0], b[3])})
    slabs = []
    for low_x, high_x in zip(xs, xs[1:]):
        active = [b for b in boxes if b[0] <= low_x and b[3] >= high_x]
        ys = sorted({value for b in active for value in (b[1], b[4])})
        rows = []
        for low_y, high_y in zip(ys, ys[1:]):
            intervals = sorted((b[2], b[5]) for b in active if b[1] <= low_y and b[4] >= high_y)
            merged_z = []
            for low_z, high_z in intervals:
                if merged_z and low_z <= merged_z[-1][1]:
                    merged_z[-1] = (merged_z[-1][0], max(high_z, merged_z[-1][1]))
                else:
                    merged_z.append((low_z, high_z))
            if not merged_z:
                continue
            coverage = tuple(merged_z)
            if rows and rows[-1][1] == low_y and rows[-1][2] == coverage:
                rows[-1] = (rows[-1][0], high_y, coverage)
            else:
                rows.append((low_y, high_y, coverage))
        if not rows:
            continue
        coverage = tuple(rows)
        if slabs and slabs[-1][1] == low_x and slabs[-1][2] == coverage:
            slabs[-1] = (slabs[-1][0], high_x, coverage)
        else:
            slabs.append((low_x, high_x, coverage))
    return tuple(slabs)


def rotate_boxes(boxes):
    return [(16 - b[5], b[1], b[0], 16 - b[2], b[4], b[3]) for b in boxes]


def structural_fingerprint(boxes):
    """A rotation of an existing wall is also an alias, not a new design."""
    fingerprints = []
    boxes = [tuple(b[:6]) for b in boxes]
    for _ in range(4):
        fingerprints.append(solid_union(boxes))
        boxes = rotate_boxes(boxes)
    return min(fingerprints)


def pixel_digest(path: Path):
    """Compare decoded pixels, not filenames, PNG metadata or compression."""
    raw = path.read_bytes()
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Invalid PNG signature")
    offset, compressed = 8, bytearray()
    width = height = channels = 0
    while offset < len(raw):
        length = struct.unpack_from(">I", raw, offset)[0]
        tag = raw[offset + 4:offset + 8]
        data = raw[offset + 8:offset + 8 + length]
        if tag == b"IHDR":
            width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", data)
            if depth != 8 or color not in (2, 6) or compression or filtering or interlace:
                raise ValueError("Expected a validated 8-bit RGB/RGBA PNG")
            channels = 3 if color == 2 else 4
        elif tag == b"IDAT":
            compressed.extend(data)
        offset += 12 + length
    data = zlib.decompress(compressed)
    stride = width * channels
    previous = bytes(stride)
    pixels = bytearray()
    for y in range(height):
        start = y * (stride + 1)
        filter_kind = data[start]
        row = bytearray(data[start + 1:start + stride + 1])
        for x in range(stride):
            left = row[x - channels] if x >= channels else 0
            up = previous[x]
            diagonal = previous[x - channels] if x >= channels else 0
            if filter_kind == 1:
                predictor = left
            elif filter_kind == 2:
                predictor = up
            elif filter_kind == 3:
                predictor = (left + up) // 2
            elif filter_kind == 4:
                p = left + up - diagonal
                distances = (abs(p - left), abs(p - up), abs(p - diagonal))
                predictor = (left, up, diagonal)[distances.index(min(distances))]
            elif filter_kind == 0:
                predictor = 0
            else:
                raise ValueError("Invalid PNG row filter")
            row[x] = (row[x] + predictor) & 255
        if channels == 4:
            pixels.extend(row)
        else:
            for x in range(0, len(row), channels):
                pixels.extend(row[x:x + 3])
                pixels.append(255)
        previous = row
    return width, height, hashlib.sha256(pixels).hexdigest()


class SolidComparison(unittest.TestCase):
    def test_repartitioned_and_hidden_boxes_do_not_create_unique_walls(self):
        solid = [(0, 0, 2, 16, 16, 16)]
        repartitioned = [(0, 0, 2, 8, 16, 16), (8, 0, 2, 16, 8, 16),
                         (8, 8, 2, 16, 16, 16), (1, 1, 3, 2, 2, 4)]
        self.assertEqual(structural_fingerprint(solid), structural_fingerprint(repartitioned))

    def test_rotation_does_not_create_unique_wall(self):
        source = [(0, 0, 3, 16, 16, 16), (0, 0, 1, 2, 16, 3)]
        self.assertEqual(structural_fingerprint(source), structural_fingerprint(rotate_boxes(source)))

    def test_exposed_relief_changes_occupied_geometry(self):
        core = [(0, 0, 3, 16, 16, 16)]
        self.assertNotEqual(structural_fingerprint(core),
                            structural_fingerprint(core + [(0, 0, 1, 2, 16, 3)]))


class ExpandedCatalog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator = import_generator_module("generate")
        sys.path.insert(0, str(GENERATOR_DIRECTORY))
        try:
            cls.wall_designs = import_generator_module("walls").designs()
        finally:
            sys.path.pop(0)
        cls.catalog = json.loads((PROJECT / "src/main/resources/data" / NAMESPACE / "catalog.json").read_text())["entries"]
        cls.entries = {entry["id"]: entry for entry in cls.catalog}
        cls.by_template = {}
        for entry in cls.catalog:
            cls.by_template.setdefault(entry["template"], {})[entry["material"]] = entry
        cls.legacy_ids = set(json.loads((PROJECT / "tests/fixtures/original_item_ids.json").read_text()))
        cls.validator = Validator(PROJECT)
        cls.texture_pixels = {}

    def effective_models(self, entry):
        models = []
        for part in entry["parts"]:
            path = self.validator.assets / "blockstates" / f"{part['id']}.json"
            variants = json.loads(path.read_text())["variants"]
            key = "facing=north,left=false,right=false" if entry["connect"] else "facing=north"
            models.append(self.validator.model(variants[key]["model"]))
        return models

    def material_fingerprint(self, entry):
        materials = set()
        for model, textures in self.effective_models(entry):
            for element in model["elements"]:
                for face in element["faces"].values():
                    texture = face["texture"]
                    visited = set()
                    while texture.startswith("#"):
                        self.assertNotIn(texture, visited, "Cyclic effective texture alias")
                        visited.add(texture)
                        texture = textures[texture[1:]]
                    namespace, relative = texture.split(":", 1)
                    self.assertEqual(NAMESPACE, namespace)
                    if texture not in self.texture_pixels:
                        path = self.validator.assets / "textures" / f"{relative}.png"
                        self.texture_pixels[texture] = pixel_digest(path)
                    materials.add(self.texture_pixels[texture])
        self.assertTrue(materials, entry["id"])
        return tuple(sorted(materials))

    def test_original_320_item_ids_and_collision_shapes_remain_unchanged(self):
        self.assertEqual(320, len(self.legacy_ids))
        self.assertTrue(self.legacy_ids.issubset(self.entries),
                        sorted(self.legacy_ids - self.entries.keys()))
        expected_old = {f"{template}_{palette}" for template in self.by_template
                        if template not in {wall["id"] for wall in self.wall_designs}
                        for palette in OLD_PALETTES}
        self.assertEqual(self.legacy_ids, expected_old)
        profiles = json.loads((PROJECT / "tests/fixtures/original_collision_shapes.json").read_text())
        self.assertEqual(80, len(profiles))
        for identifier in self.legacy_ids:
            with self.subTest(legacy_item=identifier):
                entry = self.entries[identifier]
                actual = [{key: value for key, value in part.items() if key != "id"}
                          for part in entry["parts"]]
                self.assertEqual(profiles[entry["template"]], actual,
                                 "The structural-wall collision change must not alter legacy furniture")

    def test_original_palette_names_bindings_and_texture_bytes_are_preserved(self):
        baseline = json.loads((PROJECT / "tests/fixtures/original_palette_bindings.json").read_text())
        self.assertEqual(set(OLD_PALETTES), set(baseline["palettes"]))
        for palette, original in baseline["palettes"].items():
            with self.subTest(palette=palette):
                self.assertEqual(original, {key: self.generator.PALETTES[palette][key] for key in original})
        self.assertEqual(37, len(baseline["texture_sha256"]))
        for relative, digest in baseline["texture_sha256"].items():
            with self.subTest(texture=relative):
                self.assertEqual(digest, hashlib.sha256((PROJECT / relative).read_bytes()).hexdigest())

    def test_all_120_designs_have_all_eight_palette_item_resources(self):
        self.assertEqual(set(PALETTES), set(self.generator.PALETTES))
        self.assertEqual(120, len(self.by_template))
        self.assertEqual(960, len(self.catalog))
        self.assertEqual(960, len(self.entries))
        for template, variants in self.by_template.items():
            with self.subTest(template=template):
                self.assertEqual(set(PALETTES), set(variants))
                for palette, entry in variants.items():
                    self.assertEqual(f"{template}_{palette}", entry["id"])
                    self.assertTrue((self.validator.assets / "items" / f"{entry['id']}.json").is_file())

    def test_new_walls_are_40_distinct_effective_solids(self):
        self.assertEqual(40, len(self.wall_designs))
        legacy_templates = {identifier.rsplit("_", 1)[0] for identifier in self.legacy_ids}
        new_templates = set(self.by_template) - legacy_templates
        self.assertEqual({design["id"] for design in self.wall_designs}, new_templates)
        seen = {}
        for design in self.wall_designs:
            with self.subTest(design=design["id"]):
                self.assertTrue(design["id"].startswith("wall_"))
                entry = self.by_template[design["id"]]["oak"]
                models = self.effective_models(entry)
                self.assertEqual(1, len(models))
                elements = models[0][0]["elements"]
                boxes = [tuple(element["from"] + element["to"]) for element in elements]
                signature = structural_fingerprint(boxes)
                self.assertNotIn(signature, seen, f"{design['id']} aliases {seen.get(signature)}")
                seen[signature] = design["id"]
                self.assertEqual(structural_fingerprint(design["boxes"]), signature)
        self.assertEqual(40, len(seen))

    def test_walls_are_structural_single_cell_building_materials(self):
        for design in self.wall_designs:
            for entry in self.by_template[design["id"]].values():
                with self.subTest(item=entry["id"]):
                    self.assertEqual("building_materials", entry["category"])
                    self.assertEqual("any", entry["placement"])
                    self.assertFalse(entry["connect"])
                    self.assertEqual(1, len(entry["parts"]))
                    part = entry["parts"][0]
                    self.assertEqual([0, 0, 0], part["offset"])
                    self.assertEqual(entry["id"], part["id"])
                    # Structural walls behave as ordinary one-metre Minecraft
                    # building blocks. Their rendered relief remains independent
                    # and is compared above using actual model geometry.
                    self.assertEqual([[0, 0, 0, 16, 16, 16]], part["boxes"],
                                     "New structural walls require normal full-cell collision/selection")
                    for model, _ in self.effective_models(entry):
                        for element in model["elements"]:
                            self.assertTrue(all(0 <= value <= 16 for value in element["from"] + element["to"]))
                            self.assertTrue(all(a < b for a, b in zip(element["from"], element["to"])))

    def test_each_new_wall_has_eight_effectively_different_material_palettes(self):
        for design in self.wall_designs:
            with self.subTest(design=design["id"]):
                variants = self.by_template[design["id"]]
                fingerprints = {self.material_fingerprint(variants[palette]) for palette in PALETTES}
                self.assertEqual(8, len(fingerprints), "Renamed or unused texture bindings do not count as a palette")

    def test_existing_furniture_and_materials_use_eight_rendered_palettes(self):
        # Include formerly fixed ceramic/concrete surfaces, not just wooden chairs.
        representatives = ("modern_chair", "dining_table", "modern_sofa", "kitchen_cabinet",
                           "toilet", "vase", "concrete_block", "ceramic_tiles")
        for template in representatives:
            with self.subTest(template=template):
                variants = self.by_template[template]
                self.assertEqual(8, len({self.material_fingerprint(variants[palette]) for palette in PALETTES}))


if __name__ == "__main__":
    unittest.main()
