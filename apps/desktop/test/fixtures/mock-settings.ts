/**
 * Mock-sidecar settings fixture (Track A): an in-memory /settings store. GET returns the current
 * view; PUT merges simsModsPath/telemetryEnabled and returns the updated view (so a write→read
 * round-trips). No real sidecar.
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
      const next: SettingsResponse = { ...settings };
      if (typeof body.simsModsPath === "string") next.simsModsPath = body.simsModsPath;
      if (typeof body.telemetryEnabled === "boolean") next.telemetryEnabled = body.telemetryEnabled;
      settings = next;
      return jsonResponse(settings);
    }
    return jsonResponse({ error: "unexpected" }, 404);
  }) as typeof fetch;

  return { fetchImpl, calls, current: () => settings };
}
