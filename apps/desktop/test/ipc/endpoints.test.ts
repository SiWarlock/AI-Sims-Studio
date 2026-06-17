import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import {
  CONTRACT_VERSION,
  ENDPOINTS,
  IDEMPOTENCY_KEY_HEADER,
  TOKEN_HEADER,
} from "../../src/ipc/endpoints";

/**
 * PROPOSED ADD (Step-2.5 Q-extra): the protocol catalog (endpoint paths, mutating set, header
 * names, contractVersion) is NOT emitted by the 0.6 codegen — it lives only in ipc.py + the
 * committed §2.5-seam snapshot. This guard ties the hand-authored UI catalog to that frozen
 * snapshot so it can't drift silently (the analogue of RED #9's parity guard for the SSE union).
 */
const SNAPSHOT = fileURLToPath(
  new URL(
    "../../../../packages/contracts/tests/__snapshots__/ipc.schema.json",
    import.meta.url,
  ),
);

interface IpcSnapshot {
  contractVersion: string;
  headers: { token: string; idempotencyKey: string };
  mutatingEndpoints: string[];
  readOnlyEndpoints: string[];
}

describe("endpoint catalog — drift guard against the frozen ipc snapshot (§4)", () => {
  const snap = JSON.parse(readFileSync(SNAPSHOT, "utf8")) as IpcSnapshot;

  it("test_endpoint_catalog_matches_frozen_snapshot — spec(§4)", () => {
    expect(CONTRACT_VERSION).toBe(snap.contractVersion);
    expect(TOKEN_HEADER).toBe(snap.headers.token);
    expect(IDEMPOTENCY_KEY_HEADER).toBe(snap.headers.idempotencyKey);

    const mutating = Object.entries(ENDPOINTS)
      .filter(([, def]) => def.mutating)
      .map(([id]) => id)
      .sort();
    const readOnly = Object.entries(ENDPOINTS)
      .filter(([, def]) => !def.mutating)
      .map(([id]) => id)
      .sort();

    expect(mutating).toEqual([...snap.mutatingEndpoints].sort());
    expect(readOnly).toEqual([...snap.readOnlyEndpoints].sort());
  });
});
