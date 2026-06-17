/**
 * The loaded renderer's entry (§3). index.html loads this; it reads the bridged loopback token and
 * starts the thin observer. This is the production call path `/wired bootstrapObserver` traces.
 *
 * No project context exists at first run (onboarding/project creation are 7.2/7.3), so the observer
 * starts idle (no SSE open until a projectId is available). The sidecar base URL is a placeholder
 * until the sidecar handshake lands (7.2). The TS→JS build (Vite) is wired in 7.3 (Q2 defers it).
 */
import { bootstrapObserver, type ObserverHandle } from "./bootstrap";
import { readLoopbackToken } from "./ipc/token";

// Replaced by the sidecar-negotiated loopback URL once the handshake lands (7.2).
const SIDECAR_BASE_URL = "http://127.0.0.1:0";

export function startRenderer(): ObserverHandle {
  const token = readLoopbackToken();
  return bootstrapObserver(token, SIDECAR_BASE_URL);
}

interface DomLike {
  addEventListener(type: string, listener: () => void): void;
}

const host = globalThis as { document?: DomLike };
if (host.document) {
  host.document.addEventListener("DOMContentLoaded", () => {
    try {
      startRenderer();
    } catch {
      // Missing token/bridge surfaces as the onboarding readiness gate (7.2); not fatal here.
    }
  });
}
