package com.realistichomedecor.smoke;

import com.realistichomedecor.RealisticHomeDecor;
import com.realistichomedecor.block.ConnectingFurnitureBlock;
import com.realistichomedecor.block.FurnitureBlock;
import com.realistichomedecor.catalog.FurnitureDefinition;
import com.realistichomedecor.item.FurnitureBlockItem;
import com.realistichomedecor.registry.ModBlocks;
import com.realistichomedecor.util.FurnitureGeometry.Box;
import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.item.ItemEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.DirectionalPlaceContext;
import net.minecraft.world.level.LightLayer;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.shapes.BooleanOp;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.ArrayDeque;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Development-only integration mod. Tests invoke vanilla BlockItem.place against
 * a real dedicated server, including its scheduled block ticks and loot tables.
 * This source set and its mod metadata are excluded from the distributable JAR.
 */
public final class FurnitureSmokeTests implements ModInitializer {
    private static final Logger LOGGER = LoggerFactory.getLogger("rhd_smoke_test");
    private static final BlockPos ORIGIN = new BlockPos(8, 200, 8);
    private static final BlockPos BLOCK_LIGHT_BARRIER = new BlockPos(24, 220, 9);
    private static final BlockPos SKY_LIGHT_BARRIER = new BlockPos(20, 234, 8);
    private static final List<Direction> FACINGS = List.of(Direction.NORTH, Direction.EAST, Direction.SOUTH, Direction.WEST);
    private final ArrayDeque<Step> steps = new ArrayDeque<>();
    private ServerLevel level;
    private List<FurnitureDefinition> catalog;
    private int catalogIndex;
    private int assertions;
    private int placements;
    private boolean started;
    private boolean finished;
    private boolean extraTestsQueued;
    private Step waiting;
    private int waitTicks;

    private record Step(int delayTicks, Runnable action) { }

    @Override
    public void onInitialize() {
        ServerLifecycleEvents.SERVER_STARTED.register(server -> guarded(server, () -> begin(server)));
        ServerTickEvents.END_SERVER_TICK.register(server -> {
            if (started && !finished) guarded(server, () -> tick(server));
        });
    }

    private void begin(MinecraftServer server) {
        level = server.overworld();
        catalog = ModBlocks.definitions();
        check(catalog.size() >= 320, "Expected the full catalog of at least 320 primary items");
        check(ModBlocks.allItems().size() == catalog.size(), "Primary registry item count matches catalog");
        int parts = catalog.stream().mapToInt(definition -> definition.parts().size()).sum();
        check(ModBlocks.allBlocks().size() == parts, "Registry block-cell count matches catalog");
        Set<String> categories = new HashSet<>();
        for (FurnitureDefinition definition : catalog) {
            categories.add(definition.category());
            check(BuiltInRegistries.ITEM.getKey(ModBlocks.primaryItem(definition.id())).equals(RealisticHomeDecor.id(definition.id())),
                    definition.id() + ": registered primary item identifier");
            for (FurnitureDefinition.Part part : definition.parts()) {
                check(BuiltInRegistries.BLOCK.getKey(ModBlocks.getBlock(part.id())).equals(RealisticHomeDecor.id(part.id())),
                        part.id() + ": registered block identifier");
            }
        }
        check(categories.size() == 11, "Eleven furniture creative categories are present");
        // Scheduled cleanup must be exercised even though this test server has no players.
        for (int x = -1; x <= 2; x++) {
            for (int z = -1; z <= 1; z++) {
                level.getChunk(x, z);
                level.setChunkForced(x, z, true);
            }
        }
        for (BlockPos position : BlockPos.betweenClosed(-1, 196, -1, 25, 212, 25)) {
            level.setBlock(position, Blocks.AIR.defaultBlockState(), Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE);
        }
        assertLightingCaches();
        started = true;
        LOGGER.info("RHD_SMOKE_START catalog={} block_cells={}", catalog.size(), parts);
    }

    private void tick(MinecraftServer server) {
        // Real item placement is intentionally spread over ticks to avoid hiding a stalled server.
        if (catalogIndex < catalog.size()) {
            int end = Math.min(catalogIndex + 20, catalog.size());
            while (catalogIndex < end) {
                FurnitureDefinition definition = catalog.get(catalogIndex++);
                successfulPlacement(definition, Direction.NORTH, ORIGIN);
                cleanup(definition, Direction.NORTH, ORIGIN);
            }
            return;
        }
        if (!extraTestsQueued) {
            queueExtraTests();
            extraTestsQueued = true;
        }
        if (waiting == null) {
            waiting = steps.poll();
            if (waiting == null) {
                finished = true;
                for (int x = -1; x <= 2; x++) {
                    for (int z = -1; z <= 1; z++) level.setChunkForced(x, z, false);
                }
                LOGGER.info("RHD_SMOKE_PASS assertions={} placements={} catalog={}", assertions, placements, catalog.size());
                if (!Boolean.getBoolean("rhd.smoke.keepRunning")) server.halt(false);
                return;
            }
            waitTicks = waiting.delayTicks();
        }
        if (waitTicks-- > 0) return;
        waiting.action().run();
        waiting = null;
    }

    private void queueExtraTests() {
        FurnitureDefinition multi = catalog.stream().filter(definition -> definition.parts().size() > 1
                        && definition.placement() == FurnitureDefinition.Placement.FLOOR
                        && definition.parts().stream().anyMatch(part -> part.offset().x() > 0 || part.offset().z() > 0))
                .findFirst().orElseThrow();
        FurnitureDefinition wall = catalog.stream().filter(definition -> definition.placement() == FurnitureDefinition.Placement.WALL)
                .findFirst().orElseThrow();
        FurnitureDefinition ceiling = catalog.stream().filter(definition -> definition.placement() == FurnitureDefinition.Placement.CEILING)
                .findFirst().orElseThrow();
        FurnitureDefinition connected = catalog.stream().filter(definition -> definition.connect()
                        && definition.parts().size() == 1 && definition.placement() == FurnitureDefinition.Placement.FLOOR)
                .findFirst().orElseThrow();
        for (FurnitureDefinition definition : List.of(multi, wall, ceiling)) {
            for (Direction facing : FACINGS) {
                steps.add(new Step(0, () -> {
                    successfulPlacement(definition, facing, ORIGIN);
                    cleanup(definition, facing, ORIGIN);
                }));
            }
        }
        for (Direction facing : FACINGS) {
            BlockPos second = ORIGIN.relative(facing.getClockWise());
            steps.add(new Step(0, () -> {
                successfulPlacement(connected, facing, ORIGIN);
                successfulPlacement(connected, facing, second, true, false);
            }));
            steps.add(new Step(2, () -> {
                assertConnections(connected, facing, ORIGIN, false, true);
                assertConnections(connected, facing, second, true, false);
                check(level.destroyBlock(second, false), "Connected neighbor is actually destroyed");
            }));
            steps.add(new Step(2, () -> {
                assertConnections(connected, facing, ORIGIN, false, false);
                cleanup(connected, facing, ORIGIN);
                cleanup(connected, facing, second);
            }));
        }
        steps.add(new Step(0, () -> blockedCellIsAtomic(multi)));
        for (FurnitureDefinition definition : List.of(multi, wall, ceiling)) {
            steps.add(new Step(0, () -> missingSupportIsRejected(definition)));
            steps.add(new Step(0, () -> {
                removeDrops();
                successfulPlacement(definition, Direction.NORTH, ORIGIN);
                level.destroyBlock(support(definition, Direction.NORTH, ORIGIN), false);
            }));
            steps.add(new Step(3, () -> {
                assertAbsent(definition, Direction.NORTH, ORIGIN, "support removal cleanup");
                check(dropCount(definition) == 1, definition.id() + ": support removal emits one primary item");
                cleanup(definition, Direction.NORTH, ORIGIN);
                removeDrops();
            }));
        }
        // An actual secondary destruction must schedule collapse and drop the primary exactly once.
        steps.add(new Step(0, () -> {
            removeDrops();
            successfulPlacement(multi, Direction.EAST, ORIGIN);
            level.destroyBlock(position(multi.parts().get(1), Direction.EAST, ORIGIN), true);
        }));
        steps.add(new Step(3, () -> {
            assertAbsent(multi, Direction.EAST, ORIGIN, "secondary destruction cleanup");
            check(dropCount(multi) == 1, multi.id() + ": secondary destruction emits one primary item");
            cleanup(multi, Direction.EAST, ORIGIN);
            removeDrops();
        }));
        // Repeat across a loaded chunk boundary, covering origin recovery in a neighboring chunk.
        BlockPos boundary = new BlockPos(15, 200, 8);
        Direction crossing = multi.parts().stream().anyMatch(part -> part.offset().x() > 0) ? Direction.NORTH : Direction.WEST;
        steps.add(new Step(0, () -> {
            successfulPlacement(multi, crossing, boundary);
            check(multi.parts().stream().map(part -> position(part, crossing, boundary))
                            .anyMatch(position -> (position.getX() >> 4) != (boundary.getX() >> 4)),
                    "Multiblock fixture actually crosses a chunk boundary");
            BlockPos secondary = position(multi.parts().get(1), crossing, boundary);
            level.destroyBlock(secondary, false);
        }));
        steps.add(new Step(3, () -> {
            assertAbsent(multi, crossing, boundary, "chunk-boundary secondary destruction");
            cleanup(multi, crossing, boundary);
            removeDrops();
        }));
        queueLightingTests();
    }

    /** Inspect the actual cached states consumed by both vanilla light engines. */
    private void assertLightingCaches() {
        int structuralItems = 0;
        int structuralStates = 0;
        int preservedStates = 0;
        int transparentStates = 0;
        int oldWallFurniture = 0;
        Set<String> existingWallFurniture = Set.of("wall_clock", "wall_panel", "wall_sconce", "wall_shelf", "wall_sink");
        for (FurnitureDefinition definition : catalog) {
            if (existingWallFurniture.contains(definition.template())) {
                check(!definition.structuralWall(), definition.id() + ": existing wall-mounted furniture is not a structural wall");
                oldWallFurniture++;
            }
            if (definition.structuralWall()) structuralItems++;
            for (FurnitureDefinition.Part part : definition.parts()) {
                FurnitureBlock block = ModBlocks.getBlock(part.id());
                for (BlockState state : block.getStateDefinition().getPossibleStates()) {
                    VoxelShape actualShape = state.getShape(level, ORIGIN);
                    if (definition.structuralWall()) {
                        check(state.getLightBlock() == 15, part.id() + ": structural wall blocks all incoming light facing " + state.getValue(FurnitureBlock.FACING));
                        check(!state.propagatesSkylightDown(), part.id() + ": structural wall stops direct skylight");
                        check(Block.isShapeFullBlock(actualShape), part.id() + ": structural wall has normal full-cell selection geometry");
                        check(state.canOcclude(), part.id() + ": structural wall participates in ordinary face occlusion");
                        check(state.isSolidRender(), part.id() + ": structural wall retains its solid rendering classification");
                        check(state.isCollisionShapeFullBlock(level, ORIGIN), part.id() + ": structural wall has normal full-cell collision classification");
                        VoxelShape collision = state.getCollisionShape(level, ORIGIN);
                        check(Block.isShapeFullBlock(collision), part.id() + ": structural wall has normal full-cell physical collision");
                        VoxelShape expected = Shapes.empty();
                        for (Box box : part.boxes(false, false)) {
                            expected = Shapes.or(expected, independentlyRotatedBox(box, state.getValue(FurnitureBlock.FACING)));
                        }
                        check(!Shapes.joinIsNotEmpty(expected, collision, BooleanOp.NOT_SAME),
                                part.id() + ": complete physical collision matches the independently rotated catalog collision boxes");
                        structuralStates++;
                    } else {
                        boolean expectedSky = !Block.isShapeFullBlock(actualShape) && state.getFluidState().isEmpty();
                        int expectedOpacity = state.isSolidRender() ? 15 : expectedSky ? 0 : 1;
                        check(state.propagatesSkylightDown() == expectedSky, part.id() + ": existing furniture retains vanilla skylight behavior");
                        check(state.getLightBlock() == expectedOpacity, part.id() + ": existing furniture retains vanilla light attenuation");
                        preservedStates++;
                        if (definition.renderLayer().equals("translucent") && expectedOpacity == 0) transparentStates++;
                    }
                }
            }
        }
        check(structuralItems == 320, "All 40 structural wall constructions in eight palettes receive lighting checks");
        check(structuralStates == 320 * 4, "Every structural wall is checked in all four saved orientations");
        check(oldWallFurniture == 5 * 8, "All five existing wall-furniture types retain their eight palette variants");
        check(transparentStates > 0, "Transparent shower/window/glass furniture still has light-transmitting states");
        LOGGER.info("RHD_SMOKE_LIGHT_CACHES structural_items={} structural_states={} preserved_furniture_states={} transparent_states={}",
                structuralItems, structuralStates, preservedStates, transparentStates);
    }

    /**
     * Exercise actual asynchronous vanilla lighting, with glass positive controls.
     * Stone enclosures leave exactly one route from each source to its target;
     * no test relies solely on a block property or an open outdoor light sample.
     */
    private void queueLightingTests() {
        FurnitureDefinition wall = catalog.stream().filter(FurnitureDefinition::structuralWall).findFirst().orElseThrow();
        steps.add(new Step(0, () -> {
            // A sealed 3x3x5 stone tunnel: glowstone -> wall -> target air.
            for (BlockPos position : BlockPos.betweenClosed(23, 219, 7, 25, 221, 11)) {
                boolean boundary = position.getX() == 23 || position.getX() == 25
                        || position.getY() == 219 || position.getY() == 221
                        || position.getZ() == 7 || position.getZ() == 11;
                setLightingFixture(position, boundary ? Blocks.STONE.defaultBlockState() : Blocks.AIR.defaultBlockState());
            }
            setLightingFixture(BLOCK_LIGHT_BARRIER.north(), Blocks.GLOWSTONE.defaultBlockState());
            setLightingFixture(BLOCK_LIGHT_BARRIER, ModBlocks.getBlock(wall.id()).defaultBlockState().setValue(FurnitureBlock.FACING, Direction.EAST));
            // A sealed 3x3 vertical shaft, open to direct sky only through its roof.
            for (BlockPos position : BlockPos.betweenClosed(19, 230, 7, 21, 234, 9)) {
                boolean boundary = position.getX() == 19 || position.getX() == 21
                        || position.getZ() == 7 || position.getZ() == 9 || position.getY() == 230;
                setLightingFixture(position, boundary ? Blocks.STONE.defaultBlockState() : Blocks.AIR.defaultBlockState());
            }
            for (int y = SKY_LIGHT_BARRIER.getY() + 1; y <= level.getMaxY(); y++) {
                setLightingFixture(new BlockPos(SKY_LIGHT_BARRIER.getX(), y, SKY_LIGHT_BARRIER.getZ()), Blocks.AIR.defaultBlockState());
            }
            setLightingFixture(SKY_LIGHT_BARRIER, ModBlocks.getBlock(wall.id()).defaultBlockState().setValue(FurnitureBlock.FACING, Direction.WEST));
            LOGGER.info("RHD_SMOKE_LIGHT_FIXTURE opaque_wall={}; waiting 20 ticks for torch/skylight propagation", wall.id());
        }));
        steps.add(new Step(20, () -> {
            int source = light(LightLayer.BLOCK, BLOCK_LIGHT_BARRIER.north());
            int blocked = light(LightLayer.BLOCK, BLOCK_LIGHT_BARRIER.south());
            int openSky = light(LightLayer.SKY, SKY_LIGHT_BARRIER.above());
            int blockedSky = light(LightLayer.SKY, SKY_LIGHT_BARRIER.below());
            LOGGER.info("RHD_SMOKE_LIGHT_OPAQUE source_block={} target_block={} open_sky={} target_sky={}", source, blocked, openSky, blockedSky);
            check(source == 15, "Isolated block-light fixture has an active glowstone source");
            check(blocked == 0, "Structural wall prevents real block light entering the sealed tunnel target");
            check(openSky == 15, "Skylight fixture has direct full sky above its roof");
            check(blockedSky == 0, "Structural wall roof prevents real skylight entering the sealed shaft");
            setLightingFixture(BLOCK_LIGHT_BARRIER, Blocks.GLASS.defaultBlockState());
            setLightingFixture(SKY_LIGHT_BARRIER, Blocks.GLASS.defaultBlockState());
        }));
        steps.add(new Step(20, () -> {
            int transmitted = light(LightLayer.BLOCK, BLOCK_LIGHT_BARRIER.south());
            int transmittedSky = light(LightLayer.SKY, SKY_LIGHT_BARRIER.below());
            LOGGER.info("RHD_SMOKE_LIGHT_GLASS target_block={} target_sky={}", transmitted, transmittedSky);
            check(transmitted > 0, "Replacing only the structural barrier with glass admits block light into the same sealed target");
            check(transmittedSky == 15, "Replacing only the structural roof with glass admits full skylight into the same sealed shaft");
            for (BlockPos position : BlockPos.betweenClosed(23, 219, 7, 25, 221, 11)) {
                setLightingFixture(position, Blocks.AIR.defaultBlockState());
            }
            for (BlockPos position : BlockPos.betweenClosed(19, 230, 7, 21, 234, 9)) {
                setLightingFixture(position, Blocks.AIR.defaultBlockState());
            }
            LOGGER.info("RHD_SMOKE_LIGHT_PASS opaque and glass-control propagation checks completed; fixtures removed");
        }));
    }

    private void setLightingFixture(BlockPos position, BlockState state) {
        level.setBlock(position, state, Block.UPDATE_ALL | Block.UPDATE_SUPPRESS_DROPS);
    }

    private int light(LightLayer layer, BlockPos position) {
        return level.getLightEngine().getLayerListener(layer).getLightValue(position);
    }

    private void successfulPlacement(FurnitureDefinition definition, Direction facing, BlockPos origin) {
        successfulPlacement(definition, facing, origin, false, false);
    }

    private void successfulPlacement(FurnitureDefinition definition, Direction facing, BlockPos origin,
                                     boolean left, boolean right) {
        cleanup(definition, facing, origin);
        BlockPos support = support(definition, facing, origin);
        if (support != null) level.setBlock(support, Blocks.STONE.defaultBlockState(), Block.UPDATE_ALL);
        ItemStack stack = new ItemStack(ModBlocks.primaryItem(definition.id()), 2);
        InteractionResult result = place(definition, facing, origin, stack);
        check(result.consumesAction(), definition.id() + ": actual BlockItem.place succeeds facing " + facing);
        check(stack.getCount() == 1, definition.id() + ": successful placement consumes one item");
        placements++;
        for (int index = 0; index < definition.parts().size(); index++) {
            FurnitureDefinition.Part part = definition.parts().get(index);
            BlockPos target = position(part, facing, origin);
            BlockState state = level.getBlockState(target);
            check(state.getBlock() == ModBlocks.getBlock(part.id()), part.id() + ": expected cell is present at " + target);
            check(state.getValue(FurnitureBlock.FACING) == facing, part.id() + ": orientation persists in blockstate");
            check(((FurnitureBlock) state.getBlock()).origin(target, facing).equals(origin), part.id() + ": secondary resolves exact primary origin");
            VoxelShape expected = Shapes.empty();
            for (Box box : part.boxes(left, right)) expected = Shapes.or(expected, independentlyRotatedBox(box, facing));
            check(!Shapes.joinIsNotEmpty(expected, state.getShape(level, target), BooleanOp.NOT_SAME),
                    part.id() + ": full voxel shape matches independently rotated local boxes");
        }
    }

    private void assertConnections(FurnitureDefinition definition, Direction facing, BlockPos origin,
                                   boolean left, boolean right) {
        BlockState state = level.getBlockState(origin);
        check(state.getBlock() == ModBlocks.getBlock(definition.id()), "Connected module remains present facing " + facing);
        check(state.getValue(ConnectingFurnitureBlock.LEFT) == left, "Saved LEFT connection is " + left + " facing " + facing);
        check(state.getValue(ConnectingFurnitureBlock.RIGHT) == right, "Saved RIGHT connection is " + right + " facing " + facing);
        VoxelShape expected = Shapes.empty();
        for (Box box : definition.parts().getFirst().boxes(left, right)) {
            expected = Shapes.or(expected, independentlyRotatedBox(box, facing));
        }
        check(!Shapes.joinIsNotEmpty(expected, state.getShape(level, origin), BooleanOp.NOT_SAME),
                "Connected module has the expected rotated connection-specific collision shape facing " + facing);
    }

    private void blockedCellIsAtomic(FurnitureDefinition definition) {
        cleanup(definition, Direction.NORTH, ORIGIN);
        BlockPos support = support(definition, Direction.NORTH, ORIGIN);
        if (support != null) level.setBlock(support, Blocks.STONE.defaultBlockState(), Block.UPDATE_ALL);
        BlockPos obstructed = position(definition.parts().get(1), Direction.NORTH, ORIGIN);
        level.setBlock(obstructed, Blocks.OBSIDIAN.defaultBlockState(), Block.UPDATE_ALL);
        ItemStack stack = new ItemStack(ModBlocks.primaryItem(definition.id()), 2);
        check(!place(definition, Direction.NORTH, ORIGIN, stack).consumesAction(), "Occupied secondary cell rejects placement");
        check(stack.getCount() == 2, "Rejected multiblock placement does not consume an item");
        for (FurnitureDefinition.Part part : definition.parts()) {
            BlockPos target = position(part, Direction.NORTH, ORIGIN);
            check(target.equals(obstructed) ? level.getBlockState(target).is(Blocks.OBSIDIAN) : level.isEmptyBlock(target),
                    "Rejected placement leaves every cell unchanged: " + part.id());
        }
        level.setBlock(obstructed, Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL);
        cleanup(definition, Direction.NORTH, ORIGIN);
    }

    private void missingSupportIsRejected(FurnitureDefinition definition) {
        cleanup(definition, Direction.NORTH, ORIGIN);
        ItemStack stack = new ItemStack(ModBlocks.primaryItem(definition.id()), 2);
        check(!place(definition, Direction.NORTH, ORIGIN, stack).consumesAction(), definition.id() + ": missing support rejects placement");
        check(stack.getCount() == 2, definition.id() + ": missing support does not consume item");
        assertAbsent(definition, Direction.NORTH, ORIGIN, "missing support atomicity");
    }

    private InteractionResult place(FurnitureDefinition definition, Direction facing, BlockPos origin, ItemStack stack) {
        Direction clickedFace = switch (definition.placement()) {
            case WALL -> facing;
            case CEILING -> Direction.DOWN;
            default -> Direction.UP;
        };
        int top = definition.parts().stream().mapToInt(part -> part.offset().y()).max().orElse(0);
        BlockPos clicked = definition.placement() == FurnitureDefinition.Placement.CEILING ? origin.above(top) : origin;
        var context = new DirectionalPlaceContext(level, clicked, facing.getOpposite(), stack, clickedFace);
        return ((FurnitureBlockItem) ModBlocks.primaryItem(definition.id())).place(context);
    }

    private static BlockPos position(FurnitureDefinition.Part part, Direction facing, BlockPos origin) {
        int x = part.offset().x();
        int z = part.offset().z();
        return switch (facing) {
            case NORTH -> origin.offset(x, part.offset().y(), z);
            case EAST -> origin.offset(-z, part.offset().y(), x);
            case SOUTH -> origin.offset(-x, part.offset().y(), -z);
            case WEST -> origin.offset(z, part.offset().y(), -x);
            default -> throw new IllegalArgumentException("Expected a horizontal test facing");
        };
    }

    private static VoxelShape independentlyRotatedBox(Box box, Direction facing) {
        return switch (facing) {
            case NORTH -> Block.box(box.minX(), box.minY(), box.minZ(), box.maxX(), box.maxY(), box.maxZ());
            case EAST -> Block.box(16 - box.maxZ(), box.minY(), box.minX(), 16 - box.minZ(), box.maxY(), box.maxX());
            case SOUTH -> Block.box(16 - box.maxX(), box.minY(), 16 - box.maxZ(), 16 - box.minX(), box.maxY(), 16 - box.minZ());
            case WEST -> Block.box(box.minZ(), box.minY(), 16 - box.maxX(), box.maxZ(), box.maxY(), 16 - box.minX());
            default -> throw new IllegalArgumentException("Expected a horizontal test facing");
        };
    }

    private static BlockPos support(FurnitureDefinition definition, Direction facing, BlockPos origin) {
        return switch (definition.placement()) {
            case ANY -> null;
            case FLOOR -> origin.below();
            case WALL -> origin.relative(facing.getOpposite());
            case CEILING -> origin.above(definition.parts().stream().mapToInt(part -> part.offset().y()).max().orElse(0) + 1);
        };
    }

    private void cleanup(FurnitureDefinition definition, Direction facing, BlockPos origin) {
        for (FurnitureDefinition.Part part : definition.parts()) {
            BlockPos target = position(part, facing, origin);
            level.setBlock(target, Blocks.AIR.defaultBlockState(), Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE | Block.UPDATE_SUPPRESS_DROPS);
        }
        BlockPos support = support(definition, facing, origin);
        if (support != null) level.setBlock(support, Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL | Block.UPDATE_SUPPRESS_DROPS);
    }

    private void assertAbsent(FurnitureDefinition definition, Direction facing, BlockPos origin, String reason) {
        for (FurnitureDefinition.Part part : definition.parts()) {
            check(level.isEmptyBlock(position(part, facing, origin)), part.id() + ": " + reason);
        }
    }

    private int dropCount(FurnitureDefinition definition) {
        return level.getEntitiesOfClass(ItemEntity.class, new AABB(ORIGIN).inflate(16),
                        entity -> entity.getItem().is(ModBlocks.primaryItem(definition.id())))
                .stream().mapToInt(entity -> entity.getItem().getCount()).sum();
    }

    private void removeDrops() {
        level.getEntitiesOfClass(ItemEntity.class, new AABB(ORIGIN).inflate(24)).forEach(ItemEntity::discard);
    }

    private void check(boolean condition, String message) {
        assertions++;
        if (!condition) throw new AssertionError(message);
    }

    private void guarded(MinecraftServer server, Runnable action) {
        try {
            action.run();
        } catch (Throwable failure) {
            finished = true;
            LOGGER.error("RHD_SMOKE_FAIL assertions={} placements={} catalog_index={}", assertions, placements, catalogIndex, failure);
            // The log marker is required because normal dedicated-server halt has a zero process status.
            server.halt(false);
        }
    }
}
