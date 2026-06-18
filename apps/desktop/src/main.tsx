/**
 * React renderer entry (§3) — the Vite build target that replaces 7.1's static placeholder. Mounts
 * the React root and boots the 7.1 thin observer exactly once (startRenderer). The observer reads
 * the bridged loopback token; before the sidecar handshake (later slice) there is none, so the
 * onboarding screen renders without a live client.
 */
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import type { IpcClient } from "./ipc/client";
import { resolveFsProbe } from "./onboarding/renderer-fs";
import { startRenderer } from "./renderer-entry";
import { App } from "./surfaces/onboarding/App";

const fs = resolveFsProbe();

let client: IpcClient | null = null;
try {
  client = startRenderer().client;
} catch {
  // No loopback token yet (pre-handshake) — onboarding renders without a live client.
}

const container = document.getElementById("root");
if (container) {
  createRoot(container).render(
    <StrictMode>
      <App client={client} fs={fs} />
    </StrictMode>,
  );
}
