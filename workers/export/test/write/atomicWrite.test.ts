// 🔒 RED tests — S1b-clone atomic validated write (`src/write/atomicWrite.ts`). The safety-rule-4 pins.
//
// §9 / Invariant 4: temp→fsync→validate→atomic-rename; NEVER a half-written/unvalidated package is
// published; writes go ONLY under the sidecar scratch dir; a live Sims "Mods" path is refused.

import { existsSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { atomicValidatedWrite } from "../../src/write/atomicWrite";

const BYTES = Buffer.from("DBPF-CLONE-BYTES-PAYLOAD");

let scratch: string;
beforeEach(() => {
  scratch = mkdtempSync(join(tmpdir(), "aisims-s1b-clone-test-"));
});
afterEach(() => {
  rmSync(scratch, { recursive: true, force: true });
});

describe("atomicValidatedWrite — safety rule 4 (load-bearing pins)", () => {
  it("atomic_write_sequence_temp_fsync_validate_rename", async () => {
    // spec(§9): the final file appears ONLY after a passing validate; validate sees the ON-DISK bytes.
    const finalPath = join(scratch, "clone.package");
    let finalExistedAtValidate = true;
    let tempExistedAtValidate = false;

    const result = await atomicValidatedWrite({
      scratchDir: scratch,
      filename: "clone.package",
      buffer: BYTES,
      validate: (written) => {
        finalExistedAtValidate = existsSync(finalPath); // must be false — not renamed yet
        tempExistedAtValidate = readdirSync(scratch).length > 0; // a temp file must already be on disk
        return Buffer.compare(written, BYTES) === 0; // validate reads what was written to disk
      },
    });

    expect(result.status).toBe("succeeded");
    expect(result.packagePath).toBe(finalPath);
    expect(finalExistedAtValidate).toBe(false);
    expect(tempExistedAtValidate).toBe(true);
    expect(existsSync(finalPath)).toBe(true);
    expect(Buffer.compare(readFileSync(finalPath), BYTES)).toBe(0);
    expect(readdirSync(scratch)).toEqual(["clone.package"]); // no temp left behind
  });

  it("atomic_write_validation_failure_no_partial", async () => {
    // spec(§9): a validate FAIL → no output file, no rename, temp discarded, status failed.
    const result = await atomicValidatedWrite({
      scratchDir: scratch,
      filename: "clone.package",
      buffer: BYTES,
      validate: () => false,
    });

    expect(result.status).toBe("failed");
    expect(result.packagePath).toBeNull();
    expect(existsSync(join(scratch, "clone.package"))).toBe(false);
    expect(readdirSync(scratch)).toEqual([]); // temp discarded — scratch is empty
  });

  it("atomic_write_io_failure_returns_failed_not_throw", async () => {
    // the "never throws" contract: an I/O failure (non-existent scratch dir) → a `failed` result, not
    // an uncaught throw — so callers always get a contract-valid report, never an unhandled rejection.
    const result = await atomicValidatedWrite({
      scratchDir: join(scratch, "does", "not", "exist"),
      filename: "clone.package",
      buffer: BYTES,
      validate: () => true,
    });
    expect(result.status).toBe("failed");
    expect(result.packagePath).toBeNull();
  });

  it("atomic_write_never_touches_mods_or_donor", async () => {
    // spec(§9): rule 4/3 — writes target ONLY the scratch dir; a path under a live Sims "Mods" folder
    // is refused before any byte is written. (Donor read-only is by construction: no donor handle.)
    const ok = await atomicValidatedWrite({
      scratchDir: scratch,
      filename: "clone.package",
      buffer: BYTES,
      validate: () => true,
    });
    expect(readdirSync(scratch)).toEqual(["clone.package"]);
    expect(ok.packagePath?.startsWith(scratch)).toBe(true);

    const modsDir = join(scratch, "The Sims 4", "Mods");
    mkdirSync(modsDir, { recursive: true });
    const refused = await atomicValidatedWrite({
      scratchDir: modsDir,
      filename: "evil.package",
      buffer: BYTES,
      validate: () => true,
    });
    expect(refused.status).toBe("failed");
    expect(existsSync(join(modsDir, "evil.package"))).toBe(false);
    expect(readdirSync(modsDir)).toEqual([]); // nothing written into a Mods folder
  });
});
