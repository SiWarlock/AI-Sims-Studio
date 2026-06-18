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
import { accessSync, constants, existsSync, statSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { Entry } from "@napi-rs/keyring";
import { BrowserWindow, app, ipcMain } from "electron";

import { isTopFrameSender, registerFsBridge } from "./fs-bridge";
import { KeychainWriter, type KeychainEntryFactory } from "./keychain";
import { registerKeychainBridge } from "./keychain-bridge";
import { TOKEN_IPC_CHANNEL } from "./token-handoff";

const moduleDir = dirname(fileURLToPath(import.meta.url));

/** Prod keyring factory over @napi-rs/keyring (interop + behavior proven by spike 7.2b-0). The
 *  synchronous Entry returns sentinels for an absent entry — `getPassword(): string | null` (null
 *  when absent) and `deletePassword(): boolean` (false when absent) — neither throws on not-found,
 *  so the KeychainWriter's has/delete semantics hold directly. A real keychain failure (locked)
 *  throws and propagates → KeychainUnavailableError in the writer. */
const napiKeychainEntryFactory: KeychainEntryFactory = (service, account) => {
  const entry = new Entry(service, account);
  return {
    setPassword: (password) => entry.setPassword(password),
    getPassword: () => entry.getPassword(),
    deletePassword: () => {
      entry.deletePassword(); // boolean (false when absent) — ignored; no-op on not-found
    },
  };
};

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
    // Serve the token synchronously on demand to the renderer's top frame only; it never touches
    // argv or any log sink.
    ipcMain.on(TOKEN_IPC_CHANNEL, (event) => {
      event.returnValue = isTopFrameSender(event.senderFrame) ? token : null;
    });
    // Register the narrow read-only FS-probe handlers (7.2c) so onboarding detection is live.
    registerFsBridge(
      ipcMain,
      {
        existsSync: (p) => existsSync(p),
        statSync: (p) => statSync(p),
        accessSync: (p, m) => accessSync(p, m),
        constants,
      },
      { homedir },
    );
    // Register the write-only keychain bridge (7.2b-1) over the real @napi-rs/keyring.
    registerKeychainBridge(ipcMain, new KeychainWriter(napiKeychainEntryFactory));
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
