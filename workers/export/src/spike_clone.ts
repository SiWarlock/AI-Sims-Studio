// S1b spike entry — the DONOR-SCAN stage (clone stage = spikes-004).
//
// Wires the deterministic auto-detect + resource-resolution around the EXPLORATORY @s4tk read:
// detect the Sims 4 install → open the first FullBuild donor READ-ONLY → resolve a candidate
// Build/Buy object + its required resource set → emit a scan report (+ a scratch JSON the clone
// consumes). This is the env-ready probe entry the S1b verdict is generated from; production
// Donor-Library scan/index into the §10 store lands in Phase 5.

import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  type DonorCandidate,
  type ParsedDonorObject,
  detectSims4Install,
  resolveRequiredResources,
  scanDonorObjects,
  toDonorCandidate,
} from "./donor/scan";

export interface DonorScanReport {
  installPath: string | null;
  packagesFound: string[];
  packageScanned: string | null;
  objdCount: number;
  candidate: DonorCandidate | null;
  parsedObject: ParsedDonorObject | null;
  // Required resources the scan confirmed from the OBJD's direct references.
  resolvedByScan: string[];
  // Required resources NOT-RESOLVED-BY-SCAN (the clone resolves the OBJD→MODL→MLOD→GEOM chain + COBJ
  // in spikes-004, possibly cross-package). NOT "absent from donor" — a Build/Buy object always has
  // geometry; the scan just doesn't follow the transitive chain.
  deferredToClone: string[];
  tuningResolves: boolean;
  s4tkReadOk: boolean;
  note: string;
}

function notFound(reason: string): DonorScanReport {
  return {
    installPath: null,
    packagesFound: [],
    packageScanned: null,
    objdCount: 0,
    candidate: null,
    parsedObject: null,
    resolvedByScan: [],
    deferredToClone: [],
    tuningResolves: false,
    s4tkReadOk: false,
    note: reason,
  };
}

/** Run the S1b donor-scan: detect → @s4tk read-only → resolve candidate → report. Never throws. */
export async function runDonorScan(): Promise<DonorScanReport> {
  const detect = detectSims4Install();
  if (!detect.found) {
    return notFound(`not-found: ${detect.reason} (probed ${detect.probed.join(", ")})`);
  }
  const pkg = detect.packages[0]!;
  let objs: ParsedDonorObject[];
  try {
    objs = await scanDonorObjects(pkg);
  } catch (e) {
    return {
      ...notFound(`@s4tk failed to read ${pkg}: ${e instanceof Error ? e.message : String(e)}`),
      installPath: detect.installPath,
      packagesFound: detect.packages,
      packageScanned: pkg,
    };
  }

  const parsed = objs[0] ?? null;
  const rr = parsed ? resolveRequiredResources(parsed) : null;
  const candidate = parsed ? toDonorCandidate(pkg, parsed) : null;
  return {
    installPath: detect.installPath,
    packagesFound: detect.packages,
    packageScanned: pkg,
    objdCount: objs.length,
    candidate,
    parsedObject: parsed,
    resolvedByScan: rr?.present ?? [],
    deferredToClone: rr?.missing ?? [],
    tuningResolves: rr?.tuningResolves ?? false,
    s4tkReadOk: true,
    note: parsed
      ? "@s4tk read OK — candidate OBJD resolved; resolvedByScan = the OBJD's direct refs (+ tuning). " +
        "deferredToClone [COBJ/MLOD/GEOM] are NOT-RESOLVED-BY-SCAN (the clone follows the " +
        "OBJD→MODL→MLOD→GEOM chain + COBJ, spikes-004, possibly cross-package) — NOT absent from the donor."
      : "@s4tk read OK but no OBJD found in the scanned package",
  };
}

async function main(): Promise<number> {
  // randomized scratch dir + owner-only file: no predictable path to pre-create / symlink-clobber,
  // and the report (install paths, donor keys) is not world-readable.
  const scratch = mkdtempSync(join(tmpdir(), "aisims-s1b-scan-"));
  const report = await runDonorScan();
  const out = join(scratch, "donor-scan.json");
  writeFileSync(out, JSON.stringify(report, null, 2), { mode: 0o600 });
  console.log(
    "DONOR_SCAN",
    JSON.stringify({
      s4tkReadOk: report.s4tkReadOk,
      installPath: report.installPath,
      objdCount: report.objdCount,
      candidate: report.candidate?.objectKey ?? null,
      resolvedByScan: report.resolvedByScan,
      deferredToClone: report.deferredToClone,
      note: report.note,
    }),
  );
  console.log("report written:", out);
  return report.s4tkReadOk ? 0 : 1;
}

// Run as the env-ready probe entry (not imported by tests).
if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  void main()
    .then((code) => {
      process.exitCode = code;
    })
    .catch((e: unknown) => {
      console.error(e);
      process.exitCode = 1;
    });
}
