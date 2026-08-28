/**
 * The renderer's thin-observer bootstrap (§3). `main.tsx` (the React root) calls `startRenderer()`
 * exactly once after mounting; there is no import side-effect (the 7.1 DOMContentLoaded auto-run was
 * removed so the React entry owns the single bootstrap — no double-boot). This is the production
 * call path `/wired bootstrapObserver` traces.
 *
 * No project context exists at first run (project creation is 7.3), so the observer starts idle (no
 * SSE open until a projectId is available). The sidecar base URL is a placeholder until the sidecar
 * handshake lands (later slice).
 */
import { bootstrapObserver, type BootstrapOptions, type ObserverHandle } from "./bootstrap";
import { readLoopbackToken } from "./ipc/token";

// Replaced by the sidecar-negotiated loopback URL once the handshake lands.
const SIDECAR_BASE_URL = "http://127.0.0.1:0";

export interface StartRendererOptions {
  token?: string;
  baseUrl?: string;
  projectId?: string;
  fetchImpl?: typeof fetch;
  maxReconnects?: number;
}

export function startRenderer(opts: StartRendererOptions = {}): ObserverHandle {
  const token = opts.token ?? readLoopbackToken();
  const baseUrl = opts.baseUrl ?? SIDECAR_BASE_URL;
  const bootstrapOpts: BootstrapOptions = {
    ...(opts.projectId !== undefined ? { projectId: opts.projectId } : {}),
    ...(opts.fetchImpl ? { fetchImpl: opts.fetchImpl } : {}),
    ...(opts.maxReconnects !== undefined ? { maxReconnects: opts.maxReconnects } : {}),
  };
  return bootstrapObserver(token, baseUrl, bootstrapOpts);
}
