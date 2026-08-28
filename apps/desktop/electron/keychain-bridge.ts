/**
 * The write-only keychain IPC bridge (§3, Lesson 6). A single allowlisted, top-frame-gated channel
 * exposes EXACTLY setProviderKey/hasProviderKey/deleteProviderKey — deliberately NO getProviderKey
 * (the secret is never read back to the renderer; the sidecar reads it). Neither the dispatch nor
 * the handler ever logs its args, and no response echoes the key (rule 5 — the key transits the
 * trusted IPC but is never logged or returned).
 */
import type { IpcMain } from "electron";

import { isTopFrameSender } from "./fs-bridge";
import { InvalidProviderIdError, KeychainUnavailableError, type KeychainWriter } from "./keychain";

export const KEYCHAIN_CHANNEL = "aisims:keychain";

export interface KeychainResult {
  ok: boolean;
  value?: boolean;
  /** A coarse, REDACTED code only — never the key or a raw error message. */
  error?: string;
}

/**
 * Pure channel dispatch: allowlisted write-only methods only; default → reject (no getProviderKey,
 * no arbitrary method). Returns a redacted result (never the key).
 */
export function dispatchKeychain(
  writer: KeychainWriter,
  method: string,
  providerId: string,
  key?: string,
): KeychainResult {
  try {
    switch (method) {
      case "setProviderKey":
        if (key === undefined || key.length === 0) {
          // Never silently store an empty secret (which would clobber a real key).
          return { ok: false, error: "missing-key" };
        }
        writer.setProviderKey(providerId, key);
        return { ok: true };
      case "hasProviderKey":
        return { ok: true, value: writer.hasProviderKey(providerId) };
      case "deleteProviderKey":
        writer.deleteProviderKey(providerId);
        return { ok: true };
      default:
        return { ok: false, error: "unknown-method" };
    }
  } catch (e) {
    // Coarse, REDACTED codes only — never the key or a raw message.
    if (e instanceof KeychainUnavailableError) return { ok: false, error: "unavailable" };
    if (e instanceof InvalidProviderIdError) return { ok: false, error: "invalid-id" };
    return { ok: false, error: "failed" };
  }
}

export function registerKeychainBridge(ipcMain: IpcMain, writer: KeychainWriter): void {
  ipcMain.on(KEYCHAIN_CHANNEL, (event, method: unknown, providerId: unknown, key: unknown) => {
    if (!isTopFrameSender(event.senderFrame)) {
      event.returnValue = { ok: false, error: "sender" } satisfies KeychainResult;
      return;
    }
    event.returnValue = dispatchKeychain(
      writer,
      String(method),
      String(providerId ?? ""),
      typeof key === "string" ? key : undefined,
    );
  });
}

/** The renderer-facing write-only surface (no getProviderKey). */
export interface KeychainBridge {
  setProviderKey(providerId: string, key: string): void;
  hasProviderKey(providerId: string): boolean;
  deleteProviderKey(providerId: string): void;
}

export function createKeychainBridge(
  sendSync: (channel: string, ...args: unknown[]) => unknown,
): KeychainBridge {
  const call = (method: string, providerId: string, key?: string): KeychainResult => {
    const res = sendSync(KEYCHAIN_CHANNEL, method, providerId, key) as KeychainResult | undefined;
    if (!res?.ok) {
      // Redacted: a coarse code only, never the key.
      throw new Error(`keychain ${method} ${res?.error ?? "failed"}`);
    }
    return res;
  };
  return {
    setProviderKey: (providerId, key) => {
      call("setProviderKey", providerId, key);
    },
    hasProviderKey: (providerId) => call("hasProviderKey", providerId).value === true,
    deleteProviderKey: (providerId) => {
      call("deleteProviderKey", providerId);
    },
  };
}
