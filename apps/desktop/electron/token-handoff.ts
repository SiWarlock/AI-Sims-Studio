/**
 * Loopback-token handoff helper (§4/§16) — extracted from main/preload so it unit-tests without
 * spawning Electron. Exposes the per-launch token to the renderer over the trusted parent→child
 * `contextBridge` channel ONLY: a closure-captured getter (never an enumerable property → no
 * serialization leak), never on `window`/global, never logged.
 */
import { TOKEN_BRIDGE_KEY, type TokenBridge } from "../src/ipc/token";

export { TOKEN_BRIDGE_KEY };
export type { TokenBridge };

/**
 * The synchronous IPC channel the preload uses to fetch the per-launch token from main. The token
 * is served on demand (closure-held in main) — NEVER placed on the renderer's `process.argv`
 * (which is enumerable by other local processes — the §16 local-process attack we mitigate).
 */
export const TOKEN_IPC_CHANNEL = "aisims:get-loopback-token";

/** The token producer (the main process / sidecar handshake supplies the token). */
export interface TokenSource {
  getToken(): string;
}

/** The contextBridge surface used here (matches Electron's `contextBridge`). */
export interface TokenBridgeHost {
  exposeInMainWorld(key: string, api: TokenBridge): void;
}

export function createLoopbackTokenChannel(source: TokenSource, bridge: TokenBridgeHost): void {
  const token = source.getToken();
  // Closure-capture the token in a getter; the bridged object carries no plain token property.
  const api: TokenBridge = { getToken: () => token };
  bridge.exposeInMainWorld(TOKEN_BRIDGE_KEY, api);
}
