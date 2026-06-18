// S1b spike entry — the DONOR-SCAN stage (clone stage = spikes-004).
//
// Wires the deterministic auto-detect + resource-resolution around the EXPLORATORY @s4tk read:
// detect the Sims 4 install → open the first FullBuild donor READ-ONLY → resolve a candidate
// Build/Buy object + its required resource set → emit a scan report (+ a scratch JSON the clone
// consumes). This is the env-ready probe entry the S1b verdict is generated from; production
// Donor-Library scan/index into the §10 store lands in Phase 5.

import { mkdtempSync, writeFileSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { Package } from "@s4tk/models";
import type { ResourceKey } from "@s4tk/models/types";

import type { ErrorCategory, ErrorCode, ExportJobReport } from "../../../packages/contracts/generated/contracts";
import { cloneDonor } from "./clone/clone";
import {
  type DonorCandidate,
  type ParsedDonorObject,
  detectSims4Install,
  resolveRequiredResources,
  scanDonorObjects,
  toDonorCandidate,
} from "./donor/scan";
import {
  RESOURCE_TYPE,
  type DonorPackageSource,
  type ResolvedChain,
  resolveChain,
} from "./donor/resolveChain";
import { serializeClone } from "./serialize/serialize";
import { validateRoundTrip } from "./validate/roundTrip";
import { atomicValidatedWrite } from "./write/atomicWrite";

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

// ─── Clone stage (spikes-004) ─────────────────────────────────────────────────────────────────────

/** Injected sources for the deterministic clone run — keeps it testable without a real Sims install. */
export interface CloneSources {
  donorPackages: DonorPackageSource[];
  candidateObjdKey: ResourceKey;
  /** S1a's emitted GEOM bytes to swap in. */
  geomBytes: Buffer;
  /** Sidecar scratch dir the validated `.package` is published into. */
  scratchDir: string;
}

const CLONE_FILENAME = "clone.package";

/** Build a contract-valid `failed` ExportJobReport (rule-6: failed ⟹ error present, no packagePath). */
function failedReport(detail: string, code: ErrorCode, category: ErrorCategory): ExportJobReport {
  return {
    status: "failed",
    packagePath: null,
    error: {
      category,
      code,
      creatorMessage: "Cloning the donor package failed.",
      maintainerDetail: detail,
      retryable: false,
    },
  };
}

/** The §9 resource tags present in the resolved chain (the ExportJobReport.resourceManifest). */
function resourceManifest(chain: ResolvedChain): string[] {
  const present = new Set(chain.all.map((entry) => entry.key.type));
  return Object.entries(RESOURCE_TYPE)
    .filter(([, type]) => present.has(type))
    .map(([tag]) => tag);
}

/**
 * Run the full clone pipeline against injected donor sources: resolveChain → cloneDonor → serialize →
 * atomicValidatedWrite (round-trip validate) → a contract-valid `ExportJobReport`. Never throws — a
 * resolution/validation failure returns a `failed` report (rule-6 status↔outputs).
 */
export async function runCloneFrom(sources: CloneSources): Promise<ExportJobReport> {
  const { donorPackages, candidateObjdKey, geomBytes, scratchDir } = sources;

  let chain: ResolvedChain;
  try {
    chain = resolveChain(donorPackages, candidateObjdKey);
  } catch (e) {
    return failedReport(
      `chain resolution failed: ${e instanceof Error ? e.message : String(e)}`,
      "VALIDATION_FAILED",
      "validation",
    );
  }

  const cloned = cloneDonor({ chain, newGeomBytes: geomBytes });
  if (cloned.swappedGeomKeys.length === 0) {
    // defensive: resolveChain guarantees ≥1 GEOM, but never let a geometry-less clone be published.
    return failedReport(
      "clone produced no swapped GEOM — the resolved chain carried no geometry",
      "VALIDATION_FAILED",
      "validation",
    );
  }
  const buffer = serializeClone(cloned.package);
  const requiredTypes = Object.values(RESOURCE_TYPE);
  const swappedGeomKey = cloned.swappedGeomKeys[0]!;

  const write = await atomicValidatedWrite({
    scratchDir,
    filename: CLONE_FILENAME,
    buffer,
    validate: (onDisk) =>
      validateRoundTrip(onDisk, {
        requiredTypes,
        swappedGeom: { key: swappedGeomKey, bytes: geomBytes },
        objdKey: candidateObjdKey,
      }).ok,
  });

  if (write.status === "failed") {
    return failedReport(
      `atomic validated write failed: ${write.reason}`,
      "DBPF_WRITE_FAILED",
      "packaging",
    );
  }

  return {
    status: "succeeded",
    packagePath: write.packagePath,
    resourceManifest: resourceManifest(chain),
    error: null,
  };
}

// ─── Live exploratory clone entry (run-and-observe → the S1b-clone verdict) ──────────────────────────

const REQUIRED_TYPE_SET = new Set<number>(Object.values(RESOURCE_TYPE));

/** Default GEOM to swap in = S1a's copied cube fixture; override with `AISIMS_GEOM_PATH`. */
function defaultGeomPath(): string {
  return join(fileURLToPath(new URL(".", import.meta.url)), "..", "test", "fixtures", "cube_v0x05.geom");
}

/** Parse a scan `objectKey` ("0xTYPE:0xGROUP:0xINSTANCE") back into a ResourceKey. */
export function parseObjectKey(objectKey: string): ResourceKey {
  const [type, group, instance] = objectKey.split(":");
  if (type === undefined || group === undefined || instance === undefined) {
    throw new Error(`malformed objectKey: ${objectKey}`);
  }
  const t = Number(type);
  const g = Number(group);
  if (!Number.isInteger(t) || !Number.isInteger(g)) {
    throw new Error(`malformed objectKey (non-numeric type/group): ${objectKey}`);
  }
  return { type: t, group: g, instance: BigInt(instance) };
}

export interface CloneRunResult {
  report: ExportJobReport;
  readyForS1c: boolean;
  installPath: string | null;
  candidateObjectKey: string | null;
  /** True if the live donor is a multi-object FullBuild (GEOM type-collection over-collects). */
  overCollected: boolean;
  /** The override-install warning for the user, or null when no package was produced. */
  overrideInstallNote: string | null;
  note: string;
}

/**
 * Run the clone against the LIVE Sims 4 install (read-only) → produce the validated `.package` for the
 * user's S1c in-game test-install. EXPLORATORY (run-and-observe). A multi-object FullBuild over-collects
 * under type-collection (brief Q2) — guarded: rather than build a wrong whole-catalog override, it
 * returns a structured finding (isolating one object needs the Phase-5 MLOD→GEOM ref-walk). A
 * single-object donor (supply via `AISIMS_SIMS4_PATH`) produces a real `.package`.
 */
export async function runClone(opts?: { geomPath?: string; scratchDir?: string }): Promise<CloneRunResult> {
  const detect = detectSims4Install();
  if (!detect.found) {
    return {
      report: failedReport(`no Sims 4 install: ${detect.reason}`, "TEST_INSTALL_FAILED", "system"),
      readyForS1c: false,
      installPath: null,
      candidateObjectKey: null,
      overCollected: false,
      overrideInstallNote: null,
      note: detect.reason,
    };
  }

  const pkgPath = detect.packages[0]!;
  const objects = await scanDonorObjects(pkgPath);
  if (objects.length === 0) {
    return {
      report: failedReport(`no OBJD candidate in ${pkgPath}`, "VALIDATION_FAILED", "validation"),
      readyForS1c: false,
      installPath: detect.installPath,
      candidateObjectKey: null,
      overCollected: false,
      overrideInstallNote: null,
      note: "no candidate",
    };
  }

  const candidate = objects[0]!;
  // Multi-object FullBuild → type-collection over-collects every catalog GEOM (brief Q2). Don't build a
  // whole-catalog override; surface the finding. Isolating one object's GEOM = Phase-5 MLOD→GEOM walk.
  if (objects.length > 1) {
    return {
      report: failedReport(
        `live FullBuild is multi-object (${objects.length} OBJDs in ${pkgPath}); GEOM type-collection over-collects the whole catalog — isolating one object's GEOM needs the MLOD→GEOM ref-walk (Phase-5). Deterministic clone+atomic-write mechanics are PROVEN green; live single-object isolation deferred.`,
        "VALIDATION_FAILED",
        "validation",
      ),
      readyForS1c: false,
      installPath: detect.installPath,
      candidateObjectKey: candidate.objectKey,
      overCollected: true,
      overrideInstallNote: null,
      note: "over-collection guard (Q2 live FullBuild)",
    };
  }

  // Single-object donor → a real clone.
  const geomBytes = await readFile(opts?.geomPath ?? defaultGeomPath());
  const buffer = await readFile(pkgPath);
  const entries = await Package.extractResourcesAsync(buffer, {
    resourceFilter: (type) => REQUIRED_TYPE_SET.has(type),
  });
  const scratchDir = opts?.scratchDir ?? mkdtempSync(join(tmpdir(), "aisims-s1b-clone-"));
  const report = await runCloneFrom({
    donorPackages: [{ path: pkgPath, entries }],
    candidateObjdKey: parseObjectKey(candidate.objectKey),
    geomBytes,
    scratchDir,
  });
  const readyForS1c = report.status === "succeeded";
  return {
    report,
    readyForS1c,
    installPath: detect.installPath,
    candidateObjectKey: candidate.objectKey,
    overCollected: false,
    overrideInstallNote: readyForS1c
      ? `OVERRIDE clone: this REPLACES donor object ${candidate.objectKey} in Build/Buy — remove the package from Mods after testing.`
      : null,
    note: report.error?.maintainerDetail ?? "clone produced",
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

  // Clone stage (spikes-004): consume the candidate → clone → atomic validated write → S1c artifact.
  const clone = await runClone({ scratchDir: scratch });
  console.log(
    "S1B_CLONE",
    JSON.stringify({
      status: clone.report.status,
      packagePath: clone.report.packagePath,
      resourceManifest: clone.report.resourceManifest ?? null,
      readyForS1c: clone.readyForS1c,
      candidate: clone.candidateObjectKey,
      overCollected: clone.overCollected,
      overrideInstallNote: clone.overrideInstallNote,
      error: clone.report.error?.maintainerDetail ?? null,
      note: clone.note,
    }),
  );

  return report.s4tkReadOk && clone.readyForS1c ? 0 : 1;
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
