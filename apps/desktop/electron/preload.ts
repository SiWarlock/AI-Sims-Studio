/**
 * Electron preload (§4/§16): bridge the per-launch loopback token into the renderer over the
 * trusted parent→child channel. The token is fetched from main via a synchronous IPC call (NOT via
 * process.argv — argv is enumerable by other local processes, the §16 attack we mitigate) and
 * exposed to the renderer as a closure-captured getter only.
 */
import { contextBridge, ipcRenderer } from "electron";

import { TOKEN_IPC_CHANNEL, createLoopbackTokenChannel, type TokenSource } from "./token-handoff";

const source: TokenSource = {
  getToken: () => {
    const token: unknown = ipcRenderer.sendSync(TOKEN_IPC_CHANNEL);
    return typeof token === "string" ? token : "";
  },
};

createLoopbackTokenChannel(source, contextBridge);
