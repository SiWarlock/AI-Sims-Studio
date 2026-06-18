/**
 * Electron main (§3/§4/§16): on app-ready, obtain the per-launch loopback token, register a
 * synchronous IPC channel that serves it to the preload on demand (the token is closure-held here
 * and NEVER placed on the renderer's process.argv), create the BrowserWindow with the token-
 * bridging preload (contextIsolation on, nodeIntegration off, sandbox on), deny window-open +
 * navigation (a thin observer never navigates), and load the static placeholder renderer.
 *
 * 7.1 mints a placeholder token here so the handoff path is exercised end-to-end. In production the
 * SIDECAR mints the token and hands it to main over the parent→child channel (§16); that swap lands
 * with the sidecar boot/onboarding handshake (7.2), which must preserve this no-argv posture. The
 * renderer build (Vite) lands in 7.3 (Q2).
 */
import { randomBytes } from "node:crypto";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { BrowserWindow, app, ipcMain } from "electron";

import { TOKEN_IPC_CHANNEL } from "./token-handoff";

const moduleDir = dirname(fileURLToPath(import.meta.url));

function mintLoopbackToken(): string {
  return randomBytes(32).toString("hex");
}

async function createWindow(): Promise<void> {
  const win = new BrowserWindow({
    width: 1280,
    height: 800,
    show: true,
    webPreferences: {
      preload: join(moduleDir, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });
  // A thin observer never navigates or opens windows — deny both (Electron hardening).
  win.webContents.setWindowOpenHandler(() => ({ action: "deny" }));
  win.webContents.on("will-navigate", (event) => event.preventDefault());
  // Dev: load the Vite dev server (HMR, dev-only relaxed CSP). Prod: load the built renderer
  // (dist/renderer/index.html — the tight prod CSP). The packaged layout is finalized at packaging.
  const devServerUrl = process.env.VITE_DEV_SERVER_URL;
  if (devServerUrl) {
    await win.loadURL(devServerUrl);
  } else {
    await win.loadFile(join(moduleDir, "..", "renderer", "index.html"));
  }
}

app.whenReady().then(
  async () => {
    const token = mintLoopbackToken();
    // Serve the token synchronously on demand; it never touches argv or any log sink.
    ipcMain.on(TOKEN_IPC_CHANNEL, (event) => {
      event.returnValue = token;
    });
    await createWindow();
    app.on("activate", () => {
      if (BrowserWindow.getAllWindows().length === 0) void createWindow().catch(() => undefined);
    });
  },
  () => undefined,
);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
