/**
 * The IPC protocol catalog (§4): endpoint method/path/mutating + the wire header names +
 * contractVersion.
 *
 * NOTE (deviation, flagged at Step 2.5 / routed at Step 9): the 0.6 codegen emits only model/enum
 * *types* into packages/contracts/generated — NOT this protocol catalog (it lives as module-level
 * constants/enums in ipc.py). So this is hand-authored. It is NOT a silent duplicate: the keys are
 * the frozen `Endpoint` value strings and `test_endpoint_catalog_matches_frozen_snapshot` pins this
 * catalog to the committed §2.5-seam snapshot (ipc.schema.json) so it cannot drift. Follow-up
 * (contracts track): extend the codegen to emit the catalog so a later UI slice imports it.
 */

export const TOKEN_HEADER = "X-AISims-Token";
export const IDEMPOTENCY_KEY_HEADER = "Idempotency-Key";
export const CONTRACT_VERSION = "1.0";

export interface EndpointDef {
  /** HTTP method used by the client (SETTINGS' canonical id is "GET/PUT /settings"; the mutating
   *  PUT form is what the client issues). */
  method: "GET" | "POST" | "PUT" | "DELETE";
  /** Path template; `{param}` placeholders are substituted by the client. */
  path: string;
  /** Idempotency-Key rides mutating endpoints only (§4 R9). */
  mutating: boolean;
}

/** Keys are the frozen `Endpoint` value strings ("METHOD path") — the drift-guard's join key. */
export const ENDPOINTS = {
  "POST /projects": { method: "POST", path: "/projects", mutating: true },
  "GET /projects": { method: "GET", path: "/projects", mutating: false },
  "GET /readiness": { method: "GET", path: "/readiness", mutating: false },
  "POST /projects/{id}/runs": { method: "POST", path: "/projects/{id}/runs", mutating: true },
  "POST /runs/{id}/gate": { method: "POST", path: "/runs/{id}/gate", mutating: true },
  "POST /items/{id}/regenerate": {
    method: "POST",
    path: "/items/{id}/regenerate",
    mutating: true,
  },
  "POST /items/{id}/include": { method: "POST", path: "/items/{id}/include", mutating: true },
  "POST /items/{id}/functional": {
    method: "POST",
    path: "/items/{id}/functional",
    mutating: true,
  },
  "POST /projects/{id}/validate": {
    method: "POST",
    path: "/projects/{id}/validate",
    mutating: true,
  },
  "POST /projects/{id}/export": { method: "POST", path: "/projects/{id}/export", mutating: true },
  "POST /projects/{id}/test-install": {
    method: "POST",
    path: "/projects/{id}/test-install",
    mutating: true,
  },
  "POST /steps/{id}/rerun": { method: "POST", path: "/steps/{id}/rerun", mutating: true },
  "DELETE /jobs/{id}": { method: "DELETE", path: "/jobs/{id}", mutating: true },
  "GET/PUT /settings": { method: "PUT", path: "/settings", mutating: true },
  "POST /settings/providers/{p}/test": {
    method: "POST",
    path: "/settings/providers/{p}/test",
    mutating: true,
  },
} as const satisfies Record<string, EndpointDef>;

export type EndpointId = keyof typeof ENDPOINTS;

export function isMutating(id: EndpointId): boolean {
  return ENDPOINTS[id].mutating;
}
