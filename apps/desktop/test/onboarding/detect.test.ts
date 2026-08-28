import { describe, expect, it } from "vitest";

import { detectSimsInstall } from "../../src/onboarding/detect";
import type { FsProbe } from "../../src/onboarding/fs-probe";

const HOME = "/Users/sim";
const USER_DIR = `${HOME}/Documents/Electronic Arts/The Sims 4`;

function probe(present: ReadonlySet<string>): FsProbe {
  return {
    homeDir: () => HOME,
    exists: (p) => present.has(p),
    isDirectory: (p) => present.has(p),
    isWritable: () => true,
  };
}

describe("Sims-install detection (§18 onboarding item 2)", () => {
  it("test_detect_returns_default_mods_path_when_user_dir_present — spec(§18)", () => {
    const result = detectSimsInstall(probe(new Set([USER_DIR])));
    expect(result.detected).toBe(true);
    expect(result.userDataDir).toBe(USER_DIR);
    expect(result.defaultModsPath).toBe(`${USER_DIR}/Mods`);
    expect(result.defaultModsPath?.endsWith("/The Sims 4/Mods")).toBe(true);
  });

  it("test_detect_missing_install_no_throw — spec(§18)", () => {
    const result = detectSimsInstall(probe(new Set()));
    expect(result.detected).toBe(false);
    expect(result.defaultModsPath).toBeUndefined();
    expect(result.userDataDir).toBeUndefined();
  });
});
