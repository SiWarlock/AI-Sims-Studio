// RED tests — S1b-clone re-serialize (`src/serialize/serialize.ts`).
//
// §9: the cloned package re-serializes to a real DBPF buffer @s4tk can re-open with the keys intact.

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

import { Package } from "@s4tk/models";
import { describe, expect, it } from "vitest";

import { cloneDonor } from "../../src/clone/clone";
import { resolveChain } from "../../src/donor/resolveChain";
import { serializeClone } from "../../src/serialize/serialize";
import { buildFixtureDonor, GEOM_KEY, OBJD_KEY } from "../fixtures/donorFixture";

const NEW_GEOM = readFileSync(
  join(fileURLToPath(new URL(".", import.meta.url)), "..", "fixtures", "cube_v0x05.geom"),
);

describe("serializeClone (deterministic)", () => {
  it("serialize_produces_readable_dbpf", () => {
    // spec(§9): re-serialize → a non-empty DBPF buffer @s4tk re-opens; OBJD + swapped GEOM keys survive.
    const donor = buildFixtureDonor();
    const chain = resolveChain(donor.packages, donor.candidateObjdKey);
    const { package: pkg } = cloneDonor({ chain, newGeomBytes: NEW_GEOM });

    const buffer = serializeClone(pkg);
    expect(buffer.length).toBeGreaterThan(0);

    const reopened = Package.from(buffer);
    expect(reopened.getByKey(OBJD_KEY)).toBeTruthy();
    expect(reopened.getByKey(GEOM_KEY)).toBeTruthy();
  });
});
