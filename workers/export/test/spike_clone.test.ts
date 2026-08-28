// RED tests — S1b-clone end-to-end report contract (`src/spike_clone.ts` `runCloneFrom`).
//
// §9: the full resolve→clone→serialize→atomic-validated-write path returns a contract-valid
// ExportJobReport — rule-6 status↔outputs (succeeded ⟹ packagePath + no error; failed ⟹ error + none).
// Injected donor sources keep this deterministic (no real Sims install); the live run is exploratory.

import { existsSync, mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { afterEach, beforeEach, describe, expect, it } from "vitest";

import { runCloneFrom } from "../src/spike_clone";
import { buildFixtureDonor } from "./fixtures/donorFixture";

const NEW_GEOM = readFileSync(
  join(fileURLToPath(new URL(".", import.meta.url)), "fixtures", "cube_v0x05.geom"),
);

let scratch: string;
beforeEach(() => {
  scratch = mkdtempSync(join(tmpdir(), "aisims-s1b-clone-run-"));
});
afterEach(() => {
  rmSync(scratch, { recursive: true, force: true });
});

describe("runCloneFrom — end-to-end report contract (deterministic)", () => {
  it("clone_report_contract_valid_succeeded", async () => {
    // spec(§9): succeeded ⟹ packagePath in scratch + error None; resourceManifest carries the §9 set.
    const donor = buildFixtureDonor();
    const report = await runCloneFrom({
      donorPackages: donor.packages,
      candidateObjdKey: donor.candidateObjdKey,
      geomBytes: NEW_GEOM,
      scratchDir: scratch,
    });

    expect(report.status).toBe("succeeded");
    expect(report.packagePath).toBeTruthy();
    expect(report.packagePath!.startsWith(scratch)).toBe(true);
    expect(existsSync(report.packagePath!)).toBe(true);
    expect(report.error ?? null).toBeNull();
    expect(report.resourceManifest).toContain("GEOM");
  });

  it("clone_report_contract_valid_failed", async () => {
    // spec(§9): an unresolvable chain (GEOM absent) ⟹ failed + error present + NO packagePath (rule 6).
    const donor = buildFixtureDonor({ omitGeom: true });
    const report = await runCloneFrom({
      donorPackages: donor.packages,
      candidateObjdKey: donor.candidateObjdKey,
      geomBytes: NEW_GEOM,
      scratchDir: scratch,
    });

    expect(report.status).toBe("failed");
    expect(report.error).toBeTruthy();
    expect(report.packagePath ?? null).toBeNull();
  });
});
