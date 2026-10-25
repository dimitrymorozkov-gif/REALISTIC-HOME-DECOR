#!/usr/bin/env python3
"""Generate opt-in Minecraft 1.21.11 furniture test datapacks; never edit a world.

Run from any directory. Output defaults to this checkout's build/test-datapack.
Only the Python standard library is required. Actual placement happens only when
a player/operator explicitly invokes the generated rhd_test functions in-game.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "src/main/resources/data/realistic_home_decor/catalog.json"
COUNTS = (100, 500, 1000)
NAMESPACE = "realistic_home_decor"
GENERATOR = "realistic_home_decor.scene_generator.v1"
IDENTIFIER = re.compile(r"[a-z0-9_]+\Z")


def encode(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def relative(value: int) -> str:
    return "~" if value == 0 else f"~{value}"


def coordinates(position: tuple[int, int, int] | list[int]) -> str:
    return " ".join(relative(value) for value in position)


def message(text: str, color: str = "gray") -> str:
    return "tellraw @a " + json.dumps({"text": text, "color": color}, ensure_ascii=False)


def load_catalog(path: Path) -> list[dict[str, Any]]:
    catalog = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(catalog, dict) or catalog.get("schema_version") != 1:
        raise ValueError("Expected furniture catalog schema_version=1")
    entries = catalog.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Catalog has no furniture entries; run generateResources first")
    seen: set[str] = set()
    all_part_ids: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Catalog entries must be objects")
        identifier = entry.get("id", "")
        if not isinstance(identifier, str) or not IDENTIFIER.fullmatch(identifier) or identifier in seen:
            raise ValueError(f"Invalid or duplicate furniture id: {identifier!r}")
        seen.add(identifier)
        if entry.get("placement") not in {"floor", "wall", "ceiling", "any"}:
            raise ValueError(f"Unsupported placement for {identifier}")
        parts = entry.get("parts")
        if not isinstance(parts, list) or not parts:
            raise ValueError(f"Missing parts for {identifier}")
        occupied: set[tuple[int, int, int]] = set()
        for part in parts:
            if not isinstance(part, dict):
                raise ValueError(f"Parts must be objects for {identifier}")
            offset = part.get("offset")
            part_id = part.get("id", "")
            if (not isinstance(part_id, str) or not IDENTIFIER.fullmatch(part_id)
                    or part_id in all_part_ids):
                raise ValueError(f"Invalid or duplicate part id for {identifier}")
            if (not isinstance(offset, list) or len(offset) != 3
                    or any(type(value) is not int or value < 0 for value in offset)):
                raise ValueError(f"Expected nonnegative integer offsets for {identifier}")
            if tuple(offset) in occupied:
                raise ValueError(f"Overlapping parts for {identifier}")
            occupied.add(tuple(offset))
            all_part_ids.add(part_id)
        if parts[0]["id"] != identifier or parts[0]["offset"] != [0, 0, 0]:
            raise ValueError(f"First part must be the primary at [0,0,0]: {identifier}")
    # Hash order spreads categories and palettes without platform-dependent RNG.
    return sorted(entries, key=lambda entry: hashlib.sha256(entry["id"].encode()).hexdigest())


def fill_layers(width: int, bottom: int, top: int, block: str) -> list[str]:
    """Split fills into <=1024-block horizontal tiles: default fill limit is safe."""
    lines = []
    for y in range(bottom, top + 1):
        for x in range(0, width, 32):
            for z in range(0, width, 32):
                first = (x, y, z)
                last = (min(x + 31, width - 1), y, min(z + 31, width - 1))
                lines.append(f"fill {coordinates(first)} {coordinates(last)} {block}")
    return lines


def support_positions(entry: dict[str, Any]) -> set[tuple[int, int, int]]:
    offsets = [tuple(part["offset"]) for part in entry["parts"]]
    if entry["placement"] == "wall":
        # NORTH attaches to the southward block. Every wall cell gets support.
        support = {(x, y, z + 1) for x, y, z in offsets}
    elif entry["placement"] == "ceiling":
        top = max(y for _, y, _ in offsets) + 1
        support = {(x, top, z) for x, _, z in offsets}
    else:
        support = {(x, -1, z) for x, y, z in offsets if y == 0}
    if support.intersection(offsets):
        raise ValueError(f"Support overlaps furniture cells: {entry['id']}")
    return support


def render(entries: list[dict[str, Any]], catalog_bytes: bytes) -> dict[str, str]:
    max_offset = [max(part["offset"][axis] for e in entries for part in e["parts"])
                  for axis in range(3)]
    spacing = max(5, max_offset[0] + 3, max_offset[2] + 4)
    columns = math.ceil(math.sqrt(max(COUNTS)))
    margin = 2
    width = columns * spacing + margin * 2
    # An arbitrary origin may straddle chunks; reserve that extra chunk too.
    forced_chunk_upper_bound = math.ceil((width + 15) / 16) ** 2
    if forced_chunk_upper_bound > 256:
        raise ValueError("Furniture footprint exceeds the 256-chunk forceload limit")
    top = max_offset[1] + 2
    functions = "data/rhd_test/function/"
    files: dict[str, str] = {}

    def function(name: str, lines: list[str]) -> None:
        files[functions + name + ".mcfunction"] = "\n".join(lines) + "\n"

    # Verified from 1.21.11's official version.json and bundled vanilla packs.
    files["pack.mcmeta"] = encode({"pack": {
        "description": "Realistic Home Decor: explicit 0/100/500/1000 test scenes",
        "min_format": [94, 1], "max_format": [94, 1],
    }})
    function("prepare", [
        "# TEST WORLD ONLY. Adds forced chunks; does not place furniture.",
        f"forceload add ~ ~ {relative(width - 1)} {relative(width - 1)}",
        message("RHD: chunks requested. Wait at least 5 seconds, then invoke scene_N at the SAME origin.", "yellow"),
    ])
    function("release", [
        "# Removes forced status in this test region, including any pre-existing grants.",
        f"forceload remove ~ ~ {relative(width - 1)} {relative(width - 1)}",
        message("RHD: test-region forced chunks released. Blocks remain."),
    ])
    function("internal/clear", [
        f"# DESTRUCTIVE TEST REGION: relative [0,-1,0]..[{width - 1},{top},{width - 1}].",
        "# Every fill has <=1024 blocks; no gamerule changes needed.",
        *fill_layers(width, -1, top, "minecraft:air"),
        *fill_layers(width, -1, -1, "minecraft:smooth_stone"),
    ])
    # Probe every chunk, including both bounding edges at arbitrary origin.
    probes = list(range(0, width, 16))
    if probes[-1] != width - 1:
        probes.append(width - 1)
    loaded = " ".join(f"if loaded {coordinates((x, 0, z))}" for x in probes for z in probes)
    scenes: dict[str, Any] = {}
    for count in (0, *COUNTS):
        placements: list[dict[str, Any]] = []
        body = [f"# Exactly {count} primary furniture items; secondary cells are not items.",
                "function rhd_test:internal/clear"]
        verify = ["# Run >=1 second after scene_N, or after saving and reopening the world.",
                  "# MISSING is logged even without players; any such line means failure."]
        scene_columns = math.ceil(math.sqrt(count)) if count else 0
        scene_rows = math.ceil(count / scene_columns) if count else 0
        start_x = margin + (columns - scene_columns) * spacing // 2
        start_z = margin + (columns - scene_rows) * spacing // 2
        supports: set[tuple[int, int, int]] = set()
        furniture_cells: set[tuple[int, int, int]] = set()
        for index in range(count):
            entry = entries[index % len(entries)]
            position = (start_x + (index % scene_columns) * spacing, 0,
                        start_z + (index // scene_columns) * spacing)
            placement = {"id": entry["id"], "position": list(position),
                         "category": entry.get("category"), "placement": entry["placement"],
                         "parts": []}
            for support in sorted(support_positions(entry)):
                target = tuple(position[axis] + support[axis] for axis in range(3))
                if target in furniture_cells:
                    raise ValueError(f"Support collision in scene_{count}: {target}")
                if target not in supports and target[1] != -1:
                    body.append(f"setblock {coordinates(target)} minecraft:smooth_stone")
                supports.add(target)
            for part in entry["parts"]:
                target = tuple(position[axis] + part["offset"][axis] for axis in range(3))
                if target in furniture_cells or target in supports:
                    raise ValueError(f"Furniture collision in scene_{count}: {target}")
                furniture_cells.add(target)
                state = f"{NAMESPACE}:{part['id']}[facing=north]"
                body.append(f"setblock {coordinates(target)} {state}")
                verify.append(f"execute unless block {coordinates(target)} {state} run "
                              f"say RHD MISSING scene_{count} {part['id']} at {target}")
                placement["parts"].append({"id": part["id"], "position": list(target)})
            placements.append(placement)
        body.append(message(f"RHD: scene_{count} placed ({len(furniture_cells)} furniture cells). "
                            f"Wait 1 second, then run verify_{count} at the SAME origin.", "green"))
        body.append(f"say RHD SCENE_{count} PLACED primary_items={count} furniture_cells={len(furniture_cells)}")
        verify.append(f"say RHD VERIFY_{count} FINISHED expected_cells={len(furniture_cells)}. "
                      "Any MISSING line means failure. Player placement/drops/rendering are separate tests.")
        function(f"internal/scene_{count}", body)
        function(f"verify_{count}", verify)
        function(f"scene_{count}", [
            "# Explicitly destroys/replaces the bounded test region. TEST WORLD ONLY.",
            message(f"RHD: scene_{count} requested. If no green completion appears, "
                    "run prepare at this origin and wait for all chunks to load.", "yellow"),
            f"execute {loaded} run function rhd_test:internal/scene_{count}",
        ])
        scenes[str(count)] = {"primary_items": count, "furniture_cells": len(furniture_cells),
                              "support_cells": len(supports), "grid_columns": scene_columns,
                              "grid_rows": scene_rows, "placements": placements}
    manifest = {
        "generator": GENERATOR, "minecraft": "1.21.11", "data_pack_version": [94, 1],
        "catalog_sha256": hashlib.sha256(catalog_bytes).hexdigest(),
        "catalog_items": len(entries), "spacing": spacing,
        "bounds_relative": {"min": [0, -1, 0], "max": [width - 1, top, width - 1]},
        "suggested_origin": [0, 81, 0],
        "camera_relative": [width // 2, 8, width + 8, 180, 5],
        "forced_chunk_upper_bound": forced_chunk_upper_bound, "scenes": scenes,
        "owned_files": sorted([*files, "scene_manifest.json"]),
        "warning": "Destructive test-world commands only. No benchmark measurements are included.",
    }
    files["scene_manifest.json"] = encode(manifest)
    return files


def safe_path(output: Path, relative_path: str) -> Path:
    path = output / relative_path
    if not path.resolve().is_relative_to(output):
        raise ValueError(f"Generated path escapes output directory: {relative_path}")
    return path


def save(output: Path, files: dict[str, str], check: bool) -> None:
    previous_files: set[str] = set()
    marker = output / "scene_manifest.json"
    if output.exists() and any(output.iterdir()):
        if not marker.is_file():
            raise ValueError("Output is nonempty and has no scene-generator manifest; choose an empty directory")
        previous = json.loads(marker.read_text(encoding="utf-8"))
        if previous.get("generator") != GENERATOR:
            raise ValueError("Output belongs to another tool; refusing to overwrite it")
        previous_files = set(previous.get("owned_files", []))
    if check:
        different = [name for name, contents in files.items()
                     if not safe_path(output, name).is_file()
                     or safe_path(output, name).read_text(encoding="utf-8") != contents]
        if different or previous_files - files.keys():
            raise ValueError("Generated scene files differ: " + ", ".join(different[:8]))
        return
    for name in previous_files - files.keys():
        path = safe_path(output, name)
        if path.is_file():
            path.unlink()
    for name, contents in sorted(files.items()):
        path = safe_path(output, name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=CATALOG,
                        help="Generated catalog.json (default: checkout catalog)")
    parser.add_argument("--output", type=Path, default=ROOT / "build/test-datapack",
                        help="Empty or previously generated directory (default: build/test-datapack)")
    parser.add_argument("--check", action="store_true", help="Verify output matches catalog without writing")
    args = parser.parse_args(argv)
    try:
        output = args.output.resolve()
        if output == ROOT or ROOT.is_relative_to(output) or output.is_relative_to(ROOT / "src"):
            raise ValueError("Output must be a generated directory outside project sources")
        entries = load_catalog(args.catalog)
        files = render(entries, args.catalog.read_bytes())
        save(output, files, args.check)
    except (OSError, ValueError, TypeError, KeyError) as error:
        parser.exit(1, f"scene_generator: {error}\n")
    verb = "Verified" if args.check else "Generated"
    print(f"{verb} 0/100/500/1000-item scenes ({len(entries)} catalog items): {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
