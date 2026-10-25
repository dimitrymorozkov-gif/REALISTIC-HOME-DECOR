package com.realistichomedecor.block;

import net.fabricmc.fabric.api.event.lifecycle.v1.ServerChunkEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.chunk.LevelChunk;
import net.minecraft.world.level.chunk.LevelChunkSection;

/** Restores multiblock invariants at chunk boundaries without keeping chunks loaded. */
public final class FurnitureLifecycle {
    private FurnitureLifecycle() { }

    public static void register() {
        ServerChunkEvents.CHUNK_LOAD.register((level, chunk) -> {
            // Parts are at most eight cells from their origin. Revisit loaded neighbors
            // too: an empty newly loaded primary chunk can invalidate an old secondary.
            int chunkX = chunk.getPos().x;
            int chunkZ = chunk.getPos().z;
            for (int x = chunkX - 1; x <= chunkX + 1; x++) {
                for (int z = chunkZ - 1; z <= chunkZ + 1; z++) {
                    LevelChunk loaded = x == chunkX && z == chunkZ
                            ? chunk : level.getChunkSource().getChunkNow(x, z);
                    if (loaded != null) scheduleValidation(level, loaded);
                }
            }
        });
    }

    private static void scheduleValidation(ServerLevel level, LevelChunk chunk) {
        LevelChunkSection[] sections = chunk.getSections();
        int baseX = chunk.getPos().getMinBlockX();
        int baseZ = chunk.getPos().getMinBlockZ();
        for (int index = 0; index < sections.length; index++) {
            LevelChunkSection section = sections[index];
            // Most chunks need only a palette check; never scan ordinary terrain.
            if (section.hasOnlyAir() || !section.maybeHas(state -> state.getBlock() instanceof FurnitureBlock)) continue;
            int baseY = level.getSectionYFromSectionIndex(index) << 4;
            for (int y = 0; y < 16; y++) {
                for (int z = 0; z < 16; z++) {
                    for (int x = 0; x < 16; x++) {
                        if (section.getBlockState(x, y, z).getBlock() instanceof FurnitureBlock furniture) {
                            level.scheduleTick(new BlockPos(baseX + x, baseY + y, baseZ + z), furniture, 1);
                        }
                    }
                }
            }
        }
    }
}
