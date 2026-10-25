package com.realistichomedecor.registry;

import com.realistichomedecor.RealisticHomeDecor;
import com.realistichomedecor.catalog.FurnitureCatalog;
import net.fabricmc.fabric.api.itemgroup.v1.FabricItemGroup;
import net.minecraft.core.Registry;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

/** One tab per room or use, keeping all color variants next to their design. */
public final class ModItemGroups {
    private ModItemGroups() { }

    public static void register() {
        for (String category : FurnitureCatalog.CATEGORIES) {
            var definitions = ModBlocks.definitions().stream().filter(entry -> entry.category().equals(category)).toList();
            var key = ResourceKey.create(Registries.CREATIVE_MODE_TAB, RealisticHomeDecor.id(category));
            Registry.register(BuiltInRegistries.CREATIVE_MODE_TAB, key, FabricItemGroup.builder()
                    .title(Component.translatable("itemGroup.realistic_home_decor." + category))
                    .icon(() -> definitions.isEmpty() ? new ItemStack(Items.BRICKS)
                            : new ItemStack(ModBlocks.primaryItem(definitions.getFirst().id())))
                    .displayItems((parameters, output) -> definitions.forEach(entry -> output.accept(ModBlocks.primaryItem(entry.id()))))
                    .build());
        }
    }
}
