package com.realistichomedecor.util;

import java.util.List;
import java.util.Objects;

/**
 * Coordinate transformations shared by furniture placement and collision shapes.
 * A north-facing model uses Minecraft's ordinary x=east, y=up, z=south axes.
 * East is a clockwise quarter turn, matching a block model's JSON {@code y: 90}.
 * Cell offsets rotate about the primary cell; local boxes rotate about (8, 8).
 */
public final class FurnitureGeometry {
    public static final double CELL_SIZE = 16.0;

    private FurnitureGeometry() {
    }

    public enum Rotation {
        NORTH, EAST, SOUTH, WEST
    }

    public record GridOffset(int x, int y, int z) {
    }

    /** A nonempty, finite box entirely inside its cell, in model pixel units. */
    public record Box(double minX, double minY, double minZ,
                      double maxX, double maxY, double maxZ) {
        public Box {
            if (!Double.isFinite(minX) || !Double.isFinite(minY) || !Double.isFinite(minZ)
                    || !Double.isFinite(maxX) || !Double.isFinite(maxY) || !Double.isFinite(maxZ)) {
                throw new IllegalArgumentException("Box coordinates must be finite");
            }
            if (minX < 0 || minY < 0 || minZ < 0
                    || maxX > CELL_SIZE || maxY > CELL_SIZE || maxZ > CELL_SIZE
                    || minX >= maxX || minY >= maxY || minZ >= maxZ) {
                throw new IllegalArgumentException("Box must have positive volume inside [0, 16]");
            }
        }
    }

    public static GridOffset rotate(GridOffset offset, Rotation rotation) {
        Objects.requireNonNull(offset, "offset");
        Objects.requireNonNull(rotation, "rotation");
        // Negating an arbitrary int must never silently wrap during placement.
        return switch (rotation) {
            case NORTH -> offset;
            case EAST -> new GridOffset(Math.negateExact(offset.z()), offset.y(), offset.x());
            case SOUTH -> new GridOffset(Math.negateExact(offset.x()), offset.y(), Math.negateExact(offset.z()));
            case WEST -> new GridOffset(offset.z(), offset.y(), Math.negateExact(offset.x()));
        };
    }

    public static Box rotate(Box box, Rotation rotation) {
        Objects.requireNonNull(box, "box");
        Objects.requireNonNull(rotation, "rotation");
        return switch (rotation) {
            case NORTH -> box;
            case EAST -> new Box(CELL_SIZE - box.maxZ(), box.minY(), box.minX(),
                    CELL_SIZE - box.minZ(), box.maxY(), box.maxX());
            case SOUTH -> new Box(CELL_SIZE - box.maxX(), box.minY(), CELL_SIZE - box.maxZ(),
                    CELL_SIZE - box.minX(), box.maxY(), CELL_SIZE - box.minZ());
            case WEST -> new Box(box.minZ(), box.minY(), CELL_SIZE - box.maxX(),
                    box.maxZ(), box.maxY(), CELL_SIZE - box.minX());
        };
    }

    /** Returns an immutable rotated copy; the source list is never modified. */
    public static List<Box> rotate(List<Box> boxes, Rotation rotation) {
        Objects.requireNonNull(boxes, "boxes");
        Objects.requireNonNull(rotation, "rotation");
        return boxes.stream().map(box -> rotate(box, rotation)).toList();
    }
}
