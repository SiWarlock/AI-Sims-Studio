// RED tests — S1b-clone chain resolution (`src/donor/resolveChain.ts`).
//
// §9/§10: from the candidate OBJD, resolve the deferred [COBJ, MLOD, GEOM] chain (+ the direct-ref
// MODL/FTPT/RIG/IMG/SLOT), across the FullBuild package set when a ref leaves the candidate's package.
// Against a deterministic single-object fixture donor; the live ~1 GB FullBuild is the exploratory arm.

import { describe, expect, it } from "vitest";

import { ChainResolutionError, RESOURCE_TYPE, resolveChain } from "../../src/donor/resolveChain";
import { buildFixtureDonor, MODL_KEY } from "../fixtures/donorFixture";

describe("resolveChain (deterministic)", () => {
  it("resolve_chain_objd_modl_mlod_geom", () => {
    // spec(§9): from the candidate OBJD, resolve the full §9 required set incl. the deferred
    // [COBJ, MLOD, GEOM] chain + the direct-ref MODL — co-located, so crossPackage is false.
    const { packages, candidateObjdKey } = buildFixtureDonor();
    const chain = resolveChain(packages, candidateObjdKey);

    expect(chain.objd.key).toEqual(candidateObjdKey);
    expect(chain.modl.map((e) => e.key.instance)).toContain(MODL_KEY.instance);
    expect(chain.mlod.length).toBeGreaterThan(0);
    expect(chain.geom.length).toBeGreaterThan(0);
    expect(chain.cobj.length).toBeGreaterThan(0);

    const types = new Set(chain.all.map((e) => e.key.type));
    for (const t of Object.values(RESOURCE_TYPE)) expect(types.has(t)).toBe(true);
    expect(chain.crossPackage).toBe(false);
  });

  it("resolve_chain_cross_package_ref", () => {
    // spec(§10): a chain ref that LEAVES the candidate's package resolves against the FullBuild set.
    const { packages, candidateObjdKey, geomKey } = buildFixtureDonor({ geomInSecondPackage: true });
    const chain = resolveChain(packages, candidateObjdKey);
    expect(chain.geom.map((e) => e.key.instance)).toContain(geomKey.instance);
    expect(chain.crossPackage).toBe(true);
  });

  it("resolve_chain_duplicate_geom_prefers_local_not_cross_package", () => {
    // a GEOM co-located in the OBJD's package AND duplicated (same key) in a second package must
    // resolve from the LOCAL copy — crossPackage reflects PROVENANCE, not mere presence elsewhere.
    const { packages, candidateObjdKey } = buildFixtureDonor({ geomDuplicatedInSecondPackage: true });
    const chain = resolveChain(packages, candidateObjdKey);
    expect(chain.crossPackage).toBe(false);
    expect(chain.geom).toHaveLength(1); // deduped to the local copy, not both
  });

  it("resolve_chain_missing_candidate_throws", () => {
    // a candidate key absent from the set → throw (flag; never silently clone the wrong object).
    const { packages } = buildFixtureDonor();
    expect(() =>
      resolveChain(packages, { type: RESOURCE_TYPE.OBJD, group: 0, instance: 0x9999n }),
    ).toThrow(ChainResolutionError);
  });

  it("resolve_chain_unresolvable_geom_throws", () => {
    // GEOM absent from the whole set → throw (a Build/Buy clone MUST carry geometry; rule-4 spirit).
    const { packages, candidateObjdKey } = buildFixtureDonor({ omitGeom: true });
    expect(() => resolveChain(packages, candidateObjdKey)).toThrow(ChainResolutionError);
  });
});
