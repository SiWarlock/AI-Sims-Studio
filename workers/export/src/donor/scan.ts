// S1b donor-scan — auto-detect the Sims 4 install + FullBuild donors, open a donor READ-ONLY via
// @s4tk, and resolve a candidate Build/Buy object's required resource set (§9 / §10).
//
// Split by testability: the auto-detect (behind an injected `FsProbe` seam) + the required-resource
// resolution + the donorRef shaping are DETERMINISTIC (unit-tested). The actual @s4tk parse of a
// real ~1 GB FullBuild package (`scanDonorObjects`) is the EXPLORATORY arm — run-and-observe.
//
// Safety rule 4: donors are opened READ-ONLY (only @s4tk read APIs; never a save/write on the
// game's packages). This worker writes only to sidecar scratch.

import { existsSync, readdirSync, statSync } from "node:fs";
import { readFile } from "node:fs/promises";
import { join } from "node:path";

import { ObjectDefinitionResource, Package } from "@s4tk/models";
import { BinaryResourceType } from "@s4tk/models/enums";

// The §9 required Build/Buy resource set the clone needs (OBJD + catalog + model/LOD/GEOM + footprint
// + rig + image). `_IMG·DST` is tagged `IMG`.
export const REQUIRED_RESOURCES = [
  "OBJD",
  "COBJ",
  "MODL",
  "MLOD",
  "GEOM",
  "FTPT",
  "RIG",
  "IMG",
] as const;
export type ResourceTag = (typeof REQUIRED_RESOURCES)[number];

// ─── Auto-detect ────────────────────────────────────────────────────────────────────────────────

/** The orchestrator-verified EA-App-macOS install root. */
export const EA_APP_MACOS_DEFAULT = "/Applications/EA Games/The Sims 4.app";

export interface Sims4Install {
  found: true;
  installPath: string;
  packages: string[];
}
export interface Sims4NotFound {
  found: false;
  reason: string;
  probed: string[];
}
export type DetectResult = Sims4Install | Sims4NotFound;

/** Filesystem seam — injected so auto-detect is testable without a real install. */
export interface FsProbe {
  isInstall(root: string): boolean;
  listFullBuild(root: string): string[];
}

const DATA_SUBDIRS = ["Client", "Simulation"] as const;
const FULLBUILD_RE = /FullBuild.*\.package$/i;
// EA FullBuild donors are ~1 GB; reject an absurd size before the full read (OOM / too-large guard).
const MAX_DONOR_BYTES = 4 * 1024 * 1024 * 1024;

/** Production FsProbe over `node:fs` (read-only). */
export const realFsProbe: FsProbe = {
  isInstall(root) {
    return DATA_SUBDIRS.some((d) => {
      const dir = join(root, "Contents", "Data", d);
      return existsSync(dir) && statSync(dir).isDirectory();
    });
  },
  listFullBuild(root) {
    const out: string[] = [];
    for (const d of DATA_SUBDIRS) {
      const dir = join(root, "Contents", "Data", d);
      if (existsSync(dir) && statSync(dir).isDirectory()) {
        for (const f of readdirSync(dir)) {
          if (FULLBUILD_RE.test(f)) out.push(join(dir, f));
        }
      }
    }
    return out.sort();
  },
};

/**
 * Resolve the Sims 4 install + its FullBuild donor packages. Precedence: the `AISIMS_SIMS4_PATH`
 * env override, then the EA-App-macOS default. Returns a structured `not-found` (never throws, never
 * guesses) so the orchestrator can flag an absent install to the lead → user.
 */
export function detectSims4Install(opts?: {
  env?: Record<string, string | undefined>;
  fs?: FsProbe;
}): DetectResult {
  const env = opts?.env ?? process.env;
  const fs = opts?.fs ?? realFsProbe;
  const probed: string[] = [];
  const override = env.AISIMS_SIMS4_PATH;
  if (override) probed.push(override);
  probed.push(EA_APP_MACOS_DEFAULT);

  for (const root of probed) {
    if (fs.isInstall(root)) {
      const packages = fs.listFullBuild(root);
      if (packages.length > 0) return { found: true, installPath: root, packages };
    }
  }
  return {
    found: false,
    reason: "no Sims 4 install with FullBuild packages found (set AISIMS_SIMS4_PATH)",
    probed,
  };
}

// ─── Required-resource resolution (deterministic) ─────────────────────────────────────────────────

export interface ParsedDonorObject {
  objectKey: string;
  tuningInstance: string | null;
  resources: readonly ResourceTag[];
}
export interface ResourceSetResult {
  complete: boolean;
  present: ResourceTag[];
  missing: ResourceTag[];
  tuningResolves: boolean;
}

/** Resolve which required resources a candidate donor object carries + whether its tuning resolves. */
export function resolveRequiredResources(obj: ParsedDonorObject): ResourceSetResult {
  const present = REQUIRED_RESOURCES.filter((r) => obj.resources.includes(r));
  const missing = REQUIRED_RESOURCES.filter((r) => !obj.resources.includes(r));
  const tuningResolves = obj.tuningInstance !== null && obj.tuningInstance.length > 0;
  return { complete: missing.length === 0 && tuningResolves, present, missing, tuningResolves };
}

// ─── Candidate donorRef (deterministic) ───────────────────────────────────────────────────────────

export interface DonorCandidate {
  donorRef: string;
  objectKey: string;
  resourceManifest: string[];
}

/** Shape a scan result into the `donorRef` (+ manifest) the clone (`ExportJob.donorRef`) consumes. */
export function toDonorCandidate(packagePath: string, obj: ParsedDonorObject): DonorCandidate {
  const { present } = resolveRequiredResources(obj);
  return {
    donorRef: `${packagePath}#${obj.objectKey}`,
    objectKey: obj.objectKey,
    resourceManifest: [...present],
  };
}

// ─── Exploratory @s4tk reader (run-and-observe; NOT unit-tested) ──────────────────────────────────

function keyStr(type: number, group: number, instance: bigint): string {
  const hex = (n: number | bigint, w: number) => n.toString(16).toUpperCase().padStart(w, "0");
  // mask the 32-bit type/group to unsigned so a sign-extended number never renders a `-` in the key
  return `0x${hex(type >>> 0, 8)}:0x${hex(group >>> 0, 8)}:0x${hex(instance, 16)}`;
}

/**
 * Open a FullBuild donor package READ-ONLY and resolve candidate Build/Buy objects from their OBJDs.
 * Reads via `extractResourcesAsync(buffer, {resourceFilter, limit})` — the filter+limit decode only
 * the matched OBJDs (a transient package Buffer, NOT a full `Package.from` materialization). Resource
 * tags are the OBJD's directly-referenced set (OBJD/MODL/FTPT/RIG/IMG + tuning); COBJ/MLOD/GEOM live a
 * level deeper (resolved by the clone, spikes-004). Returns candidates best-first: tuning-resolved,
 * then decorative (fewest slots), then most resources resolved.
 *
 * NOTE: the memory-bounded MMAP path (`streamResourcesAsync` + the `@s4tk/plugin-bufferfromfile`
 * native plugin) is the production ideal, but the plugin's native `.node` doesn't build on this setup
 * — deferred (Phase-5). The buffer path is confirmed working + fast on the real 1 GB EA donors.
 */
export async function scanDonorObjects(
  packagePath: string,
  limit = 256,
): Promise<ParsedDonorObject[]> {
  const size = statSync(packagePath).size;
  if (size > MAX_DONOR_BYTES) {
    throw new Error(`donor package exceeds the ${MAX_DONOR_BYTES}-byte cap: ${size}`);
  }
  const buffer = await readFile(packagePath);
  const entries = await Package.extractResourcesAsync<ObjectDefinitionResource>(buffer, {
    resourceFilter: (type) => type === BinaryResourceType.ObjectDefinition,
    limit,
  });

  const objects: { obj: ParsedDonorObject; slots: number }[] = [];
  for (const { key, value } of entries) {
    const p = value.properties;
    const tags: ResourceTag[] = ["OBJD"];
    if (p.models?.length) tags.push("MODL");
    if (p.footprints?.length) tags.push("FTPT");
    if (p.rigs?.length) tags.push("RIG");
    if (p.icons?.length) tags.push("IMG");
    // tuningId 0n is EA's "no tuning" sentinel → null (not a resolved tuning); empty `tuning` → null.
    let tuning: string | null = null;
    if (p.tuningId !== undefined && p.tuningId !== 0n) {
      tuning = `0x${p.tuningId.toString(16).toUpperCase()}`;
    } else if (p.tuning && p.tuning.length > 0) {
      tuning = p.tuning;
    }
    objects.push({
      obj: {
        objectKey: keyStr(key.type, key.group, key.instance),
        tuningInstance: tuning,
        resources: tags,
      },
      slots: p.slots?.length ?? 0,
    });
  }
  // best-first: tuning-resolved (mirrors resolveRequiredResources' rule), then decorative (fewest
  // slots), then most resources resolved.
  const hasTuning = (o: { obj: ParsedDonorObject }) =>
    o.obj.tuningInstance !== null && o.obj.tuningInstance.length > 0;
  objects.sort(
    (a, b) =>
      Number(hasTuning(b)) - Number(hasTuning(a)) ||
      a.slots - b.slots ||
      b.obj.resources.length - a.obj.resources.length,
  );
  return objects.map((o) => o.obj);
}
