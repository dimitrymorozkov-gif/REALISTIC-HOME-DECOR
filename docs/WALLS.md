# Стеновые конструкции

**40 разных рельефных конструкций × 8 палитр = 320 блоков стен.**

Все конструкции находятся во вкладке Building Materials / Строительные материалы. Каждый блок занимает одну ячейку, имеет собственную объёмную кладку или панельный рельеф и поворачивается при размещении. Стены можно строить друг на друге; опора сзади не требуется. Декоративная лицевая сторона модели NORTH направлена к северу, Z=0.

Общая основа использует согласованный материал швов `mortar`, лицевая поверхность — дерево, камень, штукатурку, бетон или металл, рамки — `trim`. Палитры изменяют настоящие материалы видимой поверхности; одни только названия не создают варианты.

Физическая коллизия и рамка выделения новых строительных стен занимают полную ячейку 1×1×1 м, как у обычных строительных блоков Minecraft. Неглубокий рельеф сохранён в модели. Стены непрозрачны для света; полноценная ячейка обеспечивает стандартное освещение утопленных граней без собственного рендера или свечения. Это правило применяется только к 40 новым стеновым конструкциям: прежняя мебель сохраняет свои точные коллизии.

| ID конструкции | English | Русский | Семейство |
|---|---|---|---|
| `wall_running_brick` | Running-bond brick wall | Стена с ложковой кладкой | masonry |
| `wall_stack_brick` | Stack-bond brick wall | Стена с прямой кирпичной кладкой | masonry |
| `wall_flemish_bond` | Flemish-bond brick wall | Стена с фламандской кладкой | masonry |
| `wall_english_bond` | English-bond brick wall | Стена с английской кладкой | masonry |
| `wall_soldier_brick` | Soldier-course brick wall | Стена с вертикальной кладкой | masonry |
| `wall_basket_brick` | Basket-weave brick wall | Стена с плетёной кирпичной кладкой | masonry |
| `wall_herringbone_brick` | Herringbone brick wall | Кирпичная стена ёлочкой | masonry |
| `wall_rusticated_brick` | Rusticated masonry wall | Стена с рельефным рустом | masonry |
| `wall_roman_brick` | Roman brick wall | Стена из длинного римского кирпича | masonry |
| `wall_breeze_brick` | Recessed breeze-block wall | Стена с нишами бриз-блоков | masonry |
| `wall_ashlar_stone` | Coursed ashlar stone wall | Стена из тесаного камня | stone |
| `wall_dry_stone` | Dry-stacked stone wall | Стена сухой каменной кладки | stone |
| `wall_cyclopean_stone` | Irregular mosaic stone wall | Стена из разновеликого камня | stone |
| `wall_slate_ledger` | Split-face stone ledger wall | Стена из колотых каменных ламелей | stone |
| `wall_travertine_bands` | Banded stone wall with inlays | Каменная стена с горизонтальными вставками | stone |
| `wall_quoin_stone` | Stone quoin and plaster wall | Стена с каменными рустовыми блоками | stone |
| `wall_large_stone_panels` | Large-format stone panel wall | Стена с крупноформатными каменными панелями | stone |
| `wall_standing_seam_metal` | Standing-seam metal wall | Стена из фальцевых металлических панелей | metal |
| `wall_metal_cassettes` | Recessed metal cassette wall | Стена из металлических кассет | metal |
| `wall_steel_grid_stone` | Steel-grid stone wall | Каменная стена в металлической решётке | metal |
| `wall_wood_vertical_slats` | Vertical timber slat wall | Стена с вертикальными деревянными рейками | wood |
| `wall_wood_board_batten` | Board-and-batten wall | Стена из досок с нащельниками | wood |
| `wall_wood_shiplap` | Horizontal shiplap wall | Стена с горизонтальной обшивкой внахлёст | wood |
| `wall_wood_coffered` | Timber coffered wall | Деревянная кессонная стена | wood |
| `wall_wood_wainscot` | Timber wainscot wall | Стена с деревянными панелями и цоколем | wood |
| `wall_wood_basket_parquet` | Basket-weave timber wall | Деревянная стена с плетёным паркетным узором | wood |
| `wall_concrete_formwork` | Formwork concrete wall with tie recesses | Бетонная стена со следами опалубки и стяжек | concrete |
| `wall_concrete_fluted` | Broad-fluted concrete wall | Бетонная стена с широкими каннелюрами | concrete |
| `wall_concrete_stepped_fins` | Stepped concrete fin wall | Бетонная стена со ступенчатыми рёбрами | concrete |
| `wall_concrete_deep_coffers` | Deep-coffered concrete wall | Бетонная стена с глубокими кессонами | concrete |
| `wall_concrete_staggered_precast` | Staggered precast concrete wall | Стена из сборных бетонных панелей со смещением | concrete |
| `wall_concrete_vertical_channel` | Channelled concrete wall | Бетонная стена с глубоким вертикальным каналом | concrete |
| `wall_plaster_picture_frame` | Picture-molding plaster wall | Штукатурная стена с узким рамочным молдингом | plaster |
| `wall_plaster_stepped_arch` | Stepped arched niche wall | Штукатурная стена со ступенчатой арочной нишей | plaster |
| `wall_plaster_recessed_rectangles` | Asymmetric recessed plaster wall | Штукатурная стена с асимметричными прямоугольными нишами | plaster |
| `wall_plaster_pyramid_tiles` | Stepped pyramid tile wall | Стена со ступенчатыми пирамидальными панелями | plaster |
| `wall_plaster_stepped_chevron` | Stepped chevron relief wall | Стена со ступенчатым шевронным рельефом | plaster |
| `wall_acoustic_baffles` | Staggered acoustic baffle wall | Стена с акустическими ламелями разной длины | acoustic |
| `wall_acoustic_checker` | Acoustic checkerboard relief wall | Стена с шахматным акустическим рельефом | acoustic |
| `wall_plaster_geometric_cross` | Geometric cross relief wall | Штукатурная стена с геометрическим крестообразным рельефом | plaster |

ID блока: `realistic_home_decor:<конструкция>_<палитра>`, например `realistic_home_decor:wall_running_brick_terracotta`.

Доступные палитры: Натуральный дуб (`oak`); Орех и латунь (`walnut`); Эбен и графит (`ebony`); Слоновая кость и берёза (`ivory`); Шалфей и сосна (`sage`); Терракота и медь (`terracotta`); Песок и шампань (`sand`); Сланец и стальной синий (`slate`).
