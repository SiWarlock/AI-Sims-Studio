import { afterEach, describe, expect, it } from "vitest";

import { detectSimsInstall } from "../../src/onboarding/detect";
import type { FsProbe } from "../../src/onboarding/fs-probe";
import { resolveFsProbe } from "../../src/onboarding/renderer-fs";

const globalWithAisims = globalThis as { aisims?: { fs?: unknown } };

function bridge(over: Partial<FsProbe>): FsProbe {
  return {
    exists: () => false,
    isDirectory: () => false,
    isWritable: () => false,
    homeDir: () => "/Users/sim",
    ...over,
  };
}

describe("resolveFsProbe — real bridge or safe default (§18)", () => {
  afterEach(() => {
    delete globalWithAisims.aisims;
  });

  it("test_resolve_fs_probe_uses_real_bridge_or_safe_defaults — spec(§18)", () => {
    // Shape-valid bridge → resolved (returned as-is).
    const real = bridge({ exists: () => true });
    globalWithAisims.aisims = { fs: real };
    expect(resolveFsProbe()).toBe(real);

    // Absent → NOT_AVAILABLE (every path blocks; nothing detected).
    delete globalWithAisims.aisims;
    expect(resolveFsProbe().exists("/anything")).toBe(false);

    // Shape-INVALID (missing 3 methods) → NOT_AVAILABLE, never the partial object.
    globalWithAisims.aisims = { fs: { exists: () => true } as unknown as FsProbe };
    expect(resolveFsProbe().exists("/anything")).toBe(false);

    // Shape-INVALID (a member is the wrong type, not a function) → NOT_AVAILABLE.
    globalWithAisims.aisims = {
      fs: {
        exists: "nope",
        isDirectory: () => true,
        isWritable: () => true,
        homeDir: () => "/h",
      } as unknown as FsProbe,
    };
    expect(resolveFsProbe().exists("/anything")).toBe(false);
  });

  it("test_detect_sims_install_over_bridged_probe — spec(§18)", () => {
    const userDir = "/Users/sim/Documents/Electronic Arts/The Sims 4";
    globalWithAisims.aisims = {
      fs: bridge({
        homeDir: () => "/Users/sim",
        exists: (p) => p === userDir,
        isDirectory: (p) => p === userDir,
      }),
    };
    const result = detectSimsInstall(resolveFsProbe());
    expect(result.detected).toBe(true);
    expect(result.defaultModsPath).toBe(`${userDir}/Mods`);
  });
});
