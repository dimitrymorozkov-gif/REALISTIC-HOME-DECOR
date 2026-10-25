"""Curated architectural, outdoor and decorative model templates.

Coordinates are pixels (16 pixels = one metre/block), with the front at z=0.
Only axis-aligned cuboids are used so every model remains a vanilla JSON model.
The shared generator supplies material palettes, clipping and block rotations.
"""


def box(x1, y1, z1, x2, y2, z2, material="wood"):
    return (x1, y1, z1, x2, y2, z2, material)


def four_legs(width, depth, height, inset=1, thickness=1.25, material="wood"):
    return [box(x, 0, z, x + thickness, height, z + thickness, material)
            for x in (inset, width - inset - thickness)
            for z in (inset, depth - inset - thickness)]


def table(width=24, depth=16, height=12, top=1.25, leg=1.5):
    return ([box(0, height - top, 0, width, height, depth, "stone")]
            + four_legs(width, depth, height - top, thickness=leg, material="metal")
            + [box(1 + leg, height - 3, 2, width - 1 - leg, height - 1.25, 3, "wood"),
               box(1 + leg, height - 3, depth - 3, width - 1 - leg, height - 1.25, depth - 2, "wood")])


def framed_panel(width=16, height=32, thickness=1.5, frame=1, glass=True):
    z = 16 - thickness
    return [box(0, 0, z, frame, height, 16, "metal"),
            box(width - frame, 0, z, width, height, 16, "metal"),
            box(frame, 0, z, width - frame, frame, 16, "metal"),
            box(frame, height - frame, z, width - frame, height, 16, "metal"),
            box(frame, frame, z + thickness * .4,
                width - frame, height - frame, z + thickness * .6,
                "glass" if glass else "wood")]


def cabinet(width=24, depth=10, height=24, sections=2):
    boxes = [box(0, 0, 0, width, 1, depth, "metal"),
             box(0, 1, 0, 1, height - 1, depth, "metal"),
             box(width - 1, 1, 0, width, height - 1, depth, "metal"),
             box(1, 1, depth - 1, width - 1, height - 1, depth, "metal"),
             box(0, height - 1, 0, width, height, depth, "metal")]
    span = (width - 2) / sections
    for n in range(sections):
        x = 1 + n * span
        boxes += [box(x + .125, 1, .25, x + span - .125, height - 1, 1, "accent"),
                  box(x + span - 2, height * .45, 0, x + span - 1.5, height * .6, .25, "metal")]
    return boxes


def designs():
    result = []

    def add(identifier, english, russian, category, geometry, placement="floor",
            luminance=0, **params):
        result.append({"id": identifier, "en": english, "ru": russian,
                       "category": category, "placement": placement,
                       "luminance": luminance, "connect": False,
                       "params": params, "boxes": geometry})

    add("chandelier", "Linear chandelier", "Линейная люстра", "lighting",
        [box(4, 15, 5, 12, 16, 11, "metal"),
         box(7.5, 9, 7.5, 8.5, 15, 8.5, "metal"),
         box(1, 8, 7.5, 15, 9, 8.5, "metal")]
        + [b for x in (2, 7, 12) for b in
           (box(x, 5, 6.5, x + 2, 8, 9.5, "light"),
            box(x - .25, 4.5, 6.25, x + 2.25, 5, 9.75, "metal"))],
        "ceiling", 14, width=16, lights=3)
    add("pendant_light", "Pendant shade", "Подвесной светильник", "lighting",
        [box(6, 15, 6, 10, 16, 10, "metal"),
         box(7.75, 7, 7.75, 8.25, 15, 8.25, "metal"),
         box(5, 5, 5, 11, 7, 11, "accent"),
         box(3, 3, 3, 13, 5, 13, "accent"),
         box(4, 2.75, 4, 12, 3, 12, "light")],
        "ceiling", 13, shade="stepped", drop=13)
    add("ceiling_spot", "Recessed ceiling spotlight", "Потолочный точечный светильник", "lighting",
        [box(4, 15, 4, 12, 16, 12, "metal"),
         box(5, 14.5, 5, 11, 15, 11, "light"),
         box(4, 14.5, 4, 5, 15, 12, "accent"),
         box(11, 14.5, 4, 12, 15, 12, "accent"),
         box(5, 14.5, 4, 11, 15, 5, "accent"),
         box(5, 14.5, 11, 11, 15, 12, "accent")],
        "ceiling", 13, width=8)
    add("wall_sconce", "Wall reading sconce", "Настенное бра", "lighting",
        [box(5, 4, 15, 11, 12, 16, "metal"),
         box(7, 5, 14.5, 9, 10, 15, "accent"),
         box(5.5, 10, 14, 10.5, 12, 15, "light"),
         box(5.5, 4, 14, 10.5, 5, 15, "light"),
         box(7.5, 7, 14, 8.5, 9, 14.5, "wood")],
        "wall", 11, projection=2)
    add("led_panel", "Square LED ceiling panel", "Потолочная LED-панель", "lighting",
        [box(1, 15, 1, 15, 16, 15, "metal"),
         box(2, 14.5, 2, 14, 15, 14, "light"),
         box(1, 14.5, 1, 2, 15, 15, "accent"),
         box(14, 14.5, 1, 15, 15, 15, "accent"),
         box(2, 14.5, 1, 14, 15, 2, "accent"),
         box(2, 14.5, 14, 14, 15, 15, "accent")],
        "ceiling", 15, width=14)
    add("led_strip", "Architectural LED strip", "Декоративная LED-лента", "lighting",
        [box(0, 7, 15, 16, 9, 16, "metal"),
         box(.5, 7.5, 14.75, 15.5, 8.5, 15, "light"),
         box(0, 7, 14.75, .5, 9, 15, "accent"),
         box(15.5, 7, 14.75, 16, 9, 15, "accent")],
        "wall", 11, length=16)
    add("garden_bollard", "Garden light bollard", "Садовый светильник", "lighting",
        [box(5, 0, 5, 11, 1, 11, "metal"),
         box(6, 1, 6, 10, 10, 10, "metal"),
         box(6, 10, 6, 10, 13, 10, "light"),
         box(5.5, 13, 5.5, 10.5, 14, 10.5, "metal"),
         box(5.75, 11, 5.75, 6.25, 12, 10.25, "metal"),
         box(9.75, 11, 5.75, 10.25, 12, 10.25, "metal")],
        luminance=12, height=14)

    add("panoramic_window", "Panoramic window", "Панорамное окно", "architecture",
        framed_panel(32, 32, 1.5, 1)[:4]
        + [box(1, 1, 15.1, 15.5, 31, 15.4, "glass"),
           box(16.5, 1, 15.1, 31, 31, 15.4, "glass"),
           box(15.5, 1, 14.5, 16.5, 31, 16, "metal")],
        "wall", width=32, height=32)
    add("narrow_window", "Narrow window", "Узкое окно", "architecture",
        framed_panel(8, 24, 1.5, 1)[:4]
        + [box(1, 1, 15.1, 7, 11.5, 15.4, "glass"),
           box(1, 12.5, 15.1, 7, 23, 15.4, "glass"),
           box(1, 11.5, 14.5, 7, 12.5, 16, "metal")],
        "wall", width=8, height=24)
    add("static_door", "Static entrance door", "Декоративная входная дверь", "architecture",
        framed_panel(16, 32, 1.5, 1, False)
        + [box(2, 2, 14.25, 14, 10, 14.5, "accent"),
           box(2, 12, 14.25, 14, 20, 14.5, "accent"),
           box(2, 22, 14.25, 14, 30, 14.5, "accent"),
           box(12, 13, 14, 12.5, 19, 14.25, "metal"),
           box(1, 7, 14.25, 1.5, 10, 14.5, "metal"),
           box(1, 23, 14.25, 1.5, 26, 14.5, "metal")],
        width=16, height=32)
    add("glass_door", "Static glazed door", "Декоративная стеклянная дверь", "architecture",
        framed_panel(16, 32, 1.5, 1)
        + [box(12, 12, 14, 12.5, 20, 14.5, "metal"),
           box(1, 4, 14.25, 15, 5, 14.75, "metal"),
           box(1, 27, 14.25, 15, 28, 14.75, "metal")],
        width=16, height=32)
    add("wall_panel", "Framed wall panel", "Декоративная стеновая панель", "architecture",
        [box(0, 0, 15, 16, 16, 16, "wood"),
         box(1, 1, 14.5, 2, 15, 15, "accent") + ("left",),
         box(14, 1, 14.5, 15, 15, 15, "accent") + ("right",),
         box(2, 1, 14.5, 14, 2, 15, "accent"),
         box(2, 14, 14.5, 14, 15, 15, "accent")],
        "wall", projection=1.5)
    result[-1]["connect"] = True
    add("slatted_panel", "Vertical slat panel", "Реечная стеновая панель", "architecture",
        [box(0, 0, 15.5, 16, 16, 16, "metal")]
        + [box(x, 0, 14, x + 1, 16, 15.5, "wood") for x in range(0, 16, 2)],
        "wall", slats=8, projection=2)
    add("handrail", "Slim metal railing", "Тонкие металлические перила", "architecture",
        [box(0, 14, 7, 16, 15, 9, "wood"),
         box(.5, 0, 7.5, 1.5, 14, 8.5, "metal") + ("left",),
         box(14.5, 0, 7.5, 15.5, 14, 8.5, "metal") + ("right",)]
        + [box(x, 2, 7.75, x + .5, 14, 8.25, "metal") for x in (4, 7.75, 11.5)],
        width=16, height=15)
    result[-1]["connect"] = True
    add("column", "Architectural column", "Декоративная колонна", "architecture",
        [box(2, 0, 2, 14, 2, 14, "stone"),
         box(3, 2, 3, 13, 3, 13, "stone"),
         box(4, 3, 4, 12, 29, 12, "concrete"),
         box(3, 29, 3, 13, 30, 13, "stone"),
         box(2, 30, 2, 14, 32, 14, "stone")],
        width=12, height=32)

    add("parquet_floor", "Herringbone parquet panel", "Панель паркета", "building_materials",
        [box(0, 0, 0, 16, 15.5, 16, "wood")]
        + [box(x, 15.5, z, x + 3.875, 16, z + 7.875, "wood")
           for x in (0, 4, 8, 12) for z in (0, 8)],
        "any", pattern="planks")
    add("ceramic_tiles", "Ceramic floor tiles", "Керамическая плитка", "building_materials",
        [box(0, 0, 0, 16, 15.75, 16, "concrete")]
        + [box(x, 15.75, z, x + 7.875, 16, z + 7.875, "ceramic")
           for x in (0, 8) for z in (0, 8)],
        "any", pattern="grouted")
    add("marble_slab", "Polished marble block", "Полированный мрамор", "building_materials",
        [box(0, 0, 0, 16, 16, 16, "stone")], "any", finish="polished")
    add("concrete_block", "Architectural concrete", "Архитектурный бетон", "building_materials",
        [box(0, 0, 0, 16, 16, 16, "concrete")], "any", finish="matte")
    add("brick_cladding", "Brick cladding panel", "Кирпичная облицовка", "building_materials",
        [box(0, 0, 15.5, 16, 16, 16, "concrete")]
        + [box(x1, y, 14, x2, y + 3.75, 15.5, "stone")
           for y in (0, 4, 8, 12)
           for x1, x2 in (((0, 7.75), (8, 16)) if y % 8 == 0
                          else ((0, 3.75), (4, 11.75), (12, 16)))],
        "wall", courses=4)
    add("metal_cladding", "Seamed metal panel", "Металлическая стеновая панель", "building_materials",
        [box(0, 0, 15, 16, 16, 16, "metal")]
        + [box(x, 0, 14.5, x + .5, 16, 15, "accent") for x in (0, 5, 10, 15.5)],
        "wall", seams=4)

    add("book_stack", "Stack of art books", "Стопка книг об искусстве", "decorations",
        [box(2, 0, 3, 13, .5, 12, "accent"),
         box(2.5, .5, 3.5, 12.5, 2, 11.5, "book"),
         box(2, 2, 3, 13, 2.5, 12, "accent"),
         box(3, 2.5, 2, 12, 3, 13, "wood"),
         box(3.5, 3, 2.5, 11.5, 4, 12.5, "book"),
         box(3, 4, 2, 12, 4.5, 13, "wood")],
        "any", books=2)
    add("vase", "Stepped ceramic vase", "Керамическая ваза", "decorations",
        [box(6, 0, 6, 10, 1, 10, "ceramic"),
         box(4, 1, 4, 12, 6, 12, "ceramic"),
         box(5, 6, 5, 11, 8, 11, "ceramic"),
         box(6, 8, 6, 10, 12, 10, "ceramic"),
         box(5.5, 12, 5.5, 6.5, 13, 10.5, "ceramic"),
         box(9.5, 12, 5.5, 10.5, 13, 10.5, "ceramic"),
         box(6.5, 12, 5.5, 9.5, 13, 6.5, "ceramic"),
         box(6.5, 12, 9.5, 9.5, 13, 10.5, "ceramic")],
        "any", height=13, silhouette="stepped")
    add("wall_clock", "Minimal wall clock", "Минималистичные настенные часы", "decorations",
        [box(2, 2, 15, 14, 14, 16, "metal"),
         box(3, 3, 14.75, 13, 13, 15, "ceramic"),
         box(7.75, 8.5, 14.25, 8.25, 12, 14.75, "metal"),
         box(8.5, 7.75, 14, 11, 8.25, 14.5, "metal"),
         box(7.5, 7.5, 13.875, 8.5, 8.5, 14.25, "accent")]
        + [box(x, y, 14.5, x + .5, y + .5, 14.75, "metal")
           for x, y in ((7.75, 12), (12, 7.75), (7.75, 3.5), (3.5, 7.75))],
        "wall", width=12)
    add("picture_frame", "Framed abstract artwork", "Картина в рамке", "decorations",
        [box(1, 1, 15, 15, 15, 16, "wood"),
         box(2, 2, 14.75, 14, 14, 15, "book"),
         box(4, 4, 14.5, 8, 12, 14.75, "accent"),
         box(8, 4, 14.5, 12, 8, 14.75, "stone"),
         box(8, 8, 14.5, 10, 10, 14.75, "metal")],
        "wall", artwork="original_geometric")
    add("soap_dispenser", "Soap dispenser", "Дозатор мыла", "decorations",
        [box(5, 0, 5, 11, .75, 11, "ceramic"),
         box(5.5, .75, 5.5, 10.5, 7, 10.5, "ceramic"),
         box(6.5, 7, 6.5, 9.5, 8, 9.5, "metal"),
         box(7.5, 8, 7.5, 8.5, 9, 8.5, "metal"),
         box(7.5, 9, 3.5, 8.5, 9.5, 8.5, "metal")],
        "any", height=9.5)
    add("candle_set", "Decorative candle trio", "Набор декоративных свечей", "decorations",
        [box(2, 0, 2, 14, .75, 14, "stone")]
        + [b for x, z, h in ((3, 3, 5), (8, 4, 8), (5, 9, 6))
           for b in (box(x, .75, z, x + 3, h, z + 3, "ceramic"),
                     box(x + 1.25, h, z + 1.25, x + 1.75, h + .5, z + 1.75, "metal"))],
        "any", candles=3)
    add("power_outlet", "Decorative power outlet", "Декоративная розетка", "decorations",
        [box(4, 4, 15.5, 12, 12, 16, "ceramic"),
         box(5, 5, 15.25, 11, 11, 15.5, "accent"),
         box(6, 7, 15, 6.75, 8.5, 15.25, "metal"),
         box(9.25, 7, 15, 10, 8.5, 15.25, "metal"),
         box(7.5, 9, 15, 8.5, 10, 15.25, "metal")],
        "wall", projection=1)

    add("garden_table", "Outdoor dining table", "Садовый обеденный стол", "outdoor",
        four_legs(24, 16, 11, material="metal")
        + [box(0, 11, z, 24, 12, z + 2.8, "wood") for z in (0, 3.25, 6.5, 9.75, 13)]
        + [box(2.25, 9.5, 2, 21.75, 10.5, 3, "metal"),
           box(2.25, 9.5, 13, 21.75, 10.5, 14, "metal")],
        width=24, depth=16, height=12, top="slatted")
    add("garden_chair", "Slatted garden chair", "Реечное садовое кресло", "outdoor",
        four_legs(12, 12, 7, material="metal")
        + [box(1, 7, z, 11, 8, z + 1.75, "wood") for z in (1, 3.25, 5.5, 7.75)]
        + [box(1, 8, 10, 2, 16, 11, "metal"), box(10, 8, 10, 11, 16, 11, "metal")]
        + [box(2, y, 10, 10, y + 1.5, 11, "wood") for y in (10, 12.5, 15)]
        + [box(.5, 11, 1, 1.5, 12, 10, "wood"),
           box(10.5, 11, 1, 11.5, 12, 10, "wood")],
        width=12, height=16)
    add("sun_lounger", "Poolside sun lounger", "Садовый шезлонг", "outdoor",
        four_legs(12, 30, 4, material="metal")
        + [box(1, 4, 1, 11, 5, 21, "wood"),
           box(1.25, 5, 1.25, 10.75, 6, 20.75, "fabric"),
           box(1, 5, 21, 11, 7, 24, "wood"),
           box(1, 7, 24, 11, 9, 27, "wood"),
           box(1, 9, 27, 11, 11, 30, "wood"),
           box(1.25, 7, 21, 10.75, 8, 24, "fabric"),
           box(1.25, 9, 24, 10.75, 10, 27, "fabric"),
           box(1.25, 11, 27, 10.75, 12, 30, "fabric")],
        width=12, depth=30, height=12)
    add("parasol", "Garden parasol", "Садовый зонт", "outdoor",
        [box(5, 0, 5, 11, 1, 11, "stone"),
         box(7.5, 1, 7.5, 8.5, 24, 8.5, "metal"),
         box(1, 24, 0, 15, 25, 16, "fabric"),
         box(2, 25, 2, 14, 26, 14, "fabric"),
         box(4, 26, 4, 12, 27, 12, "fabric"),
         box(6, 27, 6, 10, 28, 10, "fabric"),
         box(0, 24, 0, 1, 25.25, 16, "accent"),
         box(15, 24, 0, 16, 25.25, 16, "accent")],
        width=16, height=28)
    add("planter", "Architectural planter", "Кашпо с растением", "outdoor",
        [box(4, 0, 4, 12, 2, 12, "ceramic"),
         box(3, 2, 3, 13, 8, 13, "ceramic"),
         box(2, 8, 2, 14, 9, 14, "ceramic"),
         box(3, 9, 3, 13, 9.25, 13, "wood"),
         box(7, 9.25, 7, 9, 16, 9, "wood"),
         box(4, 12, 4, 12, 18, 12, "leaf"),
         box(2, 14, 6, 14, 17, 10, "leaf"),
         box(6, 17, 6, 10, 21, 10, "leaf")],
        width=12, height=21)
    add("garden_gate", "Static garden gate", "Декоративная садовая калитка", "outdoor",
        [box(0, 0, 7, 2, 24, 9, "metal"),
         box(14, 0, 7, 16, 24, 9, "metal"),
         box(2, 2, 7.5, 14, 3, 8.5, "metal"),
         box(2, 21, 7.5, 14, 22, 8.5, "metal")]
        + [box(x, 3, 7.75, x + .75, 21, 8.25, "metal") for x in (3, 5.25, 7.5, 9.75, 12)]
        + [box(11, 11, 7, 13, 12, 7.5, "accent")],
        width=16, height=24)
    add("mailbox", "Post-mounted mailbox", "Почтовый ящик на стойке", "outdoor",
        [box(5, 0, 5, 11, 1, 11, "stone"),
         box(7, 1, 7, 9, 13, 9, "metal"),
         box(3, 13, 3, 13, 19, 12, "metal"),
         box(4, 19, 4, 12, 20, 11, "metal"),
         box(4, 14, 2.5, 12, 18, 3, "accent"),
         box(5, 17, 2.25, 11, 17.5, 2.5, "screen"),
         box(10, 14.5, 2, 10.5, 16, 2.5, "metal")],
        width=10, height=20)

    add("garage_workbench", "Garage workbench", "Гаражный верстак", "garage",
        table(32, 16, 14, 2, 2)
        + [box(2, 2, 3, 30, 3, 13, "wood"),
           box(1, 14, 1, 7, 15.5, 5, "metal"),
           box(2, 15.5, 1, 6, 17, 2, "metal"),
           box(2, 15.5, 4, 6, 17, 5, "metal"),
           box(3.5, 15, 0, 4.5, 16, 1, "accent")],
        width=32, height=17, vice=True)
    add("tool_cabinet", "Garage tool cabinet", "Гаражный шкаф для инструментов", "garage",
        cabinet(24, 10, 24, 2)
        + [box(3, y, .125, 10, y + .25, .25, "screen") for y in (3, 4, 5)],
        width=24, height=24, sections=2)
    add("tool_rack", "Wall tool rack", "Настенная панель инструментов", "garage",
        [box(0, 0, 15.5, 16, 16, 16, "wood"),
         box(0, 0, 15, 16, 1, 15.5, "metal"),
         box(0, 15, 15, 16, 16, 15.5, "metal"),
         box(3, 3, 14, 4, 10, 15, "wood"),
         box(1.5, 10, 14, 5.5, 12, 15, "metal"),
         box(8, 5, 14, 9, 12, 15, "metal"),
         box(7, 3, 14, 10, 5, 15, "accent"),
         box(12, 3, 14, 13, 9, 15, "accent"),
         box(12.25, 9, 14.25, 12.75, 13, 14.75, "metal")],
        "wall", width=16, tools=3)
    add("toolbox", "Portable toolbox", "Ящик для инструментов", "garage",
        [box(2, 0, 3, 14, 6, 13, "metal"),
         box(2, 6, 3, 14, 7, 13, "accent"),
         box(5, 7, 7, 6, 9, 9, "metal"),
         box(10, 7, 7, 11, 9, 9, "metal"),
         box(6, 8, 7, 10, 9, 9, "metal"),
         box(4, 4, 2.5, 5, 6, 3, "accent"),
         box(11, 4, 2.5, 12, 6, 3, "accent")],
        width=12, height=9)
    add("storage_crate", "Reinforced storage crate", "Усиленный декоративный ящик", "garage",
        [box(1, 0, 1, 15, 13, 15, "wood"),
         box(1, 13, 1, 15, 14, 15, "wood")]
        + [box(x, 0, z, x + 1, 14, z + 1, "metal")
           for x in (0, 15) for z in (0, 15)]
        + [box(1, y, 0, 15, y + .75, .5, "metal") for y in (2, 11)]
        + [box(6, 7, .25, 10, 8.5, .75, "metal")],
        width=16, height=14)
    add("garage_door", "Static sectional garage door", "Декоративные гаражные ворота", "garage",
        [box(0, 0, 14, 1, 32, 16, "metal"),
         box(31, 0, 14, 32, 32, 16, "metal"),
         box(1, 31, 14, 31, 32, 16, "metal")]
        + [box(1, y, 15, 31, min(y + 7.75, 31), 16, "accent") for y in (0, 8, 16, 24)]
        + [box(x, 25, 14.75, x + 6, 29, 15, "glass") for x in (3, 13, 23)]
        + [box(14, 6, 14.5, 18, 7, 15, "metal")],
        width=32, height=32)
    return result
