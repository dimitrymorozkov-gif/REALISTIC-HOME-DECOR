#!/usr/bin/env python3
"""Validate generated Minecraft 1.21.11 assets without downloading Minecraft.

Checks the catalog/asset contract, model references and geometry, translation
coverage, loot, and the integrity of original PNG textures. This deliberately
fails on malformed or missing resources; it does not replace an in-game test.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import math
from pathlib import Path
import re
import struct
import sys
import zlib

NAMESPACE = "realistic_home_decor"
CATEGORIES = {
    "living_room", "kitchen", "bathroom", "bedroom", "office", "lighting",
    "architecture", "building_materials", "decorations", "outdoor", "garage",
}
FACINGS = {"north": 0, "east": 90, "south": 180, "west": 270}
IDENTIFIER = re.compile(r"^[a-z0-9_.-]+$")
RESOURCE = re.compile(r"^(?:[a-z0-9_.-]+:)?[a-z0-9_./-]+$")
FACES = {"north", "east", "south", "west", "up", "down"}


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    counts: dict[str, int] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, path: object, message: str) -> None:
        self.errors.append(f"{path}: {message}")


def _object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number {value}")


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_object,
                      parse_constant=_reject_constant)


def _number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _vec(value: object, size: int) -> bool:
    return isinstance(value, list) and len(value) == size and all(_number(v) for v in value)


def _resource(value: object) -> bool:
    return (isinstance(value, str) and RESOURCE.fullmatch(value) is not None
            and all(segment not in ("", ".", "..")
                    for segment in value.split(":", 1)[-1].split("/")))


def _location(value: str) -> tuple[str, str]:
    return tuple(value.split(":", 1)) if ":" in value else ("minecraft", value)


def validate_png(path: Path) -> tuple[int, int]:
    """Read PNG chunks, verify CRCs and decompressed rows (8-bit RGB/RGBA)."""
    raw = path.read_bytes()
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("invalid PNG signature")
    offset, chunks, payload = 8, [], bytearray()
    width = height = channels = 0
    ended = False
    while offset < len(raw):
        if offset + 12 > len(raw):
            raise ValueError("truncated PNG chunk")
        length = struct.unpack_from(">I", raw, offset)[0]
        tag = raw[offset + 4:offset + 8]
        end = offset + 12 + length
        if end > len(raw):
            raise ValueError("truncated PNG chunk data")
        data = raw[offset + 8:offset + 8 + length]
        crc = struct.unpack_from(">I", raw, offset + 8 + length)[0]
        if zlib.crc32(tag + data) & 0xFFFFFFFF != crc:
            raise ValueError(f"PNG {tag.decode('ascii', 'replace')} CRC mismatch")
        if not chunks and tag != b"IHDR":
            raise ValueError("PNG must start with IHDR")
        if tag == b"IHDR":
            if chunks or length != 13:
                raise ValueError("invalid or repeated PNG IHDR")
            width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", data)
            if width not in (32, 64, 128) or height not in (32, 64, 128):
                raise ValueError(f"unexpected texture dimensions {width}x{height}; expected 32/64/128")
            if depth != 8 or color not in (2, 6) or compression or filtering or interlace:
                raise ValueError("expected a non-interlaced 8-bit RGB/RGBA PNG")
            channels = 3 if color == 2 else 4
        elif tag == b"IDAT":
            payload.extend(data)
        elif tag == b"IEND":
            if length:
                raise ValueError("IEND must be empty")
            if end != len(raw):
                raise ValueError("unexpected trailing data after PNG IEND")
            ended = True
        elif tag[0] & 32 == 0 and tag not in (b"PLTE",):
            raise ValueError(f"unsupported critical PNG chunk {tag!r}")
        chunks.append(tag)
        offset = end
        if ended:
            break
    if not ended or not payload:
        raise ValueError("PNG lacks IEND or image data")
    decoder = zlib.decompressobj()
    rows = decoder.decompress(payload)
    rows += decoder.flush()
    if not decoder.eof or decoder.unused_data:
        raise ValueError("invalid PNG zlib stream")
    stride = width * channels + 1
    if len(rows) != height * stride:
        raise ValueError("PNG pixel data length does not match dimensions")
    if any(rows[y * stride] > 4 for y in range(height)):
        raise ValueError("invalid PNG row filter")
    return width, height


class Validator:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.resources = self.root / "src/main/resources"
        self.assets = self.resources / "assets" / NAMESPACE
        self.data = self.resources / "data" / NAMESPACE
        self.report = Report()
        self.documents: dict[Path, object] = {}
        self.model_cache: dict[str, tuple[dict, dict]] = {}
        self.parent_references: set[str] = set()

    def relative(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)

    def error(self, path: Path | str, message: str) -> None:
        self.report.error(self.relative(path) if isinstance(path, Path) else path, message)

    def load(self, path: Path) -> object:
        if path in self.documents:
            return self.documents[path]
        try:
            document = read_json(path)
        except (OSError, ValueError, UnicodeError) as exc:
            self.error(path, str(exc))
            document = None
        self.documents[path] = document
        return document

    def required_object(self, path: Path) -> dict:
        document = self.load(path)
        if document is not None and not isinstance(document, dict):
            self.error(path, "expected a JSON object")
        return document if isinstance(document, dict) else {}

    def model(self, reference: str, stack: tuple[str, ...] = ()) -> tuple[dict, dict]:
        if not _resource(reference):
            self.error("model", f"invalid resource location {reference!r}")
            return {}, {}
        namespace, name = _location(reference)
        if namespace == "minecraft":
            return {}, {}
        if namespace != NAMESPACE:
            self.error("model", f"undeclared dependency namespace {namespace!r}")
            return {}, {}
        if reference in stack:
            self.error(reference, f"cyclic model parent chain: {' -> '.join(stack)}")
            return {}, {}
        if reference in self.model_cache:
            return self.model_cache[reference]
        path = self.assets / "models" / f"{name}.json"
        document = self.required_object(path)
        parent, textures = {}, {}
        if "parent" in document:
            if not isinstance(document["parent"], str):
                self.error(path, "parent must be a resource location")
            else:
                parent, inherited = self.model(document["parent"], (*stack, reference))
                textures.update(inherited)
        if not isinstance(document.get("textures", {}), dict):
            self.error(path, "textures must be an object")
        else:
            textures.update(document.get("textures", {}))
        merged = dict(parent)
        merged.update(document)
        merged["textures"] = textures
        self.model_cache[reference] = merged, textures
        return merged, textures

    def texture(self, reference: object, textures: dict, source: Path) -> None:
        seen = set()
        while isinstance(reference, str) and reference.startswith("#"):
            key = reference[1:]
            if key in seen:
                self.error(source, f"cyclic texture alias {reference}")
                return
            seen.add(key)
            if key not in textures:
                self.error(source, f"unresolved texture alias {reference}")
                return
            reference = textures[key]
        if not _resource(reference):
            self.error(source, f"invalid texture reference {reference!r}")
            return
        namespace, name = _location(reference)
        if namespace == "minecraft":
            return
        if namespace != NAMESPACE:
            self.error(source, f"undeclared texture namespace {namespace!r}")
        elif not (self.assets / "textures" / f"{name}.png").is_file():
            self.error(source, f"missing texture {reference}")

    def validate_model(self, path: Path) -> None:
        name = path.relative_to(self.assets / "models").with_suffix("").as_posix()
        raw = self.required_object(path)
        abstract = not raw.get("textures") and f"{NAMESPACE}:{name}" in self.parent_references
        document, textures = self.model(f"{NAMESPACE}:{name}")
        for value in textures.values():
            self.texture(value, textures, path)
        elements = document.get("elements", [])
        if not isinstance(elements, list):
            self.error(path, "elements must be an array")
            return
        for index, element in enumerate(elements):
            label = f"element {index}"
            if not isinstance(element, dict):
                self.error(path, f"{label} must be an object")
                continue
            low, high = element.get("from"), element.get("to")
            if not _vec(low, 3) or not _vec(high, 3):
                self.error(path, f"{label} requires numeric from/to vectors")
                continue
            bound_low, bound_high = (0, 16) if name.startswith("block/") else (-16, 32)
            if any(not bound_low <= n <= bound_high for n in low + high):
                self.error(path, f"{label} exceeds coordinate bounds {bound_low}..{bound_high}")
            if any(a >= b for a, b in zip(low, high)):
                self.error(path, f"{label} has empty or inverted geometry")
            rotation = element.get("rotation")
            if rotation is not None:
                if (not isinstance(rotation, dict) or rotation.get("axis") not in ("x", "y", "z")
                        or rotation.get("angle") not in (-45, -22.5, 0, 22.5, 45)
                        or not _vec(rotation.get("origin"), 3)):
                    self.error(path, f"{label} has invalid standard JSON model rotation")
            faces = element.get("faces")
            if not isinstance(faces, dict) or not faces:
                self.error(path, f"{label} requires visible faces")
                continue
            for face, settings in faces.items():
                if face not in FACES or not isinstance(settings, dict):
                    self.error(path, f"{label} has invalid face {face!r}")
                    continue
                if not abstract:
                    self.texture(settings.get("texture"), textures, path)
                uv = settings.get("uv")
                if uv is not None and (not _vec(uv, 4) or any(not 0 <= n <= 16 for n in uv)):
                    self.error(path, f"{label} {face} has UV outside 0..16")
                if "cullface" in settings and settings["cullface"] not in FACES:
                    self.error(path, f"{label} has invalid cullface")
                if settings.get("rotation", 0) not in (0, 90, 180, 270):
                    self.error(path, f"{label} face rotation must be a multiple of 90")

    def blockstate(self, part_id: str, connect: bool) -> None:
        path = self.assets / "blockstates" / f"{part_id}.json"
        document = self.required_object(path)
        variants = document.get("variants")
        if not isinstance(variants, dict):
            self.error(path, "requires variants with exactly the runtime block properties")
            return
        expected = {f"facing={f}" for f in FACINGS}
        if connect:
            expected = {
                f"facing={f},left={left},right={right}"
                for f in FACINGS for left in ("false", "true") for right in ("false", "true")
            }
        canonical = lambda key: ",".join(sorted(key.split(",")))
        if {canonical(key) for key in variants} != {canonical(key) for key in expected}:
            self.error(path, "blockstate variants do not match catalog facing/connection properties")
        for key, variant in variants.items():
            entries = variant if isinstance(variant, list) else [variant]
            if not entries:
                self.error(path, f"empty model list for {key}")
            for item in entries:
                if not isinstance(item, dict) or not isinstance(item.get("model"), str):
                    self.error(path, f"variant {key} requires a model reference")
                    continue
                self.model(item["model"])
                facing = next((s.split("=", 1)[1] for s in key.split(",") if s.startswith("facing=")), None)
                if facing in FACINGS and item.get("y", 0) != FACINGS[facing]:
                    self.error(path, f"variant {key} has an incorrect facing rotation")
                if item.get("x", 0) not in (0, 90, 180, 270):
                    self.error(path, f"variant {key} has an invalid x rotation")

    def loot(self, part_id: str, primary: str, is_primary: bool) -> None:
        path = self.data / "loot_table/blocks" / f"{part_id}.json"
        document = self.required_object(path)
        if document.get("type") != "minecraft:block":
            self.error(path, "loot type must be minecraft:block")
        pools = document.get("pools", [])
        if not isinstance(pools, list):
            self.error(path, "loot pools must be an array")
            return
        drops = []
        def walk(value: object) -> None:
            if isinstance(value, dict):
                if value.get("type") == "minecraft:item":
                    drops.append(value.get("name"))
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)
        walk(pools)
        if is_primary and (drops != [f"{NAMESPACE}:{primary}"] or len(pools) != 1
                           or not isinstance(pools[0], dict) or pools[0].get("rolls") != 1):
            self.error(path, "primary loot must drop exactly its own furniture item once")
        if not is_primary and pools:
            self.error(path, "secondary furniture cells must not produce duplicate loot")

    def run(self) -> Report:
        if not self.resources.is_dir():
            self.error(self.resources, "resources directory is missing")
            return self.report
        json_files = sorted(self.resources.rglob("*.json"))
        for path in json_files:
            self.load(path)
        self.parent_references = {
            document["parent"] for path, document in self.documents.items()
            if path.is_relative_to(self.assets / "models") and isinstance(document, dict)
            and isinstance(document.get("parent"), str)
        }
        self.report.counts["json_files"] = len(json_files)
        png_files = sorted(self.assets.rglob("*.png"))
        for path in png_files:
            try:
                validate_png(path)
            except (OSError, ValueError, struct.error, zlib.error) as exc:
                self.error(path, str(exc))
        self.report.counts["textures"] = len(png_files)
        catalog_path = self.data / "catalog.json"
        catalog = self.required_object(catalog_path)
        if catalog.get("schema_version") != 1:
            self.error(catalog_path, "unsupported or absent schema_version")
        entries = catalog.get("entries")
        if not isinstance(entries, list) or not entries:
            self.error(catalog_path, "entries must be a nonempty array")
            return self.report
        languages = {lang: self.required_object(self.assets / "lang" / f"{lang}.json")
                     for lang in ("en_us", "ru_ru")}
        for lang, translations in languages.items():
            for category in CATEGORIES:
                key = f"itemGroup.{NAMESPACE}.{category}"
                if not isinstance(translations.get(key), str) or not translations[key].strip():
                    self.error(self.assets / "lang" / f"{lang}.json", f"missing creative tab translation {key}")
        all_parts, item_ids, categories = set(), set(), set()
        for i, entry in enumerate(entries):
            if not isinstance(entry, dict):
                self.error(catalog_path, f"entry {i} must be an object")
                continue
            primary = entry.get("id")
            if not isinstance(primary, str) or not IDENTIFIER.fullmatch(primary):
                self.error(catalog_path, f"entry {i} has invalid identifier {primary!r}")
                continue
            if primary in item_ids:
                self.error(catalog_path, f"duplicate item registration {primary}")
            item_ids.add(primary)
            category = entry.get("category")
            if category not in CATEGORIES:
                self.error(catalog_path, f"{primary}: unknown category {category!r}")
            else:
                categories.add(category)
            if not isinstance(entry.get("template"), str) or not entry["template"]:
                self.error(catalog_path, f"{primary}: template is required")
            if entry.get("placement") not in ("floor", "wall", "ceiling", "any"):
                self.error(catalog_path, f"{primary}: unsupported placement")
            luminance = entry.get("luminance")
            if type(luminance) is not int or not 0 <= luminance <= 15:
                self.error(catalog_path, f"{primary}: luminance must be an integer 0..15")
            if type(entry.get("connect")) is not bool:
                self.error(catalog_path, f"{primary}: connect must be boolean")
            names = entry.get("names", {})
            if not isinstance(names, dict):
                names = {}
            for lang, translations in languages.items():
                key = f"block.{NAMESPACE}.{primary}"
                if not isinstance(names.get(lang), str) or not names[lang].strip():
                    self.error(catalog_path, f"{primary}: missing {lang} catalog name")
                if not isinstance(translations.get(key), str) or not translations[key].strip():
                    self.error(self.assets / "lang" / f"{lang}.json", f"missing translation {key}")
                elif translations[key] != names.get(lang):
                    self.error(catalog_path, f"{primary}: {lang} name differs from localization")
            item_path = self.assets / "items" / f"{primary}.json"
            item = self.required_object(item_path)
            model = item.get("model")
            if (not isinstance(model, dict) or model.get("type") != "minecraft:model"
                    or not isinstance(model.get("model"), str)):
                self.error(item_path, "requires Minecraft 1.21.11 minecraft:model item definition")
            else:
                self.model(model["model"])
            parts = entry.get("parts")
            if not isinstance(parts, list) or not parts:
                self.error(catalog_path, f"{primary}: requires at least one part")
                continue
            offsets = set()
            for p, part in enumerate(parts):
                if not isinstance(part, dict):
                    self.error(catalog_path, f"{primary}: part {p} must be an object")
                    continue
                part_id, offset = part.get("id"), part.get("offset")
                if not isinstance(part_id, str) or not IDENTIFIER.fullmatch(part_id):
                    self.error(catalog_path, f"{primary}: invalid part identifier {part_id!r}")
                    continue
                if part_id in all_parts:
                    self.error(catalog_path, f"duplicate block registration {part_id}")
                all_parts.add(part_id)
                if not (isinstance(offset, list) and len(offset) == 3
                        and all(type(n) is int and 0 <= n <= 15 for n in offset)):
                    self.error(catalog_path, f"{part_id}: offset requires three nonnegative integer cells")
                else:
                    if tuple(offset) in offsets:
                        self.error(catalog_path, f"{primary}: duplicate cell offset {offset}")
                    offsets.add(tuple(offset))
                if p == 0 and (part_id != primary or offset != [0, 0, 0]):
                    self.error(catalog_path, f"{primary}: primary part must match item id at [0,0,0]")
                if p > 0 and (self.assets / "items" / f"{part_id}.json").exists():
                    self.error(catalog_path, f"{part_id}: secondary cells cannot have items")
                boxes = part.get("boxes")
                if not isinstance(boxes, list):
                    self.error(catalog_path, f"{part_id}: collision boxes must be an array")
                else:
                    for box in boxes:
                        if (not _vec(box, 6) or any(not 0 <= n <= 16 for n in box)
                                or any(a >= b for a, b in zip(box[:3], box[3:]))):
                            self.error(catalog_path, f"{part_id}: invalid collision box {box!r}")
                if entry.get("connect"):
                    connected = part.get("connection_boxes")
                    keys = {"false_false", "false_true", "true_false", "true_true"}
                    if not isinstance(connected, dict) or set(connected) != keys:
                        self.error(catalog_path, f"{part_id}: connection_boxes requires all four left/right states")
                    else:
                        for state, state_boxes in connected.items():
                            if not isinstance(state_boxes, list):
                                self.error(catalog_path, f"{part_id}: {state} connection boxes must be an array")
                                continue
                            for box in state_boxes:
                                if (not _vec(box, 6) or any(not 0 <= n <= 16 for n in box)
                                        or any(a >= b for a, b in zip(box[:3], box[3:]))):
                                    self.error(catalog_path, f"{part_id}: invalid {state} connection collision box")
                        if connected.get("false_false") != boxes:
                            self.error(catalog_path, f"{part_id}: unconnected collision must equal base boxes")
                self.blockstate(part_id, bool(entry.get("connect")))
                self.loot(part_id, primary, p == 0)
        self.report.counts.update(items=len(item_ids), blocks=len(all_parts), categories=len(categories))
        for directory, expected in (("blockstates", all_parts), ("items", item_ids)):
            actual = {p.stem for p in (self.assets / directory).glob("*.json")}
            for orphan in sorted(actual - expected):
                self.error(self.assets / directory / f"{orphan}.json", "orphan resource absent from catalog")
        models = sorted((self.assets / "models").rglob("*.json"))
        for path in models:
            self.validate_model(path)
        self.report.counts["models"] = len(models)
        return self.report


def validate(root: Path | str) -> Report:
    return Validator(Path(root)).run()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    report = validate(args.root)
    if report.errors:
        for error in report.errors:
            print(error, file=sys.stderr)
        print(f"Resource validation FAILED ({len(report.errors)} errors)", file=sys.stderr)
        return 1
    summary = ", ".join(f"{value} {key}" for key, value in report.counts.items())
    print(f"Resource validation passed: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
