// Synthetic donor-package fixture for the S1b-clone deterministic tests.
//
// Builds a single-object Build/Buy donor graph with KNOWN, unambiguous TGI keys (OBJD + COBJ + MODL +
// MLOD + GEOM + FTPT + RIG + IMG + SLOT) so the clone mechanics + chain resolution are deterministic.
// The OBJD carries real `ResourceKey[]` refs (models/footprints/rigs/icons/slots) so OBJD→MODL/FTPT/
// RIG/IMG/SLOT resolve by direct ref; COBJ/MLOD/GEOM are type-collected. The real ~1 GB FullBuild
// donor is the exploratory arm (run-and-observe), NOT this fixture.

import { ObjectDefinitionResource, RawResource } from "@s4tk/models";
import type { ResourceKey, ResourceKeyPair } from "@s4tk/models/types";

import { RESOURCE_TYPE, type DonorPackageSource } from "../../src/donor/resolveChain";

function key(type: number, instance: bigint): ResourceKey {
  return { type, group: 0, instance };
}

function raw(type: number, instance: bigint, body: string): ResourceKeyPair {
  return { key: key(type, instance), value: RawResource.from(Buffer.from(body)) };
}

export const OBJD_KEY = key(RESOURCE_TYPE.OBJD, 0x031an);
export const COBJ_KEY = key(RESOURCE_TYPE.COBJ, 0x0c0bn);
export const MODL_KEY = key(RESOURCE_TYPE.MODL, 0x0117n);
export const MLOD_KEY = key(RESOURCE_TYPE.MLOD, 0x01d1n);
export const GEOM_KEY = key(RESOURCE_TYPE.GEOM, 0x015an);
export const FTPT_KEY = key(RESOURCE_TYPE.FTPT, 0x0f70n);
export const RIG_KEY = key(RESOURCE_TYPE.RIG, 0x0816n);
export const IMG_KEY = key(RESOURCE_TYPE.IMG, 0x01a6n);
export const SLOT_KEY = key(RESOURCE_TYPE.SLOT, 0x05a7n);

/** The donor's ORIGINAL GEOM bytes (distinct from S1a's swapped-in bytes) — proves the swap happened. */
export const DONOR_GEOM_BYTES = Buffer.from("DONOR-ORIGINAL-GEOM-PLACEHOLDER");

export interface FixtureDonor {
  packages: DonorPackageSource[];
  candidateObjdKey: ResourceKey;
  geomKey: ResourceKey;
}

function buildObjd(noTuning = false): ResourceKeyPair {
  const objd = new ObjectDefinitionResource({
    version: ObjectDefinitionResource.LATEST_VERSION,
    properties: {
      name: "aisims_fixture_donor",
      models: [MODL_KEY],
      footprints: [FTPT_KEY],
      rigs: [RIG_KEY],
      icons: [IMG_KEY],
      slots: [SLOT_KEY],
      // a resolved tuning instance — omitted for the noTuning variant (tuningId stays absent).
      ...(noTuning ? {} : { tuningId: 0xdeadbeefn }),
    },
  });
  return { key: OBJD_KEY, value: objd };
}

/**
 * Build the fixture donor. By default the whole chain is co-located in one package.
 * - `geomInSecondPackage`: the GEOM lives in a SECOND package (cross-package resolution).
 * - `geomDuplicatedInSecondPackage`: the GEOM is co-located in the OBJD's package AND duplicated
 *   (same key) in a second package — resolution must PREFER the local copy (crossPackage stays false).
 * - `omitGeom`: drops the GEOM entirely (an unresolvable chain).
 * - `noTuning`: the OBJD carries no tuning instance (validateRoundTrip's tuningResolves=false path).
 */
export function buildFixtureDonor(opts?: {
  geomInSecondPackage?: boolean;
  geomDuplicatedInSecondPackage?: boolean;
  omitGeom?: boolean;
  noTuning?: boolean;
}): FixtureDonor {
  const geomInSecond = opts?.geomInSecondPackage ?? false;
  const geomDuplicated = opts?.geomDuplicatedInSecondPackage ?? false;
  const omitGeom = opts?.omitGeom ?? false;

  const geomEntry = (): ResourceKeyPair => ({
    key: GEOM_KEY,
    value: RawResource.from(DONOR_GEOM_BYTES),
  });

  const primary: ResourceKeyPair[] = [
    buildObjd(opts?.noTuning ?? false),
    raw(RESOURCE_TYPE.COBJ, COBJ_KEY.instance, "catalog"),
    raw(RESOURCE_TYPE.MODL, MODL_KEY.instance, "model"),
    raw(RESOURCE_TYPE.MLOD, MLOD_KEY.instance, "model-lod"),
    raw(RESOURCE_TYPE.FTPT, FTPT_KEY.instance, "footprint"),
    raw(RESOURCE_TYPE.RIG, RIG_KEY.instance, "rig"),
    raw(RESOURCE_TYPE.IMG, IMG_KEY.instance, "thumbnail"),
    raw(RESOURCE_TYPE.SLOT, SLOT_KEY.instance, "slot"),
  ];

  const packages: DonorPackageSource[] = [];
  if (omitGeom) {
    packages.push({ path: "/fixtures/donor-primary.package", entries: primary });
  } else if (geomInSecond) {
    packages.push({ path: "/fixtures/donor-primary.package", entries: primary });
    packages.push({ path: "/fixtures/donor-geom.package", entries: [geomEntry()] });
  } else if (geomDuplicated) {
    packages.push({ path: "/fixtures/donor-primary.package", entries: [...primary, geomEntry()] });
    packages.push({ path: "/fixtures/donor-geom.package", entries: [geomEntry()] });
  } else {
    packages.push({ path: "/fixtures/donor-primary.package", entries: [...primary, geomEntry()] });
  }

  return { packages, candidateObjdKey: OBJD_KEY, geomKey: GEOM_KEY };
}
