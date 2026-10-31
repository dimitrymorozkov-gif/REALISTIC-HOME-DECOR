#!/usr/bin/env python3
"""Build an opt-in Minecraft 1.21.11 wall showcase datapack; never modify a world.

Default output: build/wall-gallery. An operator must explicitly invoke the
generated functions to place/clear blocks in a disposable test world.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "src/main/resources/data/realistic_home_decor/catalog.json"
GENERATOR = "realistic_home_decor.wall_gallery.v1"
PALETTES = ("oak", "walnut", "ebony", "ivory", "sand", "slate", "terracotta", "sage")
FAMILIES = ("masonry", "stone", "wood", "plaster", "concrete", "metal", "acoustic")
IDENTIFIER = re.compile(r"[a-z0-9_]+\Z")
WIDTH, DEPTH, TOP = 64, 48, 6


def encode(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def coordinates(position: list[int] | tuple[int, int, int]) -> str:
    return " ".join("~" if value == 0 else f"~{value}" for value in position)


def load_walls(data: bytes) -> list[dict[str, Any]]:
    catalog = json.loads(data)
    if not isinstance(catalog, dict) or catalog.get("schema_version") != 1:
        raise ValueError("Expected catalog schema_version=1")
    if not isinstance(catalog.get("entries"), list):
        raise ValueError("Catalog entries must be a list")
    grouped: dict[str, dict[str, Any]] = {}
    ids: set[str] = set()
    for entry in catalog["entries"]:
        if not isinstance(entry, dict):
            raise ValueError("Catalog entries must be objects")
        if "wall_family" not in entry:
            continue
        template, identifier, palette = entry.get("template"), entry.get("id"), entry.get("material")
        if (not isinstance(template, str) or not IDENTIFIER.fullmatch(template)
                or not isinstance(identifier, str) or not IDENTIFIER.fullmatch(identifier)
                or identifier in ids):
            raise ValueError("Invalid or duplicate wall identifier")
        if palette not in PALETTES or identifier != f"{template}_{palette}":
            raise ValueError(f"Invalid wall palette/id: {identifier}")
        if entry["wall_family"] not in FAMILIES:
            raise ValueError(f"Unsupported wall family: {entry['wall_family']}")
        if entry.get("placement") != "any" or entry.get("connect"):
            raise ValueError(f"Gallery requires independently stackable walls: {identifier}")
        parts = entry.get("parts", [])
        if len(parts) != 1 or parts[0].get("id") != identifier or parts[0].get("offset") != [0, 0, 0]:
            raise ValueError(f"Gallery requires single-cell walls: {identifier}")
        group = grouped.setdefault(template, {})
        if palette in group:
            raise ValueError(f"Duplicate palette for {template}")
        if group and next(iter(group.values()))["wall_family"] != entry["wall_family"]:
            raise ValueError(f"Inconsistent wall family for {template}")
        group[palette] = entry
        ids.add(identifier)
    if not grouped or len(grouped) > 40:
        raise ValueError("Gallery supports 1–40 new wall templates marked wall_family")
    for template, variants in grouped.items():
        if set(variants) != set(PALETTES):
            raise ValueError(f"Incomplete eight-palette matrix for {template}")
    return [{"template": template, "family": variants["oak"]["wall_family"], "variants": variants}
            for template, variants in sorted(grouped.items(), key=lambda pair: (
                FAMILIES.index(pair[1]["oak"]["wall_family"]), pair[0]))]


def render(data: bytes) -> dict[str, str]:
    walls = load_walls(data)
    files: dict[str, str] = {}
    prefix = "data/rhd_walls/function/"

    def function(name: str, lines: list[str]) -> None:
        files[prefix + name + ".mcfunction"] = "\n".join(lines) + "\n"

    # Official Minecraft 1.21.11 version.json: data_major=94, data_minor=1.
    files["pack.mcmeta"] = encode({"pack": {"description": "RHD: 40 wall types, eight palettes; explicit test-world gallery",
                                              "min_format": [94, 1], "max_format": [94, 1]}})
    clear = ["# DESTRUCTIVE: relative [0,-1,0]..[63,6,47], including the gallery floor.",
             "fill ~ ~-1 ~ ~63 ~6 ~47 minecraft:air"]
    function("internal/clear", clear)
    build = ["# Test world only. No entities, automatic functions, or global gamerule changes.",
             "function rhd_walls:internal/clear",
             "fill ~ ~-1 ~ ~63 ~-1 ~47 minecraft:smooth_stone"]
    verify = ["# Checks all display blocks after placement or after a world reload."]
    bays = []
    expected = []
    for index, wall in enumerate(walls):
        row, column = divmod(index, 8)
        x, z = 3 + column * 7, 6 + row * 8
        oak = wall["variants"]["oak"]
        state = f"realistic_home_decor:{oak['id']}[facing=north]"
        build.append(f"fill {coordinates((x, 0, z))} {coordinates((x + 2, 2, z))} {state}")
        for dx in range(3):
            for dy in range(3):
                expected.append({"id": oak["id"], "position": [x + dx, dy, z]})
        samples = []
        for palette_index, palette in enumerate(PALETTES):
            entry = wall["variants"][palette]
            # A viewer north of the wall looks south: +X appears on their left.
            position = [x + 3 - palette_index % 4, 4 + palette_index // 4, z]
            build.append(f"setblock {coordinates(position)} realistic_home_decor:{entry['id']}[facing=north]")
            sample = {"id": entry["id"], "palette": palette, "position": position}
            samples.append(sample)
            expected.append({"id": entry["id"], "position": position})
        bays.append({"index": index + 1, "row": row + 1, "column": column + 1,
                     "template": wall["template"], "wall_family": wall["family"],
                     "name_en": oak.get("names", {}).get("en_us"), "name_ru": oak.get("names", {}).get("ru_ru"),
                     "patch": {"id": oak["id"], "min": [x, 0, z], "max": [x + 2, 2, z]},
                     "palette_samples": samples})
    for block in expected:
        position = coordinates(block["position"])
        verify.append(f"execute unless block {position} realistic_home_decor:{block['id']}[facing=north] "
                      f"run say RHD_WALL_GALLERY_MISSING {block['id']} at {block['position']}")
    build.append(f"say RHD_WALL_GALLERY_BUILT templates={len(walls)} palettes=8 display_blocks={len(expected)}")
    verify.append(f"say RHD_WALL_GALLERY_VERIFIED expected_blocks={len(expected)}. Any MISSING line means failure.")
    function("internal/build", build)
    function("verify", verify)
    # Check every touched chunk, including far edges for a non-aligned origin.
    probes_x = (0, 16, 32, 48, 63)
    probes_z = (0, 16, 32, 47)
    loaded = " ".join(f"if loaded {coordinates((x, 0, z))}" for x in probes_x for z in probes_z)
    for public, internal in (("build", "build"), ("clear", "clear")):
        function(public, ["# TEST WORLD ONLY. Refuses to modify an incompletely loaded region.",
                          f"execute {loaded} run function rhd_walls:internal/{internal}"])
    function("prepare", ["# Force-loads the bounded test region; wait at least five seconds before build.",
                         "forceload add ~ ~ ~63 ~47", "say RHD_WALL_GALLERY_PREPARED wait five seconds, then build at the SAME origin."])
    function("release", ["# Test world only: also removes any pre-existing forced status in this region.",
                         "forceload remove ~ ~ ~63 ~47", "say RHD_WALL_GALLERY_RELEASED blocks remain."])
    manifest = {"generator": GENERATOR, "minecraft": "1.21.11", "data_pack_format": [94, 1],
                "catalog_sha256": hashlib.sha256(data).hexdigest(), "wall_templates": len(walls),
                "palette_order": list(PALETTES), "palette_variants": len(walls) * len(PALETTES),
                "display_blocks": len(expected), "bounds_relative": {"min": [0, -1, 0], "max": [63, 6, 47]},
                "suggested_origin": [0, 81, 0], "rows": 5, "columns": 8,
                "warning": "Destructive opt-in test-world functions. No blocks are placed by this Python tool.",
                "bays": bays, "owned_files": sorted([*files, "gallery_manifest.json"])}
    files["gallery_manifest.json"] = encode(manifest)
    return files


def save(output: Path, files: dict[str, str], check: bool = False) -> None:
    output = output.resolve()
    marker = output / "gallery_manifest.json"
    previous: set[str] = set()
    if output.exists() and any(output.iterdir()):
        if not marker.is_file():
            raise ValueError("Output is nonempty and has no wall-gallery manifest; choose an empty directory")
        metadata = json.loads(marker.read_text(encoding="utf-8"))
        if metadata.get("generator") != GENERATOR or not isinstance(metadata.get("owned_files"), list):
            raise ValueError("Unrecognized output manifest; refusing to overwrite")
        previous = set(metadata["owned_files"])
        for name in previous:
            if not isinstance(name, str) or not (output / name).resolve().is_relative_to(output):
                raise ValueError("Unsafe path in output manifest")
        for existing in output.rglob("*"):
            if existing.is_symlink() or (existing.is_file() and str(existing.relative_to(output)) not in previous):
                raise ValueError(f"Unexpected output entry; refusing to overwrite: {existing.relative_to(output)}")
    for name in files:
        if not (output / name).resolve().is_relative_to(output):
            raise ValueError("Generated path escapes output")
    if check:
        different = [name for name, value in files.items() if not (output / name).is_file()
                     or (output / name).read_text(encoding="utf-8") != value]
        if different or previous - files.keys():
            raise ValueError("Gallery output differs: " + ", ".join(different[:6]))
        return
    for name in previous - files.keys():
        if (output / name).is_file():
            (output / name).unlink()
    for name, value in sorted(files.items()):
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value, encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    parser.add_argument("--output", type=Path, default=ROOT / "build/wall-gallery")
    parser.add_argument("--check", action="store_true", help="Check generated files without changing them")
    args = parser.parse_args(argv)
    try:
        output = args.output.resolve()
        protected = ("src", "tools", "tests", "docs", ".git", ".agents")
        if output == ROOT or ROOT.is_relative_to(output) or any(output.is_relative_to(ROOT / name) for name in protected):
            raise ValueError("Output must be a generated directory outside project sources")
        files = render(args.catalog.read_bytes())
        save(output, files, args.check)
        manifest = json.loads(files["gallery_manifest.json"])
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        parser.exit(1, f"wall_gallery: {error}\n")
    print(f"{'Verified' if args.check else 'Generated'} wall gallery: {manifest['wall_templates']} templates, "
          f"{manifest['palette_variants']} variants, {manifest['display_blocks']} display blocks: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
