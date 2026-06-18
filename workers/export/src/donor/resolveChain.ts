// S1b-clone — resolve the candidate Build/Buy object's deferred [COBJ, MLOD, GEOM] chain.
//
// The donor-scan (`src/donor/scan.ts`) resolved the OBJD's DIRECT refs (MODL/FTPT/RIG/IMG/tuning) and
// DEFERRED [COBJ, MLOD, GEOM] to the clone. This module follows the chain one level deeper, across the
// FullBuild package set if a ref leaves the candidate's package:
//   - DIRECT-REF resolved (exact, even in a multi-object package): MODL/FTPT/RIG/IMG/SLOT — via the
//     OBJD's `ResourceKey[]` properties (models/footprints/rigs/icons/slots).
//   - TYPE-COLLECTED (the spike simplification): COBJ/MLOD/GEOM — no direct OBJD ref, and @s4tk does
//     not model MODL/MLOD internals (they decode as RawResource), so the deep MODL→MLOD→GEOM binary
//     ref-walk is out of spike scope. For a single-object donor, type-collection across the set is
//     exact; for the live multi-object FullBuild it OVER-collects — the verdict's exploratory arm
//     re-scans for an in-package single-object candidate rather than grinding (brief Q2).
//
// Safety rule 4: the donor entries handed in were read READ-ONLY (the caller used @s4tk read APIs);
// this module never opens or writes a game package.

import { ObjectDefinitionResource } from "@s4tk/models";
import { BinaryResourceType } from "@s4tk/models/enums";
import type { ResourceKey, ResourceKeyPair } from "@s4tk/models/types";

// Sims 4 GEOM (geometry) — omitted from @s4tk's intentionally-incomplete BinaryResourceType enum.
export const GEOM_TYPE = 0x015a1849;

/** The §9 Build/Buy resource type ids the clone carries (tag → DBPF type number). */
export const RESOURCE_TYPE = {
  OBJD: BinaryResourceType.ObjectDefinition,
  COBJ: BinaryResourceType.ObjectCatalog,
  MODL: BinaryResourceType.Model,
  MLOD: BinaryResourceType.ModelLod,
  GEOM: GEOM_TYPE,
  FTPT: BinaryResourceType.Footprint,
  RIG: BinaryResourceType.Rig,
  IMG: BinaryResourceType.DstImage,
  SLOT: BinaryResourceType.Slot,
} as const;

/** A donor package's read-only resource entries (extracted via @s4tk read APIs) + its source path. */
export interface DonorPackageSource {
  path: string;
  entries: ResourceKeyPair[];
}

/** The resolved clone chain — resources grouped by role + a flat de-duped carry set. */
export interface ResolvedChain {
  objd: ResourceKeyPair<ObjectDefinitionResource>;
  cobj: ResourceKeyPair[];
  modl: ResourceKeyPair[];
  mlod: ResourceKeyPair[];
  geom: ResourceKeyPair[];
  ftpt: ResourceKeyPair[];
  rig: ResourceKeyPair[];
  img: ResourceKeyPair[];
  slot: ResourceKeyPair[];
  /** Every resource carried into the clone, de-duped by TGI key. */
  all: ResourceKeyPair[];
  /** True if any resolved resource came from a package other than the OBJD's. */
  crossPackage: boolean;
}

export class ChainResolutionError extends Error {}

/** A resource entry paired with the donor package path it was read from (for crossPackage provenance). */
interface Sourced {
  entry: ResourceKeyPair;
  path: string;
}

function keyEquals(a: ResourceKey, b: ResourceKey): boolean {
  return a.type === b.type && a.group === b.group && a.instance === b.instance;
}

function keyStr(k: ResourceKey): string {
  return `${k.type}:${k.group}:${k.instance}`;
}

/**
 * Resolve the candidate OBJD's clone chain across the donor package set. Throws `ChainResolutionError`
 * if the candidate OBJD is not found or the mandatory GEOM role cannot be resolved.
 *
 * Resolution strategy (brief Q2, orchestrator-approved):
 *   - DIRECT-REF (exact, even in a multi-object package): MODL/FTPT/RIG/IMG/SLOT via the OBJD's
 *     `ResourceKey[]` properties.
 *   - TYPE-COLLECTED across the package set: COBJ/MLOD/GEOM (no direct OBJD ref; @s4tk decodes
 *     MODL/MLOD as RawResource, so a precise MODL→MLOD→GEOM binary ref-walk is out of spike scope and
 *     is recorded as a Phase-5 ledger item). Single-object donor ⇒ exact; the live multi-object
 *     FullBuild over-collects → the exploratory arm re-scans for a co-located single-object candidate.
 */
export function resolveChain(
  packages: DonorPackageSource[],
  candidateObjdKey: ResourceKey,
): ResolvedChain {
  const flat: Sourced[] = [];
  for (const pkg of packages) {
    for (const entry of pkg.entries) flat.push({ entry, path: pkg.path });
  }

  const objdSource = flat.find((f) => keyEquals(f.entry.key, candidateObjdKey));
  if (!objdSource) {
    throw new ChainResolutionError(`candidate OBJD not found in the donor set: ${keyStr(candidateObjdKey)}`);
  }
  const objdPath = objdSource.path;

  let objdValue: ObjectDefinitionResource;
  try {
    objdValue =
      objdSource.entry.value instanceof ObjectDefinitionResource
        ? objdSource.entry.value
        : ObjectDefinitionResource.from(objdSource.entry.value.getBuffer());
  } catch (e) {
    throw new ChainResolutionError(
      `candidate OBJD ${keyStr(candidateObjdKey)} did not parse: ${e instanceof Error ? e.message : String(e)}`,
    );
  }
  const props = objdValue.properties;

  // Resolve to {entry, path} so crossPackage reflects PROVENANCE (which package an entry came from),
  // not mere presence elsewhere; a key found in the OBJD's own package always wins over a duplicate.
  const sourcesForKey = (k: ResourceKey): Sourced[] => flat.filter((f) => keyEquals(f.entry.key, k));
  const pickLocalFirst = (cands: Sourced[]): Sourced | undefined =>
    cands.find((c) => c.path === objdPath) ?? cands[0];

  // DIRECT-REF resolution: exact keys from the OBJD's properties (prefer the local copy).
  const byKey = (refs: ResourceKey[] | undefined): Sourced[] =>
    (refs ?? [])
      .map((ref) => pickLocalFirst(sourcesForKey(ref)))
      .filter((s): s is Sourced => s !== undefined);

  // TYPE-COLLECTED resolution: one entry per distinct key of the type (prefer the local copy).
  const byType = (type: number): Sourced[] => {
    const seen = new Set<string>();
    const out: Sourced[] = [];
    for (const f of flat) {
      if (f.entry.key.type !== type) continue;
      const id = keyStr(f.entry.key);
      if (seen.has(id)) continue;
      seen.add(id);
      const picked = pickLocalFirst(sourcesForKey(f.entry.key));
      if (picked) out.push(picked);
    }
    return out;
  };

  const modlS = byKey(props.models);
  const ftptS = byKey(props.footprints);
  const rigS = byKey(props.rigs);
  const imgS = byKey(props.icons);
  const slotS = byKey(props.slots);
  const cobjS = byType(RESOURCE_TYPE.COBJ);
  const mlodS = byType(RESOURCE_TYPE.MLOD);
  const geomS = byType(RESOURCE_TYPE.GEOM);

  if (geomS.length === 0) {
    throw new ChainResolutionError(
      `no GEOM resolved for candidate ${keyStr(candidateObjdKey)} — a Build/Buy clone must carry geometry`,
    );
  }

  // crossPackage: any RESOLVED (chosen) resource came from a package other than the OBJD's.
  const resolvedSources = [...modlS, ...mlodS, ...geomS, ...cobjS, ...ftptS, ...rigS, ...imgS, ...slotS];
  const crossPackage = resolvedSources.some((s) => s.path !== objdPath);

  const toEntries = (sources: Sourced[]): ResourceKeyPair[] => sources.map((s) => s.entry);
  const modl = toEntries(modlS);
  const ftpt = toEntries(ftptS);
  const rig = toEntries(rigS);
  const img = toEntries(imgS);
  const slot = toEntries(slotS);
  const cobj = toEntries(cobjS);
  const mlod = toEntries(mlodS);
  const geom = toEntries(geomS);

  const objd: ResourceKeyPair = { key: objdSource.entry.key, value: objdValue };
  const grouped = [objd, ...modl, ...mlod, ...geom, ...cobj, ...ftpt, ...rig, ...img, ...slot];

  // Flat carry set, de-duped by TGI key (first occurrence wins).
  const seen = new Set<string>();
  const all: ResourceKeyPair[] = [];
  for (const res of grouped) {
    const id = keyStr(res.key);
    if (seen.has(id)) continue;
    seen.add(id);
    all.push(res);
  }

  return {
    objd: objd as ResourceKeyPair<ObjectDefinitionResource>,
    cobj,
    modl,
    mlod,
    geom,
    ftpt,
    rig,
    img,
    slot,
    all,
    crossPackage,
  };
}
