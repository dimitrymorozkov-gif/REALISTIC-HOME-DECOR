package com.realistichomedecor.clientmetrics;

import com.google.gson.JsonObject;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.client.Minecraft;
import org.lwjgl.opengl.GL11;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.Locale;

/** Development-only sampling of Minecraft's cached FPS counter and JVM heap. */
public final class ClientMetricsLogger implements ClientModInitializer {
    private static final Logger LOGGER = LoggerFactory.getLogger("rhd_client_metrics");
    private static final long SAMPLE_PERIOD_NANOS = 1_000_000_000L;
    private long lastSampleNanos;
    private boolean contextLogged;

    @Override
    public void onInitializeClient() {
        ClientTickEvents.END_CLIENT_TICK.register(this::sample);
    }

    private void sample(Minecraft client) {
        if (client.level == null) {
            contextLogged = false;
            return;
        }
        long now = System.nanoTime();
        if (!contextLogged) {
            logContext(client);
            lastSampleNanos = now;
            contextLogged = true;
            return;
        }
        if (now - lastSampleNanos < SAMPLE_PERIOD_NANOS) return;
        lastSampleNanos = now;
        Runtime runtime = Runtime.getRuntime();
        JsonObject sample = new JsonObject();
        sample.addProperty("epoch_ms", System.currentTimeMillis());
        sample.addProperty("monotonic_ns", now);
        sample.addProperty("fps", client.getFps());
        sample.addProperty("heap_used_bytes", runtime.totalMemory() - runtime.freeMemory());
        sample.addProperty("heap_committed_bytes", runtime.totalMemory());
        sample.addProperty("heap_max_bytes", runtime.maxMemory());
        LOGGER.info("RHD_METRIC_SAMPLE {}", sample);
    }

    private void logContext(Minecraft client) {
        JsonObject context = new JsonObject();
        context.addProperty("epoch_ms", System.currentTimeMillis());
        String renderer = GL11.glGetString(GL11.GL_RENDERER);
        context.addProperty("gpu_renderer", renderer);
        context.addProperty("gpu_vendor", GL11.glGetString(GL11.GL_VENDOR));
        context.addProperty("opengl_version", GL11.glGetString(GL11.GL_VERSION));
        String lowerRenderer = renderer == null ? "" : renderer.toLowerCase(Locale.ROOT);
        context.addProperty("software_renderer_detected", lowerRenderer.contains("llvmpipe")
                || lowerRenderer.contains("softpipe") || lowerRenderer.contains("swrast")
                || lowerRenderer.contains("software rasterizer") || lowerRenderer.contains("swiftshader"));
        context.addProperty("width_pixels", client.getWindow().getWidth());
        context.addProperty("height_pixels", client.getWindow().getHeight());
        context.addProperty("render_distance_chunks", client.options.renderDistance().get());
        context.addProperty("simulation_distance_chunks", client.options.simulationDistance().get());
        context.addProperty("fps_limit", client.options.framerateLimit().get());
        context.addProperty("vsync", client.options.enableVsync().get());
        context.addProperty("particles", client.options.particles().get().name());
        context.addProperty("gui_scale_option", client.options.guiScale().get());
        context.addProperty("fps_measurement", "Minecraft.getFps cached counter sampled at most once per second; not frame-time percentiles");
        LOGGER.info("RHD_METRIC_CONTEXT {}", context);
    }
}
