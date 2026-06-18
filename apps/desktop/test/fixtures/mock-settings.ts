/**
 * Mock-sidecar settings fixture (Track A): an in-memory /settings store. GET returns the current
 * view; PUT is FULL-REPLACE (§4) — the body IS the new resource, so an omitted field resets to its
 * default (simsModsPath→null, telemetryEnabled→false). Modeling full-replace (not PATCH-merge)
 * means a partial-PUT regression FAILS loudly here instead of being silently masked. No real sidecar.
 */
import type {
  SettingsResponse,
  UpdateSettingsRequest,
} from "../../../../packages/contracts/generated/contracts";

import { jsonResponse, type FetchCall } from "./mock-sse";

export interface SettingsSidecar {
  fetchImpl: typeof fetch;
  calls: FetchCall[];
  /** The current persisted settings (for direct assertions). */
  current: () => SettingsResponse;
}

export function makeSettingsSidecar(initial: SettingsResponse): SettingsSidecar {
  let settings: SettingsResponse = { ...initial };
  const calls: FetchCall[] = [];

  const fetchImpl = (async (input: Parameters<typeof fetch>[0], init?: RequestInit) => {
    const url = typeof input === "string" ? input : input.toString();
    calls.push({ url, init });
    const method = (init?.method ?? "GET").toUpperCase();

    if (url.endsWith("/settings") && method === "GET") {
      return jsonResponse(settings);
    }
    if (url.endsWith("/settings") && method === "PUT") {
      const body = (init?.body ? JSON.parse(String(init.body)) : {}) as UpdateSettingsRequest;
      // FULL-REPLACE: the body IS the new resource; an omitted field resets to its default.
      settings = {
        simsModsPath: body.simsModsPath ?? null,
        telemetryEnabled: body.telemetryEnabled ?? false,
      };
      return jsonResponse(settings);
    }
    return jsonResponse({ error: "unexpected" }, 404);
  }) as typeof fetch;

  return { fetchImpl, calls, current: () => settings };
}
