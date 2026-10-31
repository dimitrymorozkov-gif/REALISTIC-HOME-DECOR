# Furniture resource compiler

Python 3.10+; no third-party packages. Run from any directory:

```sh
python3 tools/furniture_generator/generate.py
python3 tools/furniture_generator/generate.py --check
python3 tools/validate_resources.py
```

`generate.py` creates the catalog, blockstates, vanilla models, current Minecraft
item definitions, loot tables, English/Russian names, 64×64 PNG material library
and catalog documentation. All artwork and geometry in this project is original.
Its JSON is deterministic, sorted and compact. It uses a common geometric parent
for all eight coordinated material palettes instead of copying the same geometry.

The development checkpoints `--stage first-five` and `--stage first-twenty` select
the initial five and twenty *constructions*. Each construction has eight palettes.
The default `--stage full` contains 120 constructions and 960 inventory items:
80 existing furniture/architecture designs plus 40 new structural wall designs.
Use the same stage with `--check` when checking a checkpoint.

Generated files are listed with SHA256 hashes in `generated_manifest.json`.
A changed generated file is protected from accidental overwrite; edit templates
instead or use `--force` deliberately. Stale generated files are removed only
when their recorded hashes still match. `--check` compares without writing.

## Add or change a construction

Edit `templates.py` (interior furniture), `extras.py` (architecture/outdoor), or
`walls.py` and its `wall_patterns.py` helpers (structural wall relief).
Each exposes `designs()`, returning dictionaries with:

```python
{
    'id': 'my_desk', 'en': 'Writing desk', 'ru': 'Письменный стол',
    'category': 'office', 'placement': 'floor', 'luminance': 0,
    'connect': False, 'params': {'width': 24, 'height': 12},
    'boxes': table(w=24, d=16, h=12, thickness=1.5,
                   style='trestle', top='wood'),
}
```

The helpers create actual geometry from parameters. Table parameters control
width/depth/height, top thickness, four legs/pedestal/trestle and top material.
Chair parameters control seat and back heights, upholstery/slats and armrests.
Cabinet parameters control dimensions, section count, glass fronts and worktop.
Sofa parameters control width, number of cushions and removable module end arms.
Other constructions can combine these helpers or supply explicit cuboids.

A cuboid is `(x1,y1,z1,x2,y2,z2,material_role[,end_tag])`; units are 1/16 metre.
All dimensions must be positive. Coordinates are nonnegative, +Y is up, +X east,
+Z south. The NORTH view looks toward the front at Z=0. Wall backs meet Z=16;
ceiling pieces meet Y=16. A supported primary cell at `[0,0,0]` must contain
geometry. The compiler clips large constructions at 16-unit cell boundaries,
keeping every block model and collision box inside its own cell. It normalizes
the complete object for the inventory preview.

Material roles: `wood`, `fabric`, `stone`, `metal`, `accent`, `ceramic`, `glass`,
`screen`, `leaf`, `light`, `book`, `concrete`, `mortar`, `plaster`, and `trim`.
Shared patterns and RGB values live in `MATERIALS`; eight curated combinations
live in `PALETTES` in `generate.py`: `oak`, `walnut`, `ebony`, `ivory`, `sage`,
`terracotta`, `sand`, and `slate`. `palette_textures()` rejects missing materials
and the compiler rejects unmapped roles before writing any resource files.
Choose a role that matches the real surface: plaster uses a matte mineral
material, not a wood-grain texture with a different label. Optional `particle`
selects the material role for breaking particles; new walls use their front
surface instead of the default furniture wood. Optional `wall_family` is catalog
metadata for the generated wall guide and does not add a runtime mechanic.

Original palette IDs, original item IDs and original names are retained. The
original five furniture-role mappings (`wood`, `fabric`, `stone`, `metal`,
`accent`) and every original PNG are retained too. Ceramic and concrete now
have palette-specific glazed/mineral materials, so previously identical vases,
tile panels and concrete variants actually differ. `oak` preserves the original
ceramic/concrete materials; the other original IDs intentionally gain coordinated
cream, graphite and ivory surfaces. See `docs/PALETTES.md` for the exact matrix.

The forty `wall_` constructions are different geometric patterns rather than
forty recolorings of the same flat model. They use one-cell solids with mineral
cores and front relief, `building_materials` category and `placement: any` so a
wall can be stacked without a backing support. Their original eight material
variants reuse each pattern's geometric parent. See `docs/WALLS.md` for IDs and
families. Wall designs are appended after the original eighty constructions,
preserving the first-five and first-twenty checkpoint design sets.

Only these structural walls use a normal full-cell 1×1×1 m collision and selection
shape; their shallow front relief remains in the JSON model. This gives vanilla
smooth and flat lighting the ordinary outside-face samples for solid blocks,
while blocking skylight and block light. There is no custom renderer, dynamic
shape classification, light emission or permanently bright surface. Existing
furniture keeps its detailed per-part collision shapes.

Glass uses true alpha and a `translucent` catalog render layer. Furniture has no
custom renderer, animation, block entity or continuously running ticks. Neighbor
and chunk-load events schedule a one-shot integrity check when necessary.

Only single-cell constructions may use `connect: True`. Their end cuboids can
carry the tag `left` or `right`. The compiler removes those cuboids and computes
matching `connection_boxes` when a compatible neighbor is present, generating
all sixteen `facing,left,right` variants. Neighbor compatibility is the same
catalog ID and facing. Ordinary constructions have only four facing variants.

Collision deliberately ignores tiny handles and uses at most twelve significant
cuboids per cell. Open chair/table legs remain separate. When adding detailed
geometry, verify collision in game as well as running the resource validator.

All items are available in the eleven creative tabs. There are no survival
recipes in the current decorative catalog. Add recipes as a separate deliberate
design step rather than assuming these objects have appliance functionality.
