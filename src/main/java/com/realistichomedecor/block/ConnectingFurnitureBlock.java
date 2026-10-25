package com.realistichomedecor.block;

import com.realistichomedecor.catalog.FurnitureDefinition;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.util.RandomSource;
import net.minecraft.world.level.LevelReader;
import net.minecraft.world.level.ScheduledTickAccess;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.level.block.state.StateDefinition;
import net.minecraft.world.level.block.state.properties.BooleanProperty;

/** Side joins are ordinary saved block states, updated only when neighbors change. */
public final class ConnectingFurnitureBlock extends FurnitureBlock {
    public static final BooleanProperty LEFT = BooleanProperty.create("left");
    public static final BooleanProperty RIGHT = BooleanProperty.create("right");

    public ConnectingFurnitureBlock(Properties properties, FurnitureDefinition definition, int partIndex) {
        super(properties, definition, partIndex);
        registerDefaultState(defaultBlockState().setValue(LEFT, false).setValue(RIGHT, false));
    }

    @Override
    protected void createBlockStateDefinition(StateDefinition.Builder<Block, BlockState> builder) {
        super.createBlockStateDefinition(builder);
        builder.add(LEFT, RIGHT);
    }

    @Override
    protected BlockState updateShape(BlockState state, LevelReader level, ScheduledTickAccess ticks,
                                     BlockPos pos, Direction direction, BlockPos neighborPos,
                                     BlockState neighborState, RandomSource random) {
        super.updateShape(state, level, ticks, pos, direction, neighborPos, neighborState, random);
        return withConnections(state, level, pos);
    }

    public BlockState withConnections(BlockState state, LevelReader level, BlockPos pos) {
        Direction facing = state.getValue(FACING);
        return state.setValue(LEFT, connects(level.getBlockState(pos.relative(facing.getCounterClockWise())), facing))
                .setValue(RIGHT, connects(level.getBlockState(pos.relative(facing.getClockWise())), facing));
    }

    private boolean connects(BlockState neighbor, Direction facing) {
        return neighbor.is(this) && neighbor.getValue(FACING) == facing;
    }
}
