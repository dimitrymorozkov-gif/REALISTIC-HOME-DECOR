package com.realistichomedecor.registry;

import com.realistichomedecor.RealisticHomeDecor;
import com.realistichomedecor.block.ConnectingFurnitureBlock;
import com.realistichomedecor.block.FurnitureBlock;
import com.realistichomedecor.catalog.FurnitureCatalog;
import com.realistichomedecor.catalog.FurnitureDefinition;
import com.realistichomedecor.item.FurnitureBlockItem;
import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.Item;
import net.minecraft.world.level.block.SoundType;
import net.minecraft.world.level.block.state.BlockBehaviour;
import net.minecraft.world.level.material.PushReaction;

import java.util.Collection;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class ModBlocks {
    private static final Map<String, FurnitureBlock> BLOCKS = new LinkedHashMap<>();
    private static final Map<String, Item> ITEMS = new LinkedHashMap<>();
    private static List<FurnitureDefinition> definitions = List.of();

    private ModBlocks() { }

    public static void register() {
        if (!BLOCKS.isEmpty()) throw new IllegalStateException("Furniture was already registered");
        definitions = FurnitureCatalog.load();
        for (FurnitureDefinition definition : definitions) {
            for (int index = 0; index < definition.parts().size(); index++) {
                String id = definition.parts().get(index).id();
                BlockBehaviour.Properties properties = BlockBehaviour.Properties.of()
                        .setId(ResourceKey.create(Registries.BLOCK, RealisticHomeDecor.id(id)))
                        .strength(1.5F, 3.0F)
                        .sound(SoundType.WOOD)
                        .lightLevel(state -> definition.luminance())
                        .isRedstoneConductor((state, level, pos) -> false)
                        .pushReaction(PushReaction.BLOCK);
                var boxes = definition.parts().get(index).boxes();
                boolean fullOpaqueCube = definition.renderLayer().equals("solid") && boxes.size() == 1
                        && boxes.getFirst().minX() == 0 && boxes.getFirst().minY() == 0 && boxes.getFirst().minZ() == 0
                        && boxes.getFirst().maxX() == 16 && boxes.getFirst().maxY() == 16 && boxes.getFirst().maxZ() == 16;
                if (!fullOpaqueCube) properties.noOcclusion();
                if (index != 0) properties.noLootTable();
                FurnitureBlock block = definition.connect()
                        ? new ConnectingFurnitureBlock(properties, definition, index)
                        : new FurnitureBlock(properties, definition, index);
                Registry.register(BuiltInRegistries.BLOCK, RealisticHomeDecor.id(id), block);
                BLOCKS.put(id, block);
            }
        }
        for (FurnitureDefinition definition : definitions) {
            Item item = new FurnitureBlockItem(getBlock(definition.id()), new Item.Properties()
                    .setId(ResourceKey.create(Registries.ITEM, RealisticHomeDecor.id(definition.id())))
                    .useBlockDescriptionPrefix());
            Registry.register(BuiltInRegistries.ITEM, RealisticHomeDecor.id(definition.id()), item);
            ITEMS.put(definition.id(), item);
        }
        // AFTER respects protection mods that cancel BEFORE, and never mutates a canceled break.
        PlayerBlockBreakEvents.AFTER.register((level, player, pos, state, blockEntity) -> {
            if (state.getBlock() instanceof FurnitureBlock furniture) {
                var facing = state.getValue(FurnitureBlock.FACING);
                var origin = furniture.origin(pos, facing);
                if (!furniture.isPrimary()) {
                    var primary = level.getBlockState(origin);
                    if (furniture.matches(primary, 0, facing)) {
                        level.destroyBlock(origin, !player.isCreative(), player);
                    }
                }
                furniture.collapse(level, origin, facing, false);
            }
        });
    }

    public static FurnitureBlock getBlock(String id) {
        FurnitureBlock block = BLOCKS.get(id);
        if (block == null) throw new IllegalArgumentException("Unknown furniture part: " + id);
        return block;
    }

    public static Item primaryItem(String id) {
        Item item = ITEMS.get(id);
        if (item == null) throw new IllegalArgumentException("Unknown furniture item: " + id);
        return item;
    }

    public static Collection<FurnitureBlock> allBlocks() { return Collections.unmodifiableCollection(BLOCKS.values()); }
    public static Map<String, Item> allItems() { return Collections.unmodifiableMap(ITEMS); }
    public static List<FurnitureDefinition> definitions() { return definitions; }
}
