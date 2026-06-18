/**
 * Settings persistence (§4/§18) over the 7.1 token-bearing client and the frozen GET/PUT /settings
 * contract. Server-driven (thin observer, fp-2): the renderer reads settings on demand, never
 * caching them as authority. Secrets NEVER ride the /settings body — `persistModsPath` only ever
 * sets `simsModsPath` (safety rule 5; UpdateSettingsRequest has no secret field).
 */
import type { SettingsResponse } from "../../../../packages/contracts/generated/contracts";

import type { IpcClient } from "../ipc/client";

export function loadSettings(client: IpcClient): Promise<SettingsResponse> {
  return client.getSettings();
}

export function persistModsPath(client: IpcClient, modsPath: string): Promise<SettingsResponse> {
  return client.updateSettings({ simsModsPath: modsPath });
}

/**
 * §18(5) privacy opt-out: persist the server-owned `telemetryEnabled` flag (the sidecar reads it to
 * flip its thin-tracing seam). Partial PUT of ONLY this field (mirrors `persistModsPath`); no secret
 * on the body (rule 5). The opt-out polarity (enabled=false ⇒ opted out) is the disclosure screen's
 * framing — this helper matches the contract field directly.
 */
export function persistTelemetryEnabled(
  client: IpcClient,
  enabled: boolean,
): Promise<SettingsResponse> {
  return client.updateSettings({ telemetryEnabled: enabled });
}
