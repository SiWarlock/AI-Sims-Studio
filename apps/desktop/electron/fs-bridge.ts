/**
 * The renderer↔main FS-probe bridge (§18/§3). The main process performs four READ-ONLY filesystem
 * probes (exists / isDirectory / isWritable[W_OK] / homeDir) over injected node:fs/os; the preload
 * exposes them under window.aisims.fs via a single synchronous channel. NARROW SURFACE: exactly the
 * four probes — no raw fs handle, no content read, no write, no arbitrary method. `isWritable` is a
 * non-destructive W_OK access check (never a temp write).
 *
 * `import type { IpcMain }` is runtime-erased, so the pure logic (fsProbeHandlers / dispatchFsProbe /
 * createFsBridge) unit-tests with no electron runtime dependency; `registerFsBridge` is wiring,
 * exercised from main.ts (reachability), not unit-tested.
 */
import type { IpcMain } from "electron";

import type { FsProbe } from "../src/onboarding/fs-probe";

/** The narrow node:fs subset the probes need (injected for testability). */
export interface FsModule {
  existsSync(path: string): boolean;
  statSync(path: string): { isDirectory(): boolean };
  accessSync(path: string, mode: number): void;
  constants: { W_OK: number };
}

/** The narrow node:os subset the probes need. */
export interface OsModule {
  homedir(): string;
}

/** The single synchronous IPC channel the FS bridge uses. */
export const FS_PROBE_CHANNEL = "aisims:fs-probe";

/** The four read-only probes over injected node:fs/os. Never reads content, never writes. An empty
 *  path is never a meaningful probe → it deterministically reports false (avoids existsSync("")
 *  resolving against the cwd on some platforms). */
export function fsProbeHandlers(fs: FsModule, os: OsModule): FsProbe {
  return {
    exists: (path) => path.length > 0 && fs.existsSync(path),
    isDirectory: (path) => {
      if (path.length === 0) return false;
      try {
        return fs.statSync(path).isDirectory();
      } catch {
        return false;
      }
    },
    isWritable: (path) => {
      if (path.length === 0) return false;
      try {
        fs.accessSync(path, fs.constants.W_OK); // W_OK access check — never a temp write
        return true;
      } catch {
        return false;
      }
    },
    homeDir: () => os.homedir(),
  };
}

/**
 * A trusted IPC sender is the renderer's TOP frame (no parent) — rejects sub-frames/iframes that
 * could otherwise use the channel as a filesystem-existence oracle. (Defense-in-depth: navigation
 * is already denied and no remote content loads today; this hardens the narrow boundary for when
 * the real renderer / any embedded frame lands.)
 */
export function isTopFrameSender(senderFrame: { parent: unknown } | null | undefined): boolean {
  return senderFrame != null && senderFrame.parent == null;
}

/**
 * Pure channel dispatch: map a method name to its probe result, rejecting anything off the
 * allowlist with `null` and running NO fs op. This is the RUNTIME narrow-surface guarantee — a
 * non-cooperating caller that sendSyncs an arbitrary method string cannot reach a non-probe op.
 */
export function dispatchFsProbe(
  logic: FsProbe,
  method: string,
  path: string,
): boolean | string | null {
  switch (method) {
    case "exists":
      return logic.exists(path);
    case "isDirectory":
      return logic.isDirectory(path);
    case "isWritable":
      return logic.isWritable(path);
    case "homeDir":
      return logic.homeDir();
    default:
      return null;
  }
}

/** Register the main-process sync handler for the FS-probe channel (wiring; called from main.ts). */
export function registerFsBridge(ipcMain: IpcMain, fs: FsModule, os: OsModule): void {
  const logic = fsProbeHandlers(fs, os);
  ipcMain.on(FS_PROBE_CHANNEL, (event, method: unknown, path: unknown) => {
    if (!isTopFrameSender(event.senderFrame)) {
      event.returnValue = null;
      return;
    }
    event.returnValue = dispatchFsProbe(logic, String(method), String(path ?? ""));
  });
}

/** Renderer-side bridge: the four sync probes over the injected sendSync. */
export function createFsBridge(
  sendSync: (channel: string, ...args: unknown[]) => unknown,
): FsProbe {
  return {
    exists: (path) => Boolean(sendSync(FS_PROBE_CHANNEL, "exists", path)),
    isDirectory: (path) => Boolean(sendSync(FS_PROBE_CHANNEL, "isDirectory", path)),
    isWritable: (path) => Boolean(sendSync(FS_PROBE_CHANNEL, "isWritable", path)),
    homeDir: () => String(sendSync(FS_PROBE_CHANNEL, "homeDir") ?? ""),
  };
}
