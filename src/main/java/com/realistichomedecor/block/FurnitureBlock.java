package com.realistichomedecor.block;

import com.realistichomedecor.catalog.FurnitureDefinition;
import com.realistichomedecor.registry.ModBlocks;
import com.realistichomedecor.util.FurnitureGeometry;
import com.realistichomedecor.util.FurnitureGeometry.GridOffset;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.RandomSource;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.BlockGetter;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.ScheduledTickAccess;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.Mirror;
import net.minecraft.world.level.block.Rotation;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BlockStateProperties;
import net.minecraft.world.level.block.state.properties.EnumProperty;
import net.minecraft.world.phys.shapes.CollisionContext;
import net.minecraft.world.phys.shapes.Shapes;
import net.minecraft.world.phys.shapes.VoxelShape;

import java.util.EnumMap;
import java.util.Map;

/** A baked, static furniture cell. No block entity, animation or continuously running tick. */
public class FurnitureBlock extends Block {
    public static final EnumProperty<Direction> FACING = BlockStateProperties.HORIZONTAL_FACING;
    private final FurnitureDefinition definition;
    private final int partIndex;
    private final Map<Direction, VoxelShape[]> shapes = new EnumMap<>(Direction.class);

    public FurnitureBlock(Properties properties, FurnitureDefinition definition, int partIndex) {
        super(properties);
        this.definition = definition;
        this.partIndex = partIndex;
        registerDefaultState(stateDefinition.any().setValue(FACING, Direction.NORTH));
        var part = definition.parts().get(partIndex);
        for (Direction direction : Direction.Plane.HORIZONTAL) {
            VoxelShape[] variants = new VoxelShape[4];
            for (int variant = 0; variant < 4; variant++) {
                VoxelShape shape = Shapes.empty();
                for (var box : FurnitureGeometry.rotate(part.boxes((variant & 2) != 0, (variant & 1) != 0), geometryRotation(direction))) {
                    shape = Shapes.or(shape, Block.box(box.minX(), box.minY(), box.minZ(), box.maxX(), box.maxY(), box.maxZ()));
                }
                variants[variant] = shape.optimize();
            }
            shapes.put(direction, variants);
        }
    }

    public FurnitureDefinition definition() { return definition; }
    public int partIndex() { return partIndex; }
    public boolean isPrimary() { return partIndex == 0; }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        builder.add(FACING);
    }

    @Override
    public BlockState getStateForPlacement(BlockPlaceContext context) {
        Direction facing = context.getHorizontalDirection().getOpposite();
        if (definition.placement() == FurnitureDefinition.Placement.WALL) {
            if (!context.getClickedFace().getAxis().isHorizontal()) return null;
            facing = context.getClickedFace();
        } else if (definition.placement() == FurnitureDefinition.Placement.CEILING
                && context.getClickedFace() != Direction.DOWN) {
            return null;
        }
        return defaultBlockState().setValue(FACING, facing);
    }

    @Override
    protected VoxelShape getShape(BlockState state, BlockGetter level, BlockPos pos, CollisionContext context) {
        int variant = 0;
        if (state.hasProperty(ConnectingFurnitureBlock.LEFT)) {
            variant = (state.getValue(ConnectingFurnitureBlock.LEFT) ? 2 : 0)
                    | (state.getValue(ConnectingFurnitureBlock.RIGHT) ? 1 : 0);
        }
        return shapes.get(state.getValue(FACING))[variant];
    }

    @Override
    protected int getLightBlock(BlockState state) {
        // Shallow relief grooves do not turn a structural wall into a window.
        // Keep the actual outline/collision geometry and normal furniture light.
        return definition.structuralWall() ? 15 : super.getLightBlock(state);
    }

    @Override
    protected boolean propagatesSkylightDown(BlockState state) {
        return !definition.structuralWall() && super.propagatesSkylightDown(state);
    }

    @Override
    protected BlockState rotate(BlockState state, Rotation rotation) {
        return state.setValue(FACING, rotation.rotate(state.getValue(FACING)));
    }

    @Override
    protected BlockState mirror(BlockState state, Mirror mirror) {
        BlockState result = rotate(state, mirror.getRotation(state.getValue(FACING)));
        if (state.hasProperty(ConnectingFurnitureBlock.LEFT) && mirror != Mirror.NONE) {
            result = result.setValue(ConnectingFurnitureBlock.LEFT, state.getValue(ConnectingFurnitureBlock.RIGHT))
                    .setValue(ConnectingFurnitureBlock.RIGHT, state.getValue(ConnectingFurnitureBlock.LEFT));
        }
        return result;
    }

    @Override
    protected boolean canSurvive(BlockState state, LevelReader level, BlockPos pos) {
        return hasSupport(level, origin(pos, state.getValue(FACING)), state.getValue(FACING));
    }

    @Override
    protected void onPlace(BlockState state, Level level, BlockPos pos, BlockState oldState, boolean moving) {
        if (!level.isClientSide() && oldState.getBlock() != this) {
            // One event-triggered validation after all cells are present, also for /setblock.
            level.scheduleTick(pos, this, 1);
        }
    }

    @Override
    protected BlockState updateShape(BlockState state, LevelReader level, ScheduledTickAccess ticks,
                                     BlockPos pos, Direction direction, BlockPos neighborPos,
                                     BlockState neighborState, RandomSource random) {
        if (!level.isClientSide()) ticks.scheduleTick(pos, this, 1);
        return state;
    }

    @Override
    protected void tick(BlockState state, ServerLevel level, BlockPos pos, RandomSource random) {
        Direction facing = state.getValue(FACING);
        BlockPos origin = origin(pos, facing);
        if (!hasSupport(level, origin, facing) || !isComplete(level, origin, facing)) {
            collapse(level, origin, facing, true);
        }
    }

    @Override
    protected ItemStack getCloneItemStack(LevelReader level, BlockPos pos, BlockState state, boolean includeData) {
        return new ItemStack(ModBlocks.primaryItem(definition.id()));
    }

    public BlockPos origin(BlockPos cell, Direction facing) {
        GridOffset offset = FurnitureGeometry.rotate(definition.parts().get(partIndex).offset(), geometryRotation(facing));
        return cell.offset(-offset.x(), -offset.y(), -offset.z());
    }

    public BlockPos position(BlockPos origin, Direction facing, int index) {
        GridOffset offset = FurnitureGeometry.rotate(definition.parts().get(index).offset(), geometryRotation(facing));
        return origin.offset(offset.x(), offset.y(), offset.z());
    }

    public BlockState partState(int index, Direction facing) {
        return ModBlocks.getBlock(definition.parts().get(index).id()).defaultBlockState().setValue(FACING, facing);
    }

    public boolean hasSupport(LevelReader level, BlockPos origin, Direction facing) {
        BlockPos support;
        Direction supportFace;
        switch (definition.placement()) {
            case ANY -> { return true; }
            case FLOOR -> { support = origin.below(); supportFace = Direction.UP; }
            case WALL -> { support = origin.relative(facing.getOpposite()); supportFace = facing; }
            case CEILING -> {
                int top = definition.parts().stream().mapToInt(part -> part.offset().y()).max().orElse(0);
                support = origin.above(top + 1);
                supportFace = Direction.DOWN;
            }
            default -> throw new IllegalStateException("Unhandled placement kind");
        }
        // Do not force neighboring chunks to load just to validate a decoration.
        return !level.hasChunkAt(support) || level.getBlockState(support).isFaceSturdy(level, support, supportFace);
    }

    public boolean isComplete(LevelReader level, BlockPos origin, Direction facing) {
        for (int index = 0; index < definition.parts().size(); index++) {
            BlockPos target = position(origin, facing, index);
            if (level.hasChunkAt(target) && !matches(level.getBlockState(target), index, facing)) return false;
        }
        return true;
    }

    public boolean matches(BlockState state, int index, Direction facing) {
        return state.getBlock() == ModBlocks.getBlock(definition.parts().get(index).id()) && state.getValue(FACING) == facing;
    }

    /** Remove only our own cells. Primary loot is emitted once; secondary loot tables are empty. */
    public void collapse(Level level, BlockPos origin, Direction facing, boolean dropPrimary) {
        BlockPos primary = position(origin, facing, 0);
        if (level.hasChunkAt(primary) && matches(level.getBlockState(primary), 0, facing)) {
            if (dropPrimary) level.destroyBlock(primary, true);
            else level.setBlock(primary, Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL | Block.UPDATE_SUPPRESS_DROPS);
        }
        for (int index = 1; index < definition.parts().size(); index++) {
            BlockPos target = position(origin, facing, index);
            if (level.hasChunkAt(target) && matches(level.getBlockState(target), index, facing)) {
                level.setBlock(target, Blocks.AIR.defaultBlockState(), Block.UPDATE_ALL | Block.UPDATE_SUPPRESS_DROPS);
            }
        }
    }

    public static FurnitureGeometry.Rotation geometryRotation(Direction direction) {
        return switch (direction) {
            case NORTH -> FurnitureGeometry.Rotation.NORTH;
            case EAST -> FurnitureGeometry.Rotation.EAST;
            case SOUTH -> FurnitureGeometry.Rotation.SOUTH;
            case WEST -> FurnitureGeometry.Rotation.WEST;
            default -> throw new IllegalArgumentException("Furniture must face horizontally");
        };
    }
}
