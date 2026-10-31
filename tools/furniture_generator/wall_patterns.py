"""Twenty original solid wall reliefs, with one block equal to 16 pixels.

The solid core is deliberately behind the relief, never inside it. Every front
patch occupies a disjoint XY rectangle and meets the core at z=1.5. This makes
the models ordinary opaque Minecraft JSON geometry without coincident faces.
"""


def _patch(x1, y1, x2, y2, depth, material):
    return (x1, y1, depth, x2, y2, 1.5, material)


def _ring(x1, y1, x2, y2, width, depth, material):
    """Four non-overlapping pieces of a rectangular molding."""
    return [
        _patch(x1, y1, x2, y1 + width, depth, material),
        _patch(x1, y2 - width, x2, y2, depth, material),
        _patch(x1, y1 + width, x1 + width, y2 - width, depth, material),
        _patch(x2 - width, y1 + width, x2, y2 - width, depth, material),
    ]


def _surface(regions, base=(.3, "plaster")):
    """Partition a face around disjoint rectangular relief/recess regions.

    Region tuples are (x1, y1, x2, y2, depth, material). Adjacent rectangles with
    the same depth/material merge into strips, then identical strips merge
    vertically. Regions never create boxes on top of other boxes.
    """
    xs = sorted({0, 16} | {r[k] for r in regions for k in (0, 2)})
    ys = sorted({0, 16} | {r[k] for r in regions for k in (1, 3)})
    rows = []
    for y1, y2 in zip(ys, ys[1:]):
        row = []
        for x1, x2 in zip(xs, xs[1:]):
            style = base
            for a, b, c, d, depth, material in regions:
                if a <= x1 and x2 <= c and b <= y1 and y2 <= d:
                    style = (depth, material)
                    break
            if row and row[-1][2] == x1 and row[-1][4:] == style:
                row[-1] = (row[-1][0], y1, x2, y2, *style)
            else:
                row.append((x1, y1, x2, y2, *style))
        rows.extend(row)
    merged = []
    for r in rows:
        for i, old in enumerate(merged):
            if old[0] == r[0] and old[2] == r[2] and old[3] == r[1] and old[4:] == r[4:]:
                merged[i] = (old[0], old[1], old[2], r[3], *old[4:])
                break
        else:
            merged.append(r)
    return [_patch(*r) for r in merged]


def designs():
    result = []

    def add(identifier, english, russian, family, geometry, **params):
        result.append({
            "id": identifier, "en": english, "ru": russian,
            "category": "building_materials", "placement": "any",
            "luminance": 0, "connect": False,
            "wall_family": family,
            "particle": "wood" if family == "acoustic" else family,
            "params": {"family": family, "structural": True, **params},
            "boxes": [(0, 0, 1.5, 16, 16, 16, "mortar")] + geometry,
        })

    add("wall_wood_vertical_slats", "Vertical timber slat wall",
        "Стена с вертикальными деревянными рейками", "wood",
        [_patch(x, 0, x + 1.5, 16, .1, "wood") for x in range(0, 16, 2)],
        pattern="separated_full_height_slats", slats=8)

    add("wall_wood_board_batten", "Board-and-batten wall",
        "Стена из досок с нащельниками", "wood",
        [piece for x in range(0, 16, 4) for piece in
         (_patch(x, 0, x + .75, 16, .05, "trim"),
          _patch(x + .75, 0, x + 4, 16, .95, "wood"))],
        pattern="battens_over_broad_boards", boards=4)

    add("wall_wood_shiplap", "Horizontal shiplap wall",
        "Стена с горизонтальной обшивкой внахлёст", "wood",
        [piece for y in range(0, 16, 4) for piece in
         (_patch(0, y, 16, y + 3.5, .4, "wood"),
          _patch(0, y + 3.5, 16, y + 4, 1.2, "trim"))],
        pattern="horizontal_rebated_courses", courses=4)

    add("wall_wood_coffered", "Timber coffered wall",
        "Деревянная кессонная стена", "wood",
        _ring(0, 0, 16, 16, 2, .1, "wood")
        + _ring(2, 2, 14, 14, 1, .65, "trim")
        + [_patch(3, 3, 13, 13, 1.2, "wood")],
        pattern="deep_single_coffer", molding_width=2)

    add("wall_wood_wainscot", "Timber wainscot wall",
        "Стена с деревянными панелями и цоколем", "wood",
        [_patch(0, 0, 16, 1, .1, "trim"),
         _patch(0, 1, 1, 10, .15, "wood"),
         _patch(1, 1, 7.5, 10, 1, "wood"),
         _patch(7.5, 1, 8.5, 10, .15, "wood"),
         _patch(8.5, 1, 15, 10, 1, "wood"),
         _patch(15, 1, 16, 10, .15, "wood"),
         _patch(0, 10, 16, 11, .05, "trim"),
         _patch(0, 11, 16, 15.25, 1.1, "plaster"),
         _patch(0, 15.25, 16, 16, .5, "trim")],
        pattern="lower_twin_panels_with_upper_plaster", dado_height=11)

    parquet = []
    for x, y, vertical in ((0, 0, True), (8, 0, False), (0, 8, False), (8, 8, True)):
        for n in range(4):
            if vertical:
                parquet.append(_patch(x + n * 2 + .1, y + .1,
                                       x + n * 2 + 1.9, y + 7.9, .25, "wood"))
            else:
                parquet.append(_patch(x + .1, y + n * 2 + .1,
                                       x + 7.9, y + n * 2 + 1.9, .25, "wood"))
    add("wall_wood_basket_parquet", "Basket-weave timber wall",
        "Деревянная стена с плетёным паркетным узором", "wood", parquet,
        pattern="alternating_four_board_baskets", baskets=4)

    formwork = []
    for x, y in ((0, 0), (8.125, 0), (0, 8.125), (8.125, 8.125)):
        right, top = x + 7.875, y + 7.875
        formwork += _ring(x, y, right, top, 3.25, .5, "concrete")
        formwork.append(_patch(x + 3.25, y + 3.25, right - 3.25, top - 3.25,
                               1.35, "metal"))
    add("wall_concrete_formwork", "Formwork concrete wall with tie recesses",
        "Бетонная стена со следами опалубки и стяжек", "concrete", formwork,
        pattern="four_cast_panels_with_tie_recesses", panels=4)

    flutes = []
    for x in (0, 4, 8, 12):
        for a, b, depth in ((0, .75, .85), (.75, 1.5, .3), (1.5, 2.5, .05),
                            (2.5, 3.25, .3), (3.25, 4, .85)):
            flutes.append(_patch(x + a, 0, x + b, 16, depth, "concrete"))
    add("wall_concrete_fluted", "Broad-fluted concrete wall",
        "Бетонная стена с широкими каннелюрами", "concrete", flutes,
        pattern="five_step_convex_flutes", flutes=4)

    add("wall_concrete_stepped_fins", "Stepped concrete fin wall",
        "Бетонная стена со ступенчатыми рёбрами", "concrete",
        [_patch(x + n, 0, x + n + 1, 16, n * .4, "concrete")
         for x in (0, 4, 8, 12) for n in range(3)],
        pattern="asymmetric_sawtooth_fins", fins=4)

    coffers = []
    for x, y in ((0, 0), (8, 0), (0, 8), (8, 8)):
        coffers += _ring(x, y, x + 8, y + 8, 1, .1, "concrete")
        coffers += _ring(x + 1, y + 1, x + 7, y + 7, .75, .65, "stone")
        coffers.append(_patch(x + 1.75, y + 1.75, x + 6.25, y + 6.25, 1.3, "concrete"))
    add("wall_concrete_deep_coffers", "Deep-coffered concrete wall",
        "Бетонная стена с глубокими кессонами", "concrete", coffers,
        pattern="four_two_step_coffers", coffers=4)

    precast = []
    for y1, y2, spans in ((0, 5.25, ((0, 7.875), (8.125, 16))),
                           (5.375, 10.625, ((0, 3.875), (4.125, 11.875), (12.125, 16))),
                           (10.75, 16, ((0, 7.875), (8.125, 16)))):
        for x1, x2 in spans:
            precast += _ring(x1, y1, x2, y2, .3, .85, "concrete")
            precast.append(_patch(x1 + .3, y1 + .3, x2 - .3, y2 - .3, .15, "concrete"))
    add("wall_concrete_staggered_precast", "Staggered precast concrete wall",
        "Стена из сборных бетонных панелей со смещением", "concrete", precast,
        pattern="staggered_chamfered_panels", courses=3)

    add("wall_concrete_vertical_channel", "Channelled concrete wall",
        "Бетонная стена с глубоким вертикальным каналом", "concrete",
        [_patch(x1, 0, x2, 16, depth, "concrete") for x1, x2, depth in
         ((0, 5, .1), (5, 5.75, .55), (5.75, 6.5, 1), (6.5, 9.5, 1.35),
          (9.5, 10.25, 1), (10.25, 11, .55), (11, 16, .1))],
        pattern="single_sculpted_recessed_channel", channel_width=6)

    add("wall_plaster_picture_frame", "Picture-molding plaster wall",
        "Штукатурная стена с узким рамочным молдингом", "plaster",
        _ring(0, 0, 16, 16, 3, 1.1, "plaster")
        + [_patch(3, 3, 5, 13, 1.1, "plaster"),
           _patch(11, 3, 13, 13, 1.1, "plaster")]
        + _ring(5, 3, 11, 13, .5, .1, "trim")
        + [_patch(5.5, 3.5, 10.5, 12.5, 1.1, "plaster")],
        pattern="slender_portrait_molding", frame_width=6, frame_height=10)

    arch = [_patch(0, 0, 16, 2, .2, "plaster"),
            _patch(0, 15, 16, 16, .2, "plaster")]
    for y1, y2, inset in ((2, 11, 3), (11, 13, 4), (13, 14, 5), (14, 15, 6)):
        arch += [_patch(0, y1, inset, y2, .2, "plaster"),
                 _patch(inset, y1, 16 - inset, y2, 1.3, "plaster"),
                 _patch(16 - inset, y1, 16, y2, .2, "plaster")]
    add("wall_plaster_stepped_arch", "Stepped arched niche wall",
        "Штукатурная стена со ступенчатой арочной нишей", "plaster", arch,
        pattern="rectilinear_arch_niche", steps=4)

    add("wall_plaster_recessed_rectangles", "Asymmetric recessed plaster wall",
        "Штукатурная стена с асимметричными прямоугольными нишами", "plaster",
        _surface([(1, 2, 6, 14, 1.3, "plaster"),
                  (8, 2, 15, 7, 1.3, "plaster"),
                  (8, 9, 15, 14, 1.3, "plaster")]),
        pattern="one_tall_and_two_landscape_recesses", niches=3)

    pyramids = []
    for x, y in ((0, 0), (8, 0), (0, 8), (8, 8)):
        pyramids += _ring(x, y, x + 8, y + 8, 2, 1.1, "plaster")
        pyramids += _ring(x + 2, y + 2, x + 6, y + 6, 1, .55, "plaster")
        pyramids.append(_patch(x + 3, y + 3, x + 5, y + 5, .05, "plaster"))
    add("wall_plaster_pyramid_tiles", "Stepped pyramid tile wall",
        "Стена со ступенчатыми пирамидальными панелями", "plaster", pyramids,
        pattern="four_raised_three_tier_pyramids", tiles=4)

    chevrons = []
    for row, left in enumerate((0, 2, 4, 6, 6, 4, 2, 0)):
        right = 14 - left
        if left + 2 == right:
            chevrons.append(_patch(left, row * 2, right + 2, row * 2 + 2, .15, "plaster"))
        else:
            chevrons += [_patch(left, row * 2, left + 2, row * 2 + 2, .15, "plaster"),
                         _patch(right, row * 2, right + 2, row * 2 + 2, .15, "plaster")]
    add("wall_plaster_stepped_chevron", "Stepped chevron relief wall",
        "Стена со ступенчатым шевронным рельефом", "plaster", chevrons,
        pattern="tileable_rectilinear_chevrons", steps=8)

    add("wall_acoustic_baffles", "Staggered acoustic baffle wall",
        "Стена с акустическими ламелями разной длины", "acoustic",
        [_patch(x, 0 if n % 2 == 0 else 4, x + 1.5, 12 if n % 2 == 0 else 16,
                .1 if n % 2 == 0 else .65, "wood") for n, x in enumerate(range(0, 16, 2))],
        pattern="alternating_suspended_baffles", baffles=8)

    add("wall_acoustic_checker", "Acoustic checkerboard relief wall",
        "Стена с шахматным акустическим рельефом", "acoustic",
        [_patch(x + .15, y + .15, x + 3.85, y + 3.85,
                .1 if (x + y) % 8 == 0 else .95, "wood")
         for x in (0, 4, 8, 12) for y in (0, 4, 8, 12)],
        pattern="alternating_raised_square_absorbers", tiles=16)

    add("wall_plaster_geometric_cross", "Geometric cross relief wall",
        "Штукатурная стена с геометрическим крестообразным рельефом", "plaster",
        [_patch(6, 0, 10, 16, .1, "trim"),
         _patch(0, 6, 6, 10, .1, "trim"),
         _patch(10, 6, 16, 10, .1, "trim")]
        + [_patch(x1, y1, x2, y2, 1.15, "plaster")
           for x1, y1, x2, y2 in ((0, 0, 6, 6), (10, 0, 16, 6),
                                  (0, 10, 6, 16), (10, 10, 16, 16))],
        pattern="raised_cross_with_four_recessed_quadrants", arm_width=4)
    return result
