import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
export default defineConfig(function (_a) {
    var mode = _a.mode;
    var env = loadEnv(mode, process.cwd(), "");
    return {
        plugins: [react()],
        base: env.VITE_BASE_PATH || "/",
        server: {
            host: env.FRONTEND_HOST || "0.0.0.0",
            port: Number(env.FRONTEND_PORT || 5173),
        },
        preview: {
            host: env.FRONTEND_HOST || "0.0.0.0",
            port: Number(env.FRONTEND_PORT || 5173),
        },
        build: {
            sourcemap: mode !== "production",
            outDir: "dist",
        },
    };
});
