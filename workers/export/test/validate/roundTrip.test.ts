// RED tests — S1b-clone DBPF round-trip validation (`src/validate/roundTrip.ts`).
//
// §9 (safety rule 4 validate step): re-open the serialized package → required resource set present +
// swapped GEOM bytes survived + OBJD tuning resolves. A missing/wrong resource fails the gate.

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import { cloneDonor } from "../../src/clone/clone";
import { RESOURCE_TYPE, resolveChain } from "../../src/donor/resolveChain";
import { serializeClone } from "../../src/serialize/serialize";
import { validateRoundTrip } from "../../src/validate/roundTrip";
import { buildFixtureDonor, GEOM_KEY, OBJD_KEY } from "../fixtures/donorFixture";

const NEW_GEOM = readFileSync(
  join(fileURLToPath(new URL(".", import.meta.url)), "..", "fixtures", "cube_v0x05.geom"),
);
const REQUIRED_TYPES = Object.values(RESOURCE_TYPE);

function validCloneBuffer(): Buffer {
  const donor = buildFixtureDonor();
  const chain = resolveChain(donor.packages, donor.candidateObjdKey);
  const { package: pkg } = cloneDonor({ chain, newGeomBytes: NEW_GEOM });
  return serializeClone(pkg);
}

describe("validateRoundTrip (deterministic)", () => {
  it("roundtrip_validate_asserts_required_set_and_tuning", () => {
    // spec(§9): a valid clone → ok, no missing types, GEOM present with swapped bytes, tuning resolves.
    const result = validateRoundTrip(validCloneBuffer(), {
      requiredTypes: REQUIRED_TYPES,
      swappedGeom: { key: GEOM_KEY, bytes: NEW_GEOM },
      objdKey: OBJD_KEY,
    });
    expect(result.ok).toBe(true);
    expect(result.missingTypes).toEqual([]);
    expect(result.geomPresent).toBe(true);
    expect(result.tuningResolves).toBe(true);
  });

  it("roundtrip_validate_flags_missing_resource", () => {
    // spec(§9): a package missing a required resource (GEOM dropped) fails the publish gate.
    const donor = buildFixtureDonor();
    const chain = resolveChain(donor.packages, donor.candidateObjdKey);
    const { package: pkg } = cloneDonor({ chain, newGeomBytes: NEW_GEOM });
    pkg.deleteByKey(GEOM_KEY);
    const result = validateRoundTrip(serializeClone(pkg), {
      requiredTypes: REQUIRED_TYPES,
      swappedGeom: { key: GEOM_KEY, bytes: NEW_GEOM },
      objdKey: OBJD_KEY,
    });
    expect(result.ok).toBe(false);
    expect(result.geomPresent).toBe(false);
  });

  it("roundtrip_validate_flags_unresolved_tuning", () => {
    // spec(§9): an OBJD whose tuning instance does NOT resolve (no tuningId / tuning) fails the gate,
    // even when every required resource is present.
    const donor = buildFixtureDonor({ noTuning: true });
    const chain = resolveChain(donor.packages, donor.candidateObjdKey);
    const { package: pkg } = cloneDonor({ chain, newGeomBytes: NEW_GEOM });
    const result = validateRoundTrip(serializeClone(pkg), {
      requiredTypes: REQUIRED_TYPES,
      swappedGeom: { key: GEOM_KEY, bytes: NEW_GEOM },
      objdKey: OBJD_KEY,
    });
    expect(result.tuningResolves).toBe(false);
    expect(result.ok).toBe(false);
  });

  it("roundtrip_validate_flags_wrong_geom_bytes", () => {
    // spec(§9): GEOM present but bytes != swapped-in → fail (the swap didn't survive serialization).
    const result = validateRoundTrip(validCloneBuffer(), {
      requiredTypes: REQUIRED_TYPES,
      swappedGeom: { key: GEOM_KEY, bytes: Buffer.from("NOT-THE-SWAPPED-GEOM") },
      objdKey: OBJD_KEY,
    });
    expect(result.ok).toBe(false);
  });
});
