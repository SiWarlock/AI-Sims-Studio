// S1b-clone — the clone transform: swap S1a's emitted GEOM into the donor's GEOM resource, carry every
// other resource through UNCHANGED (OBJD→tuning / COBJ / MODL / MLOD / FTPT / RIG / IMG / SLOT preserved
// byte-identical). Builds a NEW in-memory @s4tk Package; the donor entries are cloned, never mutated
// (safety rule 4 — game packages are immutable inputs).
//
// Spike scope (brief Q-flag): the production clone ALSO swaps textures / thumbnail / COBJ for new
// catalog content. The spike has only a new GEOM (the S1a→S1b proof), so it swaps GEOM and PRESERVES
// the rest — yielding an OVERRIDE package (same donor TGI keys) the user installs to confirm the
// donor object now renders/places as the headless-Mac cube (S1c). Re-keying to a fresh non-colliding
// object (new GUIDs + MODL/MLOD ref-rewrite) needs binary model parsing → Phase 5.

import { Package, RawResource } from "@s4tk/models";
import type { ResourceKey } from "@s4tk/models/types";

import { RESOURCE_TYPE, type ResolvedChain } from "../donor/resolveChain";

export interface CloneInput {
  chain: ResolvedChain;
  /** S1a's emitted GEOM bytes to swap into every GEOM resource of the chain. */
  newGeomBytes: Buffer;
}

export interface CloneResult {
  package: Package;
  /** GEOM keys whose bytes were replaced with `newGeomBytes`. */
  swappedGeomKeys: ResourceKey[];
  /** Keys carried through byte-identical (OBJD/COBJ/MODL/MLOD/FTPT/RIG/IMG/SLOT). */
  preservedKeys: ResourceKey[];
}

/** Build the cloned package: GEOM bytes swapped, all other donor resources preserved. */
export function cloneDonor(input: CloneInput): CloneResult {
  const { chain, newGeomBytes } = input;
  const pkg = new Package();
  const swappedGeomKeys: ResourceKey[] = [];
  const preservedKeys: ResourceKey[] = [];

  for (const entry of chain.all) {
    if (entry.key.type === RESOURCE_TYPE.GEOM) {
      // swap: a fresh RawResource carrying S1a's GEOM bytes under the donor's GEOM key.
      pkg.add(entry.key, RawResource.from(Buffer.from(newGeomBytes)));
      swappedGeomKeys.push(entry.key);
    } else {
      // preserve: clone the donor resource (never mutate the donor — rule 4 read-only).
      pkg.add(entry.key, entry.value.clone());
      preservedKeys.push(entry.key);
    }
  }

  return { package: pkg, swappedGeomKeys, preservedKeys };
}
