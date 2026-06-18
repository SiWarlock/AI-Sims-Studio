import { describe, expect, it } from "vitest";

import type { FsProbe } from "../../src/onboarding/fs-probe";
import { validateModsPath } from "../../src/onboarding/mods-path";

const STANDARD = "/Users/sim/Documents/Electronic Arts/The Sims 4/Mods";
const CUSTOM = "/Users/sim/MySims/Mods";

/** A probe defaulting to a writable directory; override individual predicates per case. */
function fsWith(over: Partial<FsProbe>): FsProbe {
  return {
    homeDir: () => "/Users/sim",
    exists: () => true,
    isDirectory: () => true,
    isWritable: () => true,
    ...over,
  };
}

describe("Mods-path validation (§18 onboarding item 2)", () => {
  it("test_validate_mods_path_hard_fails — spec(§18)", () => {
    const missing = validateModsPath(fsWith({ exists: () => false }), STANDARD);
    expect(missing.valid).toBe(false);
    expect(missing.blocking).toBeTruthy();

    const notDir = validateModsPath(fsWith({ isDirectory: () => false }), STANDARD);
    expect(notDir.valid).toBe(false);
    expect(notDir.blocking).toBeTruthy();

    const notWritable = validateModsPath(fsWith({ isWritable: () => false }), STANDARD);
    expect(notWritable.valid).toBe(false);
    expect(notWritable.blocking).toBeTruthy();
  });

  it("test_validate_mods_path_warns_on_shape — spec(§18)", () => {
    // A writable dir that doesn't match …/The Sims 4/Mods → non-blocking warn (custom setups OK).
    const custom = validateModsPath(fsWith({}), CUSTOM);
    expect(custom.valid).toBe(true);
    expect(custom.warnings.length).toBeGreaterThan(0);

    // The canonical shape → valid with no warnings.
    const standard = validateModsPath(fsWith({}), STANDARD);
    expect(standard.valid).toBe(true);
    expect(standard.warnings).toHaveLength(0);

    // Canonical-but-normalized variants must NOT warn (Finder trailing slash; case-insensitive FS).
    const trailingSlash = validateModsPath(fsWith({}), `${STANDARD}/`);
    expect(trailingSlash.warnings).toHaveLength(0);
    const caseVariant = validateModsPath(
      fsWith({}),
      "/Users/sim/Documents/Electronic Arts/the sims 4/mods",
    );
    expect(caseVariant.warnings).toHaveLength(0);
  });
});
