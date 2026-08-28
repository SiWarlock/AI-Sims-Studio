// RED tests for the S1b donor-scan deterministic surface — `src/donor/scan.ts`.
//
// §9/§10: auto-detect the Sims 4 install + FullBuild donors, resolve a candidate Build/Buy object's
// required resource set, and emit a donorRef the clone (ExportJob.donorRef) consumes. The actual
// @s4tk parse of a real ~1 GB FullBuild package is the EXPLORATORY arm (run-and-observe, not here).
//
// The fs access is behind an injected `FsProbe` seam so auto-detect is testable without a real
// install; the contract conformance is checked against the FROZEN generated TS types (no hand-roll).

import { describe, expect, it } from "vitest";

// The frozen §9 worker contract (generated from packages/contracts; the source of truth).
import type {
  ExportJob,
  ExportJobReport,
} from "../../../../packages/contracts/generated/contracts";
import {
  EA_APP_MACOS_DEFAULT,
  REQUIRED_RESOURCES,
  detectSims4Install,
  resolveRequiredResources,
  toDonorCandidate,
  type FsProbe,
  type ParsedDonorObject,
} from "../../src/donor/scan";

const FULLBUILD = [
  `${EA_APP_MACOS_DEFAULT}/Contents/Data/Client/ClientFullBuild0.package`,
  `${EA_APP_MACOS_DEFAULT}/Contents/Data/Simulation/SimulationFullBuild0.package`,
];

/** An FsProbe that reports the given roots as installs with a fixed FullBuild list. */
function fakeFs(installs: Record<string, string[]>): FsProbe {
  return {
    isInstall: (root) => root in installs,
    listFullBuild: (root) => installs[root] ?? [],
  };
}

const COMPLETE_OBJECT: ParsedDonorObject = {
  objectKey: "0x319E4F1D:0x00000000:0x000000000000DEC0",
  tuningInstance: "0x00000000DEADBEEF",
  resources: [...REQUIRED_RESOURCES],
};

describe("auto-detect (deterministic)", () => {
  it("auto_detect_resolves_ea_app_macos_default", () => {
    // spec(§10): the verified EA-App-macOS default resolves to install root + FullBuild list.
    const result = detectSims4Install({ env: {}, fs: fakeFs({ [EA_APP_MACOS_DEFAULT]: FULLBUILD }) });
    expect(result.found).toBe(true);
    if (result.found) {
      expect(result.installPath).toBe(EA_APP_MACOS_DEFAULT);
      expect(result.packages).toEqual(FULLBUILD);
    }
  });

  it("auto_detect_env_override_wins", () => {
    // spec(§10): AISIMS_SIMS4_PATH takes precedence even when the default also exists — and returns
    // the OVERRIDE's packages, not the default's.
    const custom = "/Volumes/Games/The Sims 4.app";
    const customPkgs = [`${custom}/Contents/Data/Client/ClientFullBuild0.package`];
    const result = detectSims4Install({
      env: { AISIMS_SIMS4_PATH: custom },
      fs: fakeFs({ [custom]: customPkgs, [EA_APP_MACOS_DEFAULT]: FULLBUILD }),
    });
    expect(result.found).toBe(true);
    if (result.found) {
      expect(result.installPath).toBe(custom);
      expect(result.packages).toEqual(customPkgs);
    }
  });

  it("auto_detect_not_found_returns_structured_result", () => {
    // spec(§10): no install anywhere → a structured not-found (lead's directive: flag, don't guess
    // or throw).
    const result = detectSims4Install({ env: {}, fs: fakeFs({}) });
    expect(result.found).toBe(false);
    if (!result.found) {
      expect(result.reason).toBeTruthy();
      expect(result.probed).toContain(EA_APP_MACOS_DEFAULT);
    }
  });
});

describe("required-resource-set resolution (deterministic)", () => {
  it("resolve_required_resource_set", () => {
    // spec(§9): a complete donor object → complete (all required present + tuning resolves); a
    // donor missing GEOM → incomplete with GEOM reported missing.
    const complete = resolveRequiredResources(COMPLETE_OBJECT);
    expect(complete.complete).toBe(true);
    expect(complete.missing).toEqual([]);
    expect(complete.tuningResolves).toBe(true);

    const noGeom = resolveRequiredResources({
      ...COMPLETE_OBJECT,
      resources: REQUIRED_RESOURCES.filter((r) => r !== "GEOM"),
    });
    expect(noGeom.complete).toBe(false);
    expect(noGeom.missing).toContain("GEOM");
  });
});

describe("candidate donorRef (deterministic)", () => {
  it("candidate_donor_ref_conforms", () => {
    // spec(§9): the scan emits a donorRef + resourceManifest shape the clone consumes — assignable
    // to the FROZEN ExportJob.donorRef (string) / ExportJobReport.resourceManifest (string[]).
    const candidate = toDonorCandidate(FULLBUILD[0]!, COMPLETE_OBJECT);
    const donorRef: ExportJob["donorRef"] = candidate.donorRef;
    const manifest: NonNullable<ExportJobReport["resourceManifest"]> = candidate.resourceManifest;
    expect(typeof donorRef).toBe("string");
    expect(donorRef.length).toBeGreaterThan(0);
    expect(manifest.every((r) => typeof r === "string")).toBe(true);
    expect(manifest).toContain("GEOM");
  });
});
