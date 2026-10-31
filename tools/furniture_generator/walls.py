"""Forty independent structural wall designs, built from original cuboid reliefs.

Every design occupies one 16x16x16 model cell. The continuous structural core is
14.5 pixels deep; the exposed north face has actual recessed mortar, joints and
relief, rather than a differently named full cube. Neighbouring copies tile on
an exact 16-pixel period. Coordinates use +Y up and north at Z=0.

A face patch is (left, bottom, right, top, front_depth, material_role). Patches
are disjoint in the XY plane and end at the structural core (Z=1.5), so there
are no overlapping slabs or coincident outward faces. The parametric helpers
below deliberately control the brick bond, joint width and individual depth.
Wood, concrete, plaster and acoustic patterns are defined in wall_patterns.py.
"""
from __future__ import annotations

from collections.abc import Iterable
import math


CORE_DEPTH = 1.5
JOINT = 0.20


def _face(x1: float, y1: float, x2: float, y2: float,
          front: float = 0.15, role: str = 'stone') -> tuple:
    """One exposed relief patch, backed by the structural core."""
    return (x1, y1, front, x2, y2, CORE_DEPTH, role)


def _inset_rect(x1: float, y1: float, x2: float, y2: float,
                front: float = 0.15, role: str = 'stone',
                joint: float = JOINT) -> tuple:
    """Inset genuine tile edges, retaining unbroken cuts at periodic borders."""
    half = joint / 2
    return _face(max(0, x1 + half), max(0, y1 + half),
                 min(16, x2 - half), min(16, y2 - half), front, role)


def _courses(heights: Iterable[float], widths: Iterable[float],
             phases: Iterable[float] = (0,), depths: Iterable[float] = (.15,),
             role: str = 'stone', joint: float = JOINT) -> list[tuple]:
    """Lay horizontal masonry courses with a repeating bond and depth profile."""
    widths = tuple(widths)
    phases = tuple(phases)
    depths = tuple(depths)
    period = sum(widths)
    boxes = []
    y = 0.0
    for row, height in enumerate(heights):
        phase = phases[row % len(phases)] % period
        x = -phase
        while x > 0:
            x -= period
        index = 0
        while x < 16:
            width = widths[index % len(widths)]
            if x + width > 0:
                rect = _inset_rect(x, y, x + width, y + height,
                                   depths[(row + index) % len(depths)], role, joint)
                if rect[3] > rect[0] and rect[4] > rect[1]:
                    boxes.append(rect)
            x += width
            index += 1
        y += height
    assert math.isclose(y, 16), f'Courses must fill the 16-pixel repeat: {y}'
    return boxes


def _framed_tile(x1: float, y1: float, x2: float, y2: float,
                 rim: float, frame_front: float, centre_front: float,
                 role: str, frame_role: str | None = None) -> list[tuple]:
    """Five disjoint patches form a raised boss or a recessed cassette."""
    frame_role = frame_role or role
    return [
        _face(x1, y1, x1 + rim, y2, frame_front, frame_role),
        _face(x2 - rim, y1, x2, y2, frame_front, frame_role),
        _face(x1 + rim, y1, x2 - rim, y1 + rim, frame_front, frame_role),
        _face(x1 + rim, y2 - rim, x2 - rim, y2, frame_front, frame_role),
        _face(x1 + rim, y1 + rim, x2 - rim, y2 - rim, centre_front, role),
    ]


def _herringbone() -> list[tuple]:
    """A true repeating 90-degree herringbone tiling of 2:1 brick rectangles.

    On a unit grid, sums 0/1 mod4 belong to horizontal dominoes, sums2/3 to
    vertical dominoes. This covers the plane once and has period four units
    along both axes. Clipping retains the natural brick across repeat borders.
    """
    boxes = []
    for y in range(-1, 4):
        for x in range(-1, 4):
            bond = (x + y) % 4
            if bond not in (0, 2):
                continue
            width, height = (8, 4) if bond == 0 else (4, 8)
            tile = _inset_rect(x * 4, y * 4, x * 4 + width, y * 4 + height,
                               .12 if bond == 0 else .42, 'stone')
            if tile[3] > tile[0] and tile[4] > tile[1]:
                boxes.append(tile)
    return boxes


def _own_designs() -> list[dict]:
    result = []

    def add(identifier, english, russian, family, patches, particle='stone', **params):
        result.append({
            'id': identifier, 'en': english, 'ru': russian,
            'category': 'building_materials', 'placement': 'any',
            'luminance': 0, 'connect': False, 'particle': particle,
            'wall_family': family,
            'params': {'family': family, 'core_depth': CORE_DEPTH, **params},
            'boxes': [(0, 0, CORE_DEPTH, 16, 16, 16, 'mortar'), *patches],
        })

    add('wall_running_brick', 'Running-bond brick wall', 'Стена с ложковой кладкой',
        'masonry', _courses([4]*4, [8], [0, 4]), bond='half-offset', joint=JOINT)
    add('wall_stack_brick', 'Stack-bond brick wall', 'Стена с прямой кирпичной кладкой',
        'masonry', _courses([4]*4, [4], depths=[.25]), bond='stack', joint=JOINT)
    add('wall_flemish_bond', 'Flemish-bond brick wall', 'Стена с фламандской кладкой',
        'masonry', _courses([4]*4, [16/3, 8/3], [0, 4], [.12, .33]),
        bond='alternating-headers-stretchers', joint=JOINT)
    add('wall_english_bond', 'English-bond brick wall', 'Стена с английской кладкой',
        'masonry',
        _courses([4]*4, [8], [0, 0])[:2]
        + [_inset_rect(x, 4, x+4, 8, .38) for x in range(0, 16, 4)]
        + [_inset_rect(x, 8, x+8, 12, .15) for x in (0, 8)]
        + [_inset_rect(x, 12, x+4, 16, .38) for x in range(0, 16, 4)],
        bond='alternating-header-courses', joint=JOINT)
    add('wall_soldier_brick', 'Soldier-course brick wall', 'Стена с вертикальной кладкой',
        'masonry', _courses([8, 8], [4], [0, 2], [.08, .30]),
        bond='upright-bricks', joint=JOINT)

    basket = []
    for qy in (0, 8):
        for qx in (0, 8):
            if (qx + qy) % 16 == 0:
                basket += [_inset_rect(qx, qy+dy, qx+8, qy+dy+4, .12)
                           for dy in (0, 4)]
            else:
                basket += [_inset_rect(qx+dx, qy, qx+dx+4, qy+8, .48)
                           for dx in (0, 4)]
    add('wall_basket_brick', 'Basket-weave brick wall', 'Стена с плетёной кирпичной кладкой',
        'masonry', basket, bond='paired-quarter-turn')
    add('wall_herringbone_brick', 'Herringbone brick wall', 'Кирпичная стена ёлочкой',
        'masonry', _herringbone(), bond='90-degree-herringbone')

    rusticated = []
    for x in (0, 8):
        for y in (0, 8):
            rusticated += _framed_tile(x+.12, y+.12, x+7.88, y+7.88,
                                      .75, .75, 0, 'stone')
    add('wall_rusticated_brick', 'Rusticated masonry wall', 'Стена с рельефным рустом',
        'masonry', rusticated, relief='stepped-raised-boss', joint=.24)
    add('wall_roman_brick', 'Roman brick wall', 'Стена из длинного римского кирпича',
        'masonry', _courses([2]*8, [8], [0, 4], [.10], joint=.16),
        bond='thin-long-stretchers', joint=.16)

    breeze = []
    for x in (0, 8):
        for y in (0, 8):
            # The centre remains a real recess down to the continuous mortar
            # core. These are architectural relief blocks, not through-holes.
            frame = _framed_tile(x+.18, y+.18, x+7.82, y+7.82,
                                 1.35, .10, .90, 'stone')
            breeze += frame[:4]
    add('wall_breeze_brick', 'Recessed breeze-block wall', 'Стена с нишами бриз-блоков',
        'masonry', breeze, relief='four-square-open-recesses', joint=.36)

    ashlar = []
    for row, (bottom, top, cuts) in enumerate([
            (0, 5, [0, 6, 16]), (5, 11, [0, 10, 16]), (11, 16, [0, 4, 12, 16])]):
        for n, (left, right) in enumerate(zip(cuts, cuts[1:])):
            ashlar.append(_inset_rect(left, bottom, right, top,
                                      (.12, .46, .25)[(row+n)%3]))
    add('wall_ashlar_stone', 'Coursed ashlar stone wall', 'Стена из тесаного камня',
        'stone', ashlar, bond='three-height-ashlar', joint=JOINT)

    dry_stone = []
    y = 0
    rows = [(3, [0, 5, 10, 16]), (4, [0, 3, 11, 16]),
            (2.5, [0, 7, 12, 16]), (3.5, [0, 4, 9, 16]), (3, [0, 6, 16])]
    for row, (height, cuts) in enumerate(rows):
        for n, (left, right) in enumerate(zip(cuts, cuts[1:])):
            dry_stone.append(_inset_rect(left, y, right, y+height,
                                         (.08, .65, .35, .95)[(2*row+n)%4],
                                         joint=.27))
        y += height
    add('wall_dry_stone', 'Dry-stacked stone wall', 'Стена сухой каменной кладки',
        'stone', dry_stone, bond='irregular-five-course', joint=.27)

    # Independently sized stones form an orthogonal polygonal mosaic rather
    # than the repeated rows used by the coursed masonry templates above.
    cyclopean = [
        (0, 0, 6, 5, .10), (6, 0, 11, 3, .42), (11, 0, 16, 7, .28),
        (6, 3, 11, 9, .72), (0, 5, 3, 11, .50), (3, 5, 6, 9, .22),
        (11, 7, 16, 12, .08), (3, 9, 11, 13, .38),
        (0, 11, 3, 16, .18), (11, 12, 16, 16, .62), (3, 13, 11, 16, .05),
    ]
    add('wall_cyclopean_stone', 'Irregular mosaic stone wall', 'Стена из разновеликого камня',
        'stone', [_inset_rect(*r) for r in cyclopean],
        bond='orthogonal-irregular-mosaic', joint=JOINT)

    ledger = []
    for row in range(8):
        cuts = ([0, 3, 9, 16], [0, 7, 12, 16], [0, 5, 16])[row%3]
        for n, (left, right) in enumerate(zip(cuts, cuts[1:])):
            ledger.append(_inset_rect(left, row*2, right, row*2+2,
                                      (0, .55, .95, .30)[(row+n)%4], joint=.12))
    add('wall_slate_ledger', 'Split-face stone ledger wall', 'Стена из колотых каменных ламелей',
        'stone', ledger, bond='thin-varied-depth-ledger', joint=.12)

    bands = [_face(0, 0, 16, 4.95, .35),
             _face(0, 4.95, 16, 5.25, .10, 'trim'),
             _face(0, 5.25, 16, 10.75, .65),
             _face(0, 10.75, 16, 11.05, .10, 'trim'),
             _face(0, 11.05, 16, 16, .35)]
    add('wall_travertine_bands', 'Banded stone wall with inlays', 'Каменная стена с горизонтальными вставками',
        'stone', bands, relief='three-stone-bands-two-inlays')

    quoins = []
    for row in range(4):
        edge = 5 if row%2 == 0 else 9
        quoins += [_inset_rect(0, row*4, edge, row*4+4, 0, 'stone', .25),
                   _inset_rect(edge, row*4, 16, row*4+4, .75, 'plaster', .25)]
    add('wall_quoin_stone', 'Stone quoin and plaster wall', 'Стена с каменными рустовыми блоками',
        'stone', quoins, relief='alternating-quoin-edge', joint=.25)

    large_panels = []
    for row in range(2):
        for col in range(2):
            large_panels.append(_inset_rect(col*8, row*8, col*8+8, row*8+8,
                                            (.08, .35, .65, .18)[row*2+col],
                                            joint=.35))
    add('wall_large_stone_panels', 'Large-format stone panel wall', 'Стена с крупноформатными каменными панелями',
        'stone', large_panels, relief='four-offset-stone-plates', joint=.35)

    standing_seam = []
    for n in range(4):
        x = n*4
        standing_seam += [_face(x, 0, x+.45, 16, 0, 'trim'),
                         _face(x+.45, 0, x+4, 16, 1.05, 'metal')]
    add('wall_standing_seam_metal', 'Standing-seam metal wall', 'Стена из фальцевых металлических панелей',
        'metal', standing_seam, particle='metal', relief='four-raised-standing-seams')

    cassettes = []
    for x in (0, 8):
        for y in (0, 8):
            cassettes += _framed_tile(x+.15, y+.15, x+7.85, y+7.85,
                                     .55, .10, .95, 'metal', 'trim')
    add('wall_metal_cassettes', 'Recessed metal cassette wall', 'Стена из металлических кассет',
        'metal', cassettes, particle='metal', relief='four-recessed-cassettes', joint=.30)

    steel_grid = []
    seams = (.0, 5.25, 10.5, 15.75)
    # Horizontal rails run continuously; vertical struts stop at the rails.
    for y in seams:
        steel_grid.append(_face(0, y, 16, y+.25, .05, 'metal'))
    for row in range(3):
        bottom, top = seams[row]+.25, seams[row+1]
        for x in seams:
            steel_grid.append(_face(x, bottom, x+.25, top, .05, 'metal'))
        for col in range(3):
            left, right = seams[col]+.25, seams[col+1]
            steel_grid.append(_face(left+.12, bottom+.12, right-.12, top-.12,
                                     (.48, .90, .68)[(row+col)%3], 'stone'))
    add('wall_steel_grid_stone', 'Steel-grid stone wall', 'Каменная стена в металлической решётке',
        'metal', steel_grid, particle='stone', relief='three-by-three-grid-stone-infill')
    return result


def designs() -> list[dict]:
    """Return all forty wall constructions; palettes are supplied elsewhere."""
    from wall_patterns import designs as interior_patterns
    return _own_designs() + interior_patterns()
