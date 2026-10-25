package com.realistichomedecor.client;

import com.realistichomedecor.registry.ModBlocks;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.rendering.v1.BlockRenderLayerMap;
import net.minecraft.client.renderer.chunk.ChunkSectionLayer;

/** Only the client loads rendering classes; dedicated servers use common code. */
public final class RealisticHomeDecorClient implements ClientModInitializer {
    @Override
    public void onInitializeClient() {
        for (var block : ModBlocks.allBlocks()) {
            switch (block.definition().renderLayer()) {
                case "cutout" -> BlockRenderLayerMap.putBlock(block, ChunkSectionLayer.CUTOUT);
                case "translucent" -> BlockRenderLayerMap.putBlock(block, ChunkSectionLayer.TRANSLUCENT);
                default -> { }
            }
        }
    }
}
