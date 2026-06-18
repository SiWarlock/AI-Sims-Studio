// RED tests — S1b-clone transform (`src/clone/clone.ts`).
//
// §9: swap S1a's emitted GEOM bytes into the donor's GEOM resource; carry OBJD→tuning / FTPT / RIG /
// SLOT (and the rest of the §9 set) through byte-identical; never mutate the donor (rule 4).

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import { cloneDonor } from "../../src/clone/clone";
import { resolveChain } from "../../src/donor/resolveChain";
import {
  buildFixtureDonor,
  DONOR_GEOM_BYTES,
  FTPT_KEY,
  GEOM_KEY,
  OBJD_KEY,
  RIG_KEY,
  SLOT_KEY,
} from "../fixtures/donorFixture";

const NEW_GEOM = readFileSync(
  join(fileURLToPath(new URL(".", import.meta.url)), "..", "fixtures", "cube_v0x05.geom"),
);

describe("cloneDonor (deterministic)", () => {
  it("clone_swaps_geom_preserves_obj_ftpt_rig_slot", () => {
    // spec(§9): GEOM bytes == S1a's swapped-in GEOM; OBJD/FTPT/RIG/SLOT byte-identical to the donor.
    const donor = buildFixtureDonor();
    const chain = resolveChain(donor.packages, donor.candidateObjdKey);
    const result = cloneDonor({ chain, newGeomBytes: NEW_GEOM });

    const geom = result.package.getByKey(GEOM_KEY);
    expect(geom).toBeTruthy();
    expect(Buffer.compare(geom.value.getBuffer(), NEW_GEOM)).toBe(0);
    expect(Buffer.compare(geom.value.getBuffer(), DONOR_GEOM_BYTES)).not.toBe(0);
    expect(result.swappedGeomKeys).toContainEqual(GEOM_KEY);

    const preserved: Array<[typeof OBJD_KEY, { value: { getBuffer(): Buffer } }]> = [
      [OBJD_KEY, chain.objd],
      [FTPT_KEY, chain.ftpt[0]!],
      [RIG_KEY, chain.rig[0]!],
      [SLOT_KEY, chain.slot[0]!],
    ];
    for (const [k, original] of preserved) {
      const cloned = result.package.getByKey(k);
      expect(cloned).toBeTruthy();
      expect(Buffer.compare(cloned.value.getBuffer(), original.value.getBuffer())).toBe(0);
      expect(result.preservedKeys).toContainEqual(k);
    }
  });

  it("clone_does_not_mutate_donor", () => {
    // safety rule 4: donor entries are READ-ONLY — the donor's GEOM resource is untouched post-clone.
    const donor = buildFixtureDonor();
    const chain = resolveChain(donor.packages, donor.candidateObjdKey);
    const donorGeom = chain.geom[0]!;
    cloneDonor({ chain, newGeomBytes: NEW_GEOM });
    expect(Buffer.compare(donorGeom.value.getBuffer(), DONOR_GEOM_BYTES)).toBe(0);
  });
});
