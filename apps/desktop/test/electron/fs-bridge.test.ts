import {
  accessSync,
  constants,
  existsSync,
  mkdtempSync,
  readdirSync,
  rmSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { homedir, tmpdir } from "node:os";
import { join } from "node:path";

import { afterAll, beforeAll, describe, expect, it } from "vitest";

import {
  createFsBridge,
  dispatchFsProbe,
  fsProbeHandlers,
  isTopFrameSender,
  type FsModule,
} from "../../electron/fs-bridge";
import { createLoopbackTokenChannel } from "../../electron/token-handoff";

const FOUR_METHODS = ["exists", "homeDir", "isDirectory", "isWritable"];

const fsModule: FsModule = { existsSync, statSync, accessSync, constants };
const osModule = { homedir };

describe("FS-probe bridge — narrow read-only main-process probes (§18/§3)", () => {
  let tempDir: string;
  let tempFile: string;

  beforeAll(() => {
    tempDir = mkdtempSync(join(tmpdir(), "aisims-fs-"));
    tempFile = join(tempDir, "a-file.txt");
    writeFileSync(tempFile, "x");
  });
  afterAll(() => {
    rmSync(tempDir, { recursive: true, force: true });
  });

  it("test_fs_probe_handlers_report_correctly — spec(§18)", () => {
    const probes = fsProbeHandlers(fsModule, osModule);
    expect(probes.exists(tempDir)).toBe(true);
    expect(probes.exists(join(tempDir, "missing"))).toBe(false);
    expect(probes.isDirectory(tempDir)).toBe(true);
    expect(probes.isDirectory(tempFile)).toBe(false);
    expect(probes.isWritable(tempDir)).toBe(true);
    expect(probes.isWritable(join(tempDir, "missing"))).toBe(false);
    expect(probes.homeDir()).toBe(homedir());
    // An empty path is never a meaningful probe → deterministically false (no cwd resolution).
    expect(probes.exists("")).toBe(false);
    expect(probes.isDirectory("")).toBe(false);
    expect(probes.isWritable("")).toBe(false);
  });

  it("test_ipc_sender_must_be_top_frame — spec(§16) frame-origin gate", () => {
    expect(isTopFrameSender({ parent: null })).toBe(true); // renderer top frame
    expect(isTopFrameSender({ parent: {} })).toBe(false); // a sub-frame / iframe
    expect(isTopFrameSender(null)).toBe(false);
    expect(isTopFrameSender(undefined)).toBe(false);
  });

  it("test_is_writable_is_non_destructive — read-only posture", () => {
    const before = readdirSync(tempDir).sort();
    fsProbeHandlers(fsModule, osModule).isWritable(tempDir);
    const after = readdirSync(tempDir).sort();
    expect(after).toEqual(before); // never wrote/removed a probe file
  });

  it("test_bridge_surface_is_exactly_four_readonly_methods — spec(§3) narrow surface", () => {
    expect(Object.keys(fsProbeHandlers(fsModule, osModule)).sort()).toEqual(FOUR_METHODS);
    // The renderer-side bridge exposes the same exactly-four surface (no raw fs / content / channel).
    expect(Object.keys(createFsBridge(() => null)).sort()).toEqual(FOUR_METHODS);
  });

  it("test_fs_probe_channel_rejects_non_allowlisted_method — spec(§3) runtime narrow-surface", () => {
    const calls: string[] = [];
    const spyLogic = {
      exists: () => {
        calls.push("exists");
        return true;
      },
      isDirectory: () => {
        calls.push("isDirectory");
        return true;
      },
      isWritable: () => {
        calls.push("isWritable");
        return true;
      },
      homeDir: () => {
        calls.push("homeDir");
        return "/h";
      },
    };
    // A non-cooperating caller can sendSync an arbitrary method string on the channel; the dispatch
    // must reject anything off the 4-method allowlist with null AND run no fs op.
    for (const bad of ["readFile", "writeFile", "unlink", "rename", "stat", ""]) {
      expect(dispatchFsProbe(spyLogic, bad, "/x")).toBeNull();
    }
    expect(calls).toEqual([]);
    // The allowlisted methods still dispatch.
    expect(dispatchFsProbe(spyLogic, "exists", "/x")).toBe(true);
    expect(dispatchFsProbe(spyLogic, "homeDir", "")).toBe("/h");
  });

  it("test_preload_exposes_fs_alongside_token — spec(§3) 7.1 not clobbered", () => {
    const exposed: { key: string; api: Record<string, unknown> }[] = [];
    const bridge = {
      exposeInMainWorld: (key: string, api: Record<string, unknown>) => exposed.push({ key, api }),
    };
    const fs = createFsBridge((_channel, method) => (method === "exists" ? true : null));

    createLoopbackTokenChannel({ getToken: () => "tok-xyz" }, bridge, { fs });

    expect(exposed).toHaveLength(1);
    const api = exposed[0].api;
    expect(typeof api.getToken).toBe("function");
    expect((api.getToken as () => string)()).toBe("tok-xyz");
    expect(Object.keys(api.fs as object).sort()).toEqual(FOUR_METHODS);
  });
});
