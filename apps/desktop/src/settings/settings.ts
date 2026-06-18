/**
 * Settings persistence (§4/§18) over the 7.1 token-bearing client and the frozen GET/PUT /settings
 * contract. Server-driven (thin observer, fp-2): the renderer reads settings on demand, never
 * caching them as authority.
 *
 * `PUT /settings` is **FULL-REPLACE** (§4, user-pinned): the body IS the new resource, so an
 * omitted field is RESET to its default. A write of a single field must therefore READ-MODIFY-WRITE
 * the full object — a partial PUT would silently drop the sibling field (data loss). Secrets NEVER
 * ride the body (safety rule 5; UpdateSettingsRequest carries only simsModsPath/telemetryEnabled).
 */
import type {
  SettingsResponse,
  UpdateSettingsRequest,
} from "../../../../packages/contracts/generated/contracts";

import type { IpcClient } from "../ipc/client";

/** The settings fields a write may change (the rule-5-safe subset — no secret field exists). */
type SettingsPatch = Partial<{ simsModsPath: string | null; telemetryEnabled: boolean }>;

/**
 * Read-modify-write the full settings resource: GET current, overlay the changed field(s), PUT the
 * FULL `{ simsModsPath, telemetryEnabled }` object. Each field is resolved explicitly (patch value
 * if provided, else current) so both are always present and correctly typed — under full-replace a
 * dropped field would reset server-side. There is a benign GET→PUT TOCTOU window (single-user
 * onboarding, low-contention); optimistic concurrency is a future concern, not this path.
 */
async function writeSettings(client: IpcClient, patch: SettingsPatch): Promise<SettingsResponse> {
  const current = await client.getSettings();
  const full: UpdateSettingsRequest = {
    simsModsPath:
      patch.simsModsPath !== undefined ? patch.simsModsPath : (current.simsModsPath ?? null),
    telemetryEnabled:
      patch.telemetryEnabled !== undefined ? patch.telemetryEnabled : current.telemetryEnabled,
  };
  return client.updateSettings(full);
}

export function loadSettings(client: IpcClient): Promise<SettingsResponse> {
  return client.getSettings();
}

export function persistModsPath(client: IpcClient, modsPath: string): Promise<SettingsResponse> {
  return writeSettings(client, { simsModsPath: modsPath });
}

/**
 * §18(5) privacy opt-out: persist the server-owned `telemetryEnabled` flag (the sidecar reads it to
 * flip its thin-tracing seam) via read-modify-write (preserves `simsModsPath`). The opt-out polarity
 * (enabled=false ⇒ opted out) is the disclosure screen's framing — this helper matches the contract
 * field directly.
 */
export function persistTelemetryEnabled(
  client: IpcClient,
  enabled: boolean,
): Promise<SettingsResponse> {
  return writeSettings(client, { telemetryEnabled: enabled });
}
