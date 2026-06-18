import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";

/**
 * Dev/HMR needs a relaxed connect-src (ws:) + inline scripts that the tight 7.1 prod CSP forbids
 * (Q4). `apply: "serve"` scopes this to `vite dev` ONLY — the BUILD output keeps index.html's tight
 * prod CSP, so the relaxed policy is never shipped.
 */
function devCspRelaxation(): Plugin {
  return {
    name: "aisims:dev-csp-relaxation",
    apply: "serve",
    transformIndexHtml(html: string): string {
      return html.replace(
        /<meta\s+http-equiv="Content-Security-Policy"[\s\S]*?\/>/,
        `<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src http://127.0.0.1:* ws://127.0.0.1:* ws://localhost:*; object-src 'none'; base-uri 'none'" />`,
      );
    },
  };
}

// The Electron shell loads the built renderer over file://, so assets must be relative-pathed.
// Output → dist/renderer; electron/main.ts loads dist/renderer/index.html in production and the
// dev-server URL (VITE_DEV_SERVER_URL) during `vite dev`.
export default defineConfig({
  base: "./",
  plugins: [react(), devCspRelaxation()],
  build: {
    outDir: "dist/renderer",
    emptyOutDir: true,
  },
});
