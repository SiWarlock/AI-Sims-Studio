/**
 * Renderer-side loopback token holder (§4/§16). The preload `contextBridge` exposes a getter under
 * TOKEN_BRIDGE_KEY; this reads it. The key + the bridge shape live here (the ipc layer) and the
 * preload helper re-exports them, so the dependency direction stays electron → ipc (never ipc →
 * electron).
 */

/** The global key the preload bridge exposes the token getter under. */
export const TOKEN_BRIDGE_KEY = "aisims";

/** The renderer-visible token bridge: a getter, never a plain property (no serialization leak). */
export interface TokenBridge {
  getToken(): string;
}

/**
 * Read the per-launch token from the bridged getter. Throws if the bridge is absent or yields an
 * empty token — a renderer must never issue an untokened request (forbidden pattern 3).
 */
export function readLoopbackToken(host?: Record<string, unknown>): string {
  const root = host ?? (globalThis as unknown as Record<string, unknown>);
  const bridge = root[TOKEN_BRIDGE_KEY] as TokenBridge | undefined;
  if (!bridge || typeof bridge.getToken !== "function") {
    throw new Error("Loopback token bridge missing on the renderer global (§16)");
  }
  const token = bridge.getToken();
  if (!token) {
    throw new Error("Loopback token bridge yielded an empty token (§16)");
  }
  return token;
}
