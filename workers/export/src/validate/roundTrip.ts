// S1b-clone — DBPF round-trip + structural validation (safety rule 4's validate step).
//
// Re-OPEN the serialized buffer via @s4tk (proving the bytes parse as a real DBPF) and assert the
// structural contract the clone must hold:
//   - the §9 required resource type set is present;
//   - the swapped GEOM is present with EXACTLY the swapped-in bytes (the S1a→S1b proof survived
//     serialize→deserialize);
//   - the OBJD parses and its tuning instance resolves (non-sentinel).
// This is the gate the atomic write runs BEFORE the rename — a fail means no package is published.
// In-game placeability is S1c (the user), explicitly NOT this validation's bar (brief Q4).

import { ObjectDefinitionResource, Package } from "@s4tk/models";
import type { ResourceKey } from "@s4tk/models/types";

import { RESOURCE_TYPE } from "../donor/resolveChain";

const TYPE_TAG = new Map<number, string>(
  Object.entries(RESOURCE_TYPE).map(([tag, type]) => [type, tag]),
);
function typeTag(type: number): string {
  return TYPE_TAG.get(type) ?? `0x${type.toString(16).toUpperCase()}`;
}

export interface RoundTripExpectation {
  /** Required DBPF resource type ids that must each be present at least once. */
  requiredTypes: number[];
  /** The swapped GEOM key + the exact bytes that must round-trip. */
  swappedGeom: { key: ResourceKey; bytes: Buffer };
  /** The OBJD key that must be present + whose tuning must resolve. */
  objdKey: ResourceKey;
}

export interface RoundTripResult {
  ok: boolean;
  missingTypes: string[];
  geomPresent: boolean;
  tuningResolves: boolean;
  reason: string;
}

/** Re-open the serialized package and validate the §9 structural contract. Never throws. */
export function validateRoundTrip(buffer: Buffer, expectation: RoundTripExpectation): RoundTripResult {
  let pkg: Package;
  try {
    pkg = Package.from(buffer);
  } catch (e) {
    return {
      ok: false,
      missingTypes: expectation.requiredTypes.map(typeTag),
      geomPresent: false,
      tuningResolves: false,
      reason: `not a readable DBPF: ${e instanceof Error ? e.message : String(e)}`,
    };
  }

  // required resource type set present
  const presentTypes = new Set(pkg.entries.map((entry) => entry.key.type));
  const missingTypes = expectation.requiredTypes.filter((t) => !presentTypes.has(t)).map(typeTag);

  // swapped GEOM present with EXACTLY the swapped-in bytes (survived serialize→deserialize)
  const geomEntry = pkg.getByKey(expectation.swappedGeom.key);
  const geomPresent =
    geomEntry !== undefined &&
    Buffer.compare(geomEntry.value.getBuffer(), expectation.swappedGeom.bytes) === 0;

  // OBJD present + tuning instance resolves (non-sentinel)
  const objdEntry = pkg.getByKey(expectation.objdKey);
  let tuningResolves = false;
  if (objdEntry !== undefined) {
    const objd =
      objdEntry.value instanceof ObjectDefinitionResource
        ? objdEntry.value
        : ObjectDefinitionResource.from(objdEntry.value.getBuffer());
    const { tuningId, tuning } = objd.properties;
    tuningResolves =
      (tuningId !== undefined && tuningId !== 0n) || (tuning !== undefined && tuning.length > 0);
  }

  const ok = missingTypes.length === 0 && geomPresent && tuningResolves;
  return {
    ok,
    missingTypes,
    geomPresent,
    tuningResolves,
    reason: ok
      ? "round-trip valid: required set present, swapped GEOM survived, OBJD tuning resolves"
      : `round-trip invalid: missing=[${missingTypes.join(",")}] geomPresent=${geomPresent} tuningResolves=${tuningResolves}`,
  };
}
