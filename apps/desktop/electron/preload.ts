/**
 * Electron preload (§4/§16/§18): compose the single `window.aisims` bridge — the per-launch token
 * (synchronous IPC, NOT process.argv — §16) as a closure-captured getter, ALONGSIDE the narrow
 * read-only FS probe (7.2c, window.aisims.fs). Both ride one exposeInMainWorld via the handoff
 * helper (contextBridge forbids exposing the same key twice).
 */
import { contextBridge, ipcRenderer } from "electron";

import { createFsBridge } from "./fs-bridge";
import { TOKEN_IPC_CHANNEL, createLoopbackTokenChannel, type TokenSource } from "./token-handoff";

const source: TokenSource = {
  getToken: () => {
    const token: unknown = ipcRenderer.sendSync(TOKEN_IPC_CHANNEL);
    return typeof token === "string" ? token : "";
  },
};

const fs = createFsBridge((channel, ...args) => ipcRenderer.sendSync(channel, ...args));

createLoopbackTokenChannel(source, contextBridge, { fs });
