/**
 * Renderer-side typed client over window.aisims.keychain (§18). Sanitizes the providerId before it
 * crosses the bridge (early UX rejection); the main-process KeychainWriter re-validates
 * authoritatively. Write-only: set / has / delete — it never reads a secret back into the renderer.
 */
import type { KeychainBridge } from "../../electron/keychain-bridge";

const PROVIDER_ID_RE = /^[a-z0-9][a-z0-9._-]*$/i;

export function sanitizeProviderId(raw: string): string {
  const id = raw.trim();
  if (!PROVIDER_ID_RE.test(id)) {
    throw new Error("Invalid provider id.");
  }
  return id;
}

export type ProviderKeysClient = KeychainBridge;

export function createProviderKeysClient(bridge: KeychainBridge): ProviderKeysClient {
  return {
    setProviderKey: (providerId, key) => bridge.setProviderKey(sanitizeProviderId(providerId), key),
    hasProviderKey: (providerId) => bridge.hasProviderKey(sanitizeProviderId(providerId)),
    deleteProviderKey: (providerId) => bridge.deleteProviderKey(sanitizeProviderId(providerId)),
  };
}
