package com.realistichomedecor.catalog;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.realistichomedecor.util.FurnitureGeometry.Box;
import com.realistichomedecor.util.FurnitureGeometry.GridOffset;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

/** Reads our bundled development-generated catalog; never accepts runtime scripts. */
public final class FurnitureCatalog {
    public static final List<String> CATEGORIES = List.of("living_room", "kitchen", "bathroom",
            "bedroom", "office", "lighting", "architecture", "building_materials",
            "decorations", "outdoor", "garage");
    private static final String PATH = "/data/realistic_home_decor/catalog.json";

    private FurnitureCatalog() { }

    public static List<FurnitureDefinition> load() {
        try (InputStream stream = FurnitureCatalog.class.getResourceAsStream(PATH)) {
            if (stream == null) throw new IllegalStateException("Missing furniture catalog: " + PATH);
            JsonObject root = JsonParser.parseReader(new InputStreamReader(stream, StandardCharsets.UTF_8))
                    .getAsJsonObject();
            if (root.get("schema_version").getAsInt() != 1) {
                throw new IllegalArgumentException("Unsupported furniture catalog schema");
            }
            List<FurnitureDefinition> definitions = new ArrayList<>();
            Set<String> ids = new HashSet<>();
            for (JsonElement element : root.getAsJsonArray("entries")) {
                JsonObject entry = element.getAsJsonObject();
                String id = identifier(entry.get("id").getAsString());
                String category = entry.get("category").getAsString();
                if (!CATEGORIES.contains(category)) throw new IllegalArgumentException("Unknown category: " + category);
                FurnitureDefinition.Placement placement = FurnitureDefinition.Placement.valueOf(
                        entry.get("placement").getAsString().toUpperCase(Locale.ROOT));
                int luminance = entry.has("luminance") ? entry.get("luminance").getAsInt() : 0;
                if (luminance < 0 || luminance > 15) throw new IllegalArgumentException("Invalid light level: " + id);
                boolean connect = entry.has("connect") && entry.get("connect").getAsBoolean();
                String renderLayer = entry.has("render_layer") ? entry.get("render_layer").getAsString() : "solid";
                if (!Set.of("solid", "cutout", "translucent").contains(renderLayer)) {
                    throw new IllegalArgumentException("Invalid render layer: " + id);
                }
                // Structural wall metadata is explicit; wall clocks, shelves and
                // other decorative wall_* IDs must keep their ordinary lighting.
                boolean structuralWall = entry.has("wall_family");
                if (structuralWall && (!entry.get("wall_family").isJsonPrimitive()
                        || entry.get("wall_family").getAsString().isBlank()
                        || !category.equals("building_materials") || !renderLayer.equals("solid"))) {
                    throw new IllegalArgumentException("Invalid structural wall metadata: " + id);
                }
                List<FurnitureDefinition.Part> parts = new ArrayList<>();
                Set<GridOffset> positions = new HashSet<>();
                for (JsonElement partElement : entry.getAsJsonArray("parts")) {
                    JsonObject part = partElement.getAsJsonObject();
                    String partId = identifier(part.get("id").getAsString());
                    if (!ids.add(partId)) throw new IllegalArgumentException("Duplicate block identifier: " + partId);
                    JsonArray offset = part.getAsJsonArray("offset");
                    if (offset.size() != 3) throw new IllegalArgumentException("Invalid offset: " + partId);
                    GridOffset position = new GridOffset(offset.get(0).getAsInt(), offset.get(1).getAsInt(), offset.get(2).getAsInt());
                    if (position.x() < 0 || position.y() < 0 || position.z() < 0
                            || position.x() > 7 || position.y() > 7 || position.z() > 7 || !positions.add(position)) {
                        throw new IllegalArgumentException("Invalid or duplicate cell: " + partId);
                    }
                    Map<String, List<Box>> connectionBoxes = new HashMap<>();
                    if (part.has("connection_boxes")) {
                        for (var variant : part.getAsJsonObject("connection_boxes").entrySet()) {
                            if (!Set.of("false_false", "false_true", "true_false", "true_true").contains(variant.getKey())) {
                                throw new IllegalArgumentException("Invalid connection shape key: " + partId);
                            }
                            connectionBoxes.put(variant.getKey(), boxes(variant.getValue().getAsJsonArray()));
                        }
                    }
                    parts.add(new FurnitureDefinition.Part(partId, position, boxes(part.getAsJsonArray("boxes")), connectionBoxes));
                }
                if (parts.isEmpty() || !parts.getFirst().id().equals(id)
                        || !parts.getFirst().offset().equals(new GridOffset(0, 0, 0))) {
                    throw new IllegalArgumentException("Primary furniture part must be first, at the origin: " + id);
                }
                if (connect && parts.size() != 1) throw new IllegalArgumentException("Connecting furniture must occupy one cell: " + id);
                definitions.add(new FurnitureDefinition(id, entry.get("template").getAsString(), category,
                        placement, luminance, connect, renderLayer, structuralWall, parts));
            }
            if (definitions.isEmpty()) throw new IllegalArgumentException("The furniture catalog is empty");
            return List.copyOf(definitions);
        } catch (Exception failure) {
            throw new IllegalStateException("Unable to load bundled Realistic Home Decor furniture catalog", failure);
        }
    }

    private static List<Box> boxes(JsonArray array) {
        List<Box> result = new ArrayList<>();
        for (JsonElement element : array) {
            JsonArray coordinates = element.getAsJsonArray();
            if (coordinates.size() != 6) throw new IllegalArgumentException("A collision box requires six coordinates");
            result.add(new Box(coordinates.get(0).getAsDouble(), coordinates.get(1).getAsDouble(), coordinates.get(2).getAsDouble(),
                    coordinates.get(3).getAsDouble(), coordinates.get(4).getAsDouble(), coordinates.get(5).getAsDouble()));
        }
        return List.copyOf(result);
    }

    private static String identifier(String value) {
        if (!value.matches("[a-z0-9][a-z0-9_]*")) throw new IllegalArgumentException("Invalid furniture identifier: " + value);
        return value;
    }
}
