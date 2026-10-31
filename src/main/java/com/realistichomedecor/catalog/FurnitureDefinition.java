package com.realistichomedecor.catalog;

import com.realistichomedecor.util.FurnitureGeometry.Box;
import com.realistichomedecor.util.FurnitureGeometry.GridOffset;

import java.util.List;
import java.util.Map;

/** Immutable, validated data shared by registration, placement and shape caches. */
public record FurnitureDefinition(String id, String template, String category,
                                  Placement placement, int luminance, boolean connect,
                                  String renderLayer, boolean structuralWall, List<Part> parts) {
    public FurnitureDefinition {
        parts = List.copyOf(parts);
    }

    public enum Placement { FLOOR, WALL, CEILING, ANY }

    public record Part(String id, GridOffset offset, List<Box> boxes,
                       Map<String, List<Box>> connectionBoxes) {
        public Part {
            boxes = List.copyOf(boxes);
            connectionBoxes = Map.copyOf(connectionBoxes);
        }

        public List<Box> boxes(boolean left, boolean right) {
            return connectionBoxes.getOrDefault(left + "_" + right, boxes);
        }
    }
}
