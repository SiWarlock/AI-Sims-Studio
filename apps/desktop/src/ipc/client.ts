/**
 * Token-bearing REST client (§4/§16). Every request carries the per-launch loopback token in the
 * X-AISims-Token header; mutating commands carry an Idempotency-Key (§4 R9). The token is header-
 * only — never in a URL/query string, never logged (forbidden pattern 3). An untokened client
 * cannot be constructed.
 */
import type {
  ListProjectsResponse,
  RunResponse,
  StartRunRequest,
} from "../../../../packages/contracts/generated/contracts";

import {
  ENDPOINTS,
  IDEMPOTENCY_KEY_HEADER,
  TOKEN_HEADER,
  isMutating,
  type EndpointId,
} from "./endpoints";

export interface BuildHeadersArgs {
  endpointId: EndpointId;
  token: string;
  idempotencyKeyFactory?: () => string;
}

function defaultIdempotencyKey(): string {
  return globalThis.crypto.randomUUID();
}

/** Pure header builder: token always; Idempotency-Key iff the endpoint mutates (§4 R9). */
export function buildRequestHeaders(args: BuildHeadersArgs): Record<string, string> {
  const headers: Record<string, string> = { [TOKEN_HEADER]: args.token };
  if (isMutating(args.endpointId)) {
    const factory = args.idempotencyKeyFactory ?? defaultIdempotencyKey;
    headers[IDEMPOTENCY_KEY_HEADER] = factory();
  }
  return headers;
}

export interface IpcClientOptions {
  baseUrl: string;
  token: string;
  fetchImpl?: typeof fetch;
  idempotencyKeyFactory?: () => string;
}

export interface RequestArgs {
  pathParams?: Record<string, string>;
  query?: Record<string, string | number>;
  body?: unknown;
}

export interface IpcClient {
  request<T>(endpointId: EndpointId, args?: RequestArgs): Promise<T>;
  startRun(projectId: string, body?: StartRunRequest): Promise<RunResponse>;
  listProjects(query?: { limit?: number; offset?: number }): Promise<ListProjectsResponse>;
}

export function createIpcClient(options: IpcClientOptions): IpcClient {
  if (!options.token) {
    throw new Error("IPC client requires a per-launch loopback token (§4/§16, forbidden-pattern 3)");
  }
  const fetchImpl = options.fetchImpl ?? globalThis.fetch;

  async function request<T>(endpointId: EndpointId, args: RequestArgs = {}): Promise<T> {
    const def = ENDPOINTS[endpointId];
    let path: string = def.path;
    for (const [key, value] of Object.entries(args.pathParams ?? {})) {
      path = path.replace(`{${key}}`, encodeURIComponent(value));
    }
    const url = new URL(options.baseUrl + path);
    for (const [key, value] of Object.entries(args.query ?? {})) {
      url.searchParams.set(key, String(value));
    }
    const headers = buildRequestHeaders({
      endpointId,
      token: options.token,
      ...(options.idempotencyKeyFactory
        ? { idempotencyKeyFactory: options.idempotencyKeyFactory }
        : {}),
    });
    const init: RequestInit = { method: def.method, headers };
    if (args.body !== undefined) {
      headers["content-type"] = "application/json";
      init.body = JSON.stringify(args.body);
    }
    const resp = await fetchImpl(url.toString(), init);
    if (!resp.ok) {
      throw new Error(`IPC ${endpointId} failed: HTTP ${resp.status}`);
    }
    return (await resp.json()) as T;
  }

  return {
    request,
    startRun: (projectId, body) =>
      request<RunResponse>("POST /projects/{id}/runs", {
        pathParams: { id: projectId },
        body: body ?? ({ action: "start" } satisfies StartRunRequest),
      }),
    listProjects: (query) =>
      request<ListProjectsResponse>("GET /projects", query ? { query } : {}),
  };
}
