/**
 * Token-bearing REST client (§4/§16). Every request carries the per-launch loopback token in the
 * X-AISims-Token header; mutating commands carry an Idempotency-Key (§4 R9). The token is header-
 * only — never in a URL/query string, never logged (forbidden pattern 3). An untokened client
 * cannot be constructed.
 */
import type {
  ListProjectsResponse,
  ReadinessReport,
  RunResponse,
  SettingsResponse,
  StartRunRequest,
  UpdateSettingsRequest,
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
  /** The effective HTTP method (defaults to the catalog method). */
  method?: "GET" | "POST" | "PUT" | "DELETE";
  idempotencyKeyFactory?: () => string;
}

function defaultIdempotencyKey(): string {
  return globalThis.crypto.randomUUID();
}

/**
 * Pure header builder: token always; Idempotency-Key iff the endpoint mutates AND the effective
 * method is a write (§4 R9). Deriving from the effective method (not stripping after the fact) keeps
 * the conflated SETTINGS endpoint's GET read key-free without a divergent post-hoc delete.
 */
export function buildRequestHeaders(args: BuildHeadersArgs): Record<string, string> {
  const headers: Record<string, string> = { [TOKEN_HEADER]: args.token };
  const method = args.method ?? ENDPOINTS[args.endpointId].method;
  if (isMutating(args.endpointId) && method !== "GET") {
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
  /** Override the catalog method — needed for the conflated "GET/PUT /settings" endpoint. */
  method?: "GET" | "POST" | "PUT" | "DELETE";
}

export interface IpcClient {
  request<T>(endpointId: EndpointId, args?: RequestArgs): Promise<T>;
  startRun(projectId: string, body?: StartRunRequest): Promise<RunResponse>;
  listProjects(query?: { limit?: number; offset?: number }): Promise<ListProjectsResponse>;
  /** GET /settings — a read on the conflated SETTINGS endpoint (omits Idempotency-Key). */
  getSettings(): Promise<SettingsResponse>;
  /** PUT /settings — a write (carries Idempotency-Key); secrets never ride the body (rule 5). */
  updateSettings(body: UpdateSettingsRequest): Promise<SettingsResponse>;
  /** GET /readiness — read-only system-readiness probe (token header, NO Idempotency-Key). */
  getReadiness(): Promise<ReadinessReport>;
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
    // The method override exists ONLY to express the read form of the conflated "GET/PUT /settings"
    // endpoint — never to send a wrong method (e.g. a GET) to a genuinely mutating path. Gate it so
    // it can't widen the frozen §4 surface (review Finding).
    if (args.method !== undefined && endpointId !== "GET/PUT /settings") {
      throw new Error(
        `IPC method override is only supported for "GET/PUT /settings" (got ${endpointId})`,
      );
    }
    const method = args.method ?? def.method;
    const headers = buildRequestHeaders({
      endpointId,
      token: options.token,
      method,
      ...(options.idempotencyKeyFactory
        ? { idempotencyKeyFactory: options.idempotencyKeyFactory }
        : {}),
    });
    const init: RequestInit = { method, headers };
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
    getSettings: () => request<SettingsResponse>("GET/PUT /settings", { method: "GET" }),
    updateSettings: (body) =>
      request<SettingsResponse>("GET/PUT /settings", { method: "PUT", body }),
    getReadiness: () => request<ReadinessReport>("GET /readiness"),
  };
}
