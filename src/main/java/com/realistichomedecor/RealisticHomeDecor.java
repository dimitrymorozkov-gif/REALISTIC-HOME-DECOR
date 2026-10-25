package com.realistichomedecor;

import com.realistichomedecor.registry.ModBlocks;
import com.realistichomedecor.block.FurnitureLifecycle;
import com.realistichomedecor.registry.ModItemGroups;
import net.fabricmc.api.ModInitializer;
import net.minecraft.resources.Identifier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public final class RealisticHomeDecor implements ModInitializer {
    public static final String MOD_ID = "realistic_home_decor";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    public static Identifier id(String path) {
        return Identifier.fromNamespaceAndPath(MOD_ID, path);
    }

    @Override
    public void onInitialize() {
        ModBlocks.register();
        ModItemGroups.register();
        FurnitureLifecycle.register();
        LOGGER.info("Realistic Home Decor: registered {} decorative items, {} static block cells and 11 creative tabs",
                ModBlocks.allItems().size(), ModBlocks.allBlocks().size());
    }
}
