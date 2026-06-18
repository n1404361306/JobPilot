import { fileURLToPath, URL } from "node:url";
import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

function mdCharsetPlugin() {
  const middleware = (
    req: { url?: string },
    res: { setHeader: (name: string, value: string) => void },
    next: () => void
  ) => {
    const path = req.url?.split("?")[0] ?? "";
    if (path.endsWith(".md")) {
      res.setHeader("Content-Type", "text/plain; charset=utf-8");
    }
    next();
  };

  return {
    name: "md-charset",
    configureServer(server: { middlewares: { use: (fn: typeof middleware) => void } }) {
      server.middlewares.use(middleware);
    },
    configurePreviewServer(server: { middlewares: { use: (fn: typeof middleware) => void } }) {
      server.middlewares.use(middleware);
    }
  };
}

export default defineConfig({
  plugins: [vue(), mdCharsetPlugin()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url))
    }
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
    allowedHosts: true,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true
      }
    }
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./vitest.setup.ts"],
    globals: true
  }
} as any);
