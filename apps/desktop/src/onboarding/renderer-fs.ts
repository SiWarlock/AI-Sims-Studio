/**
 * Resolve a renderer-side FsProbe. The preload may expose a node:fs-backed probe under
 * `window.aisims.fs` (that bridge lands in a later slice — see Step-9 Future TODO). Until then this
 * returns a safe default: nothing detected, every path blocks — so onboarding degrades to "set your
 * Mods path manually" rather than crashing.
 */
import type { FsProbe } from "./fs-probe";

interface FsBridgeGlobal {
  aisims?: { fs?: unknown };
}

const NOT_AVAILABLE: FsProbe = {
  exists: () => false,
  isDirectory: () => false,
  isWritable: () => false,
  homeDir: () => "",
};

// `window.aisims` must only ever be populated by the preload over the contextIsolation boundary; a
// loaded page cannot reach it. Still, validate the shape before trusting it (defense in depth).
function isFsProbe(value: unknown): value is FsProbe {
  if (typeof value !== "object" || value === null) return false;
  const candidate = value as Record<string, unknown>;
  return (
    typeof candidate.exists === "function" &&
    typeof candidate.isDirectory === "function" &&
    typeof candidate.isWritable === "function" &&
    typeof candidate.homeDir === "function"
  );
}

export function resolveFsProbe(): FsProbe {
  const bridged = (globalThis as FsBridgeGlobal).aisims?.fs;
  return isFsProbe(bridged) ? bridged : NOT_AVAILABLE;
}
