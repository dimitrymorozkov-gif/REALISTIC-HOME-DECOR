package com.realistichomedecor.item;

import com.realistichomedecor.block.ConnectingFurnitureBlock;
import com.realistichomedecor.block.FurnitureBlock;
import com.realistichomedecor.catalog.FurnitureDefinition;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.world.item.BlockItem;
import net.minecraft.world.item.context.BlockPlaceContext;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.shapes.CollisionContext;

import java.util.ArrayList;
import java.util.List;

/** Validates the entire footprint before changing any cell; vanilla handles sound and stack use. */
public final class FurnitureBlockItem extends BlockItem {
    private final FurnitureBlock furniture;

    public FurnitureBlockItem(FurnitureBlock block, Properties properties) {
        super(block, properties);
        this.furniture = block;
    }

    @Override
    public BlockPlaceContext updatePlacementContext(BlockPlaceContext context) {
        if (furniture.definition().placement() == FurnitureDefinition.Placement.CEILING) {
            if (context.getClickedFace() != Direction.DOWN) return null;
            int top = furniture.definition().parts().stream().mapToInt(part -> part.offset().y()).max().orElse(0);
            if (top != 0) {
                // The clicked cell is below the ceiling; the origin is the lowest cell.
                BlockPlaceContext shifted = BlockPlaceContext.at(context, context.getClickedPos().below(top), Direction.DOWN);
                // Preserve dispenser/test contexts as well as player-facing placement.
                return new BlockPlaceContext(shifted) {
                    @Override
                    public Direction getHorizontalDirection() {
                        return context.getHorizontalDirection();
                    }
                };
            }
        }
        return context;
    }

    @Override
    protected BlockState getPlacementState(BlockPlaceContext context) {
        BlockState state = super.getPlacementState(context);
        if (state == null || !canPlaceAssembly(context, state)) return null;
        if (furniture instanceof ConnectingFurnitureBlock connecting) {
            state = connecting.withConnections(state, context.getLevel(), context.getClickedPos());
        }
        return state;
    }

    private boolean canPlaceAssembly(BlockPlaceContext context, BlockState state) {
        Level level = context.getLevel();
        BlockPos origin = context.getClickedPos();
        Direction facing = state.getValue(FurnitureBlock.FACING);
        if (!furniture.hasSupport(level, origin, facing)) return false;
        CollisionContext collision = context.getPlayer() == null ? CollisionContext.empty() : CollisionContext.of(context.getPlayer());
        for (int index = 0; index < furniture.definition().parts().size(); index++) {
            BlockPos target = furniture.position(origin, facing, index);
            if (!level.isInWorldBounds(target) || !level.hasChunkAt(target)
                    || !level.getWorldBorder().isWithinBounds(target)
                    || !level.getBlockState(target).canBeReplaced()
                    || !level.isUnobstructed(furniture.partState(index, facing), target, collision)) return false;
            if (context.getPlayer() != null && !context.getPlayer().mayUseItemAt(target, context.getClickedFace(), context.getItemInHand())) {
                return false;
            }
        }
        return true;
    }

    @Override
    protected boolean placeBlock(BlockPlaceContext context, BlockState state) {
        // Recheck immediately before mutation, after other item-placement callbacks.
        if (!canPlaceAssembly(context, state)) return false;
        Level level = context.getLevel();
        BlockPos origin = context.getClickedPos();
        Direction facing = state.getValue(FurnitureBlock.FACING);
        List<BlockPos> positions = new ArrayList<>();
        List<BlockState> originals = new ArrayList<>();
        for (int index = 0; index < furniture.definition().parts().size(); index++) {
            BlockPos target = furniture.position(origin, facing, index);
            positions.add(target);
            originals.add(level.getBlockState(target));
            BlockState part = index == 0 ? state : furniture.partState(index, facing);
            // Defer shape propagation until the complete assembly has been written.
            if (!level.setBlock(target, part, Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE)) {
                for (int rollback = positions.size() - 1; rollback >= 0; rollback--) {
                    level.setBlock(positions.get(rollback), originals.get(rollback), Block.UPDATE_ALL | Block.UPDATE_SUPPRESS_DROPS);
                }
                return false;
            }
        }
        for (BlockPos target : positions) {
            BlockState current = level.getBlockState(target);
            current.updateNeighbourShapes(level, target, Block.UPDATE_ALL);
            level.updateNeighborsAt(target, current.getBlock(), null);
        }
        return true;
    }
}
